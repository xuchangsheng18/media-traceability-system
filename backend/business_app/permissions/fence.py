"""One-transaction database ordering plus an independent, explicitly supplied recovery proof."""

import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from threading import Lock
from typing import Any, Protocol

from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

from ..errors import BusinessError
from ..identity.directory import valid_key
from .conditional import ConditionalPermissionAuthority
from .context import Evidence
from .rule_types import AuthorizationEvidence, RoleFacts, WorkAuthorizationEvidence, WorkRoleFacts
from .work_subject import WORK_OPERATIONS


@dataclass(frozen=True)
class GenerationProof:
    recovery_generation: str
    policy_version: str
    policy_sha256: str
    database_name: str
    database_oid: int
    minimum_epoch: int
    confirmed_at: float
    valid_until: float


class GenerationReader(Protocol):
    def read(self) -> GenerationProof: ...


@dataclass(frozen=True)
class HeldAuthorization:
    transaction: object
    evidence: Evidence
    epoch: int
    generation: GenerationProof


class AuthorizationFence:
    def __init__(
        self,
        authority: ConditionalPermissionAuthority,
        generations: GenerationReader | None,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.authority, self.generations, self.clock = authority, generations, clock
        self.last_time: float | None = None
        self.time_lock = Lock()
        self.key = ("media-trace-authorization-fence", id(self))

    def _time(self) -> float:
        # Sampling is inside the lock: an earlier sample may otherwise resume
        # after a later request and masquerade as an actual clock rollback.
        with self.time_lock:
            value = self.clock()
            if type(value) not in (int, float) or not math.isfinite(value):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            current = float(value)
            if self.last_time is not None and current < self.last_time:
                raise BusinessError("AUTHORIZATION_CHANGED", 503)
            self.last_time = current
            return current

    def _generation(self, stamp: Mapping[str, Any], current: float) -> GenerationProof:
        if self.generations is None:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        proof = self.generations.read()
        snapshot = self.authority.rules.snapshot
        if (
            not isinstance(proof, GenerationProof)
            or any(
                not valid_key(v, 1024) for v in [proof.recovery_generation, proof.policy_version, proof.database_name]
            )
            or type(proof.database_oid) is not int
            or proof.database_oid <= 0
            or type(proof.minimum_epoch) is not int
            or proof.minimum_epoch <= 0
            or type(proof.confirmed_at) not in (float, int)
            or not math.isfinite(proof.confirmed_at)
            or type(proof.valid_until) not in (float, int)
            or not math.isfinite(proof.valid_until)
            or not proof.confirmed_at <= current < proof.valid_until
            or (proof.database_name, proof.database_oid) != (stamp["database_name"], stamp["database_oid"])
            or proof.minimum_epoch > stamp["epoch"]
            or (proof.policy_version, proof.policy_sha256, proof.recovery_generation)
            != (snapshot.version, snapshot.sha256, snapshot.recovery_generation)
            or (stamp["policy_version"], stamp["policy_sha256"], stamp["recovery_generation"])
            != (proof.policy_version, proof.policy_sha256, proof.recovery_generation)
        ):
            raise BusinessError("AUTHORIZATION_CHANGED", 503)
        self.authority.rules.validate_snapshot()
        return proof

    @staticmethod
    def _stamp(connection: Connection) -> dict[str, Any]:
        if not connection.in_transaction():
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        row = connection.execute(text("SELECT * FROM mt.hold_authorization_epoch()")).mappings().one()
        return dict(row)

    def hold(self, connection: Connection, evidence: Evidence) -> None:
        try:
            if not isinstance(evidence, (AuthorizationEvidence, WorkAuthorizationEvidence)):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            current = self._time()
            if (
                type(evidence.valid_until) not in (float, int)
                or not math.isfinite(evidence.valid_until)
                or current >= evidence.valid_until
            ):
                raise BusinessError("AUTHORIZATION_CHANGED", 503)
            stamp = self._stamp(connection)
            generation = self._generation(stamp, current)
            fresh = (
                self.authority.authorize(
                    evidence.principal, evidence.operation_id, evidence.target, connection=connection
                )
                if isinstance(evidence, AuthorizationEvidence)
                else self.authority.authorize_work(
                    evidence.subject, evidence.operation_id, evidence.target, connection=connection
                )
            )
            if any(
                getattr(fresh, k) != getattr(evidence, k)
                for k in [
                    "principal" if isinstance(evidence, AuthorizationEvidence) else "subject",
                    "operation_id",
                    "target",
                    "role_digest",
                    "condition_digest",
                    "policy_version",
                    "recovery_generation",
                ]
            ):
                raise BusinessError("AUTHORIZATION_CHANGED", 503)
            connection.info[self.key] = HeldAuthorization(
                connection.get_transaction(),
                evidence,
                stamp["epoch"],
                generation,
            )
        except BusinessError:
            raise
        except (SQLAlchemyError, RuntimeError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None

    def finish(self, connection: Connection, evidence: Evidence) -> None:
        try:
            held = connection.info.get(self.key)
            current = self._time()
            if (
                not isinstance(held, HeldAuthorization)
                or held.transaction is not connection.get_transaction()
                or held.evidence != evidence
            ):
                raise BusinessError("AUTHORIZATION_CHANGED", 503)
            # The original five-second fact interval is not a job timeout. The
            # retained transaction/epoch and immutable subject/target stay bound;
            # all current identity, delegation, source, policy and actual expiry
            # checks below are mandatory even when the first interval has ended.
            stamp = self._stamp(connection)
            generation = self._generation(stamp, current)
            # Freshness renewal does not rotate a generation. Its immutable
            # database/policy identity and monotone epoch floor must still match.
            if (
                stamp["epoch"] != held.epoch
                or replace(
                    generation,
                    confirmed_at=held.generation.confirmed_at,
                    valid_until=held.generation.valid_until,
                    minimum_epoch=held.generation.minimum_epoch,
                )
                != held.generation
                or generation.minimum_epoch < held.generation.minimum_epoch
            ):
                raise BusinessError("AUTHORIZATION_CHANGED", 503)
            roles: RoleFacts | WorkRoleFacts
            if isinstance(evidence, AuthorizationEvidence):
                roles = self.authority._roles(
                    evidence.principal, self.authority.catalog[evidence.operation_id].permission, connection
                )
            else:
                roles = self.authority._work_roles(
                    evidence.subject, WORK_OPERATIONS[evidence.operation_id][0], connection
                )
            if roles.version_digest != evidence.role_digest:
                raise BusinessError("AUTHORIZATION_CHANGED", 503)
            # Initial exact-version verification and retained row locks exclude other
            # writers. Our own state/version update is legitimate; current conditions,
            # purpose, source set and immutable request binding still have to hold.
            target = replace(evidence.target, object_version=None)
            fresh = (
                self.authority.authorize(evidence.principal, evidence.operation_id, target, connection=connection)
                if isinstance(evidence, AuthorizationEvidence)
                else self.authority.authorize_work(
                    evidence.subject, evidence.operation_id, target, connection=connection
                )
            )
            if (
                fresh.role_digest != evidence.role_digest
                or fresh.policy_version != evidence.policy_version
                or fresh.recovery_generation != evidence.recovery_generation
            ):
                raise BusinessError("AUTHORIZATION_CHANGED", 503)
        except BusinessError:
            raise
        except (SQLAlchemyError, RuntimeError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
