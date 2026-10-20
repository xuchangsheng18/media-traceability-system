"""Independent people and current duties. User ids, JWT subjects and names are not people."""

import math
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import Connection

from ..controls.providers import ApprovalRule
from ..errors import BusinessError
from ..identity.directory import valid_key
from ..types import Actor, Scope
from .object_facts import digest
from .policy import validate_principal
from .rule_types import RuleTarget
from .types import Principal


@dataclass(frozen=True)
class VerifiedPerson:
    actor: Actor
    person_id: UUID
    mapping_version: str
    valid_until: int


class HumanIdentityReader(Protocol):
    def resolve(self, actor: Actor) -> VerifiedPerson: ...


@dataclass(frozen=True)
class DutyFacts:
    applicant: UUID
    submitters: frozenset[UUID]
    executors: frozenset[UUID]
    evaluators: frozenset[UUID]
    approved_people: frozenset[UUID]
    version_digest: str


@dataclass(frozen=True)
class DutyActors:
    target: RuleTarget
    submitters: frozenset[Actor]
    executors: frozenset[Actor]
    evaluators: frozenset[Actor]
    version_digest: str
    valid_until: float


@dataclass(frozen=True)
class BoundDutyFacts(DutyFacts):
    target: RuleTarget
    bindings: Mapping[UUID, VerifiedPerson]
    context_digest: str
    valid_until: float


class DutyAssignmentReader(Protocol):
    def read(self, target: RuleTarget, *, connection: Connection | None) -> DutyActors: ...


def approval_target(scope: Scope, item: Mapping[str, Any]) -> RuleTarget:
    return RuleTarget(
        scope.actor.org_id,
        str(item["object_type"]),
        UUID(str(item["object_id"])),
        int(item["object_version"]),
        scope.case_id,
        str(item["purpose"]),
        None,
        request_digest=digest({k: item[k] for k in ("run_version", "result_version", "policy_version")}),
    )


class IndependentDuties:
    def __init__(
        self,
        people: HumanIdentityReader | None,
        assignments: DutyAssignmentReader | None,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.people, self.assignments, self.clock = people, assignments, clock

    def current_time(self) -> float:
        try:
            value = self.clock()
        except Exception:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
        if type(value) not in (float, int) or not math.isfinite(value):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return float(value)

    def person(self, actor: Actor) -> VerifiedPerson:
        if self.people is None:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        try:
            value = self.people.resolve(actor)
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
        if (
            not isinstance(value, VerifiedPerson)
            or value.actor != actor
            or not isinstance(value.person_id, UUID)
            or not valid_key(value.mapping_version, 1024)
            or type(value.valid_until) is not int
            or value.valid_until <= self.current_time()
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return value

    def collect(
        self,
        scope: Scope,
        item: Mapping[str, Any],
        decisions: Sequence[Mapping[str, Any]],
        *,
        connection: Connection | None,
        extra_actors: frozenset[Actor] = frozenset(),
    ) -> BoundDutyFacts:
        if self.assignments is None:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        target = approval_target(scope, item)
        try:
            duty = self.assignments.read(target, connection=connection)
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
        current = self.current_time()
        if (
            not isinstance(duty, DutyActors)
            or duty.target != target
            or not isinstance(duty.version_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", duty.version_digest) is None
            or type(duty.valid_until) not in (int, float)
            or not math.isfinite(duty.valid_until)
            or duty.valid_until <= current
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        sets = (duty.submitters, duty.executors, duty.evaluators, extra_actors)
        if any(
            type(values) is not frozenset
            or any(
                not isinstance(a, Actor) or a.org_id != target.org_id or not isinstance(a.user_id, UUID) for a in values
            )
            for values in sets
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        applicant = Actor(UUID(str(item["requested_by"])), target.org_id)
        voters = frozenset(
            Actor(UUID(str(d["decision_actor_id"])), target.org_id) for d in decisions if d["decision"] == "approve"
        )
        context_actors = frozenset({applicant}) | duty.submitters | duty.executors | duty.evaluators
        actors = context_actors | voters | extra_actors
        values = {a.user_id: self.person(a) for a in sorted(actors, key=lambda a: str(a.user_id))}
        context = digest(
            dict(
                target=asdict(target),
                assignment_version=duty.version_digest,
                submitters=sorted(str(values[a.user_id].person_id) for a in duty.submitters),
                executors=sorted(str(values[a.user_id].person_id) for a in duty.executors),
                evaluators=sorted(str(values[a.user_id].person_id) for a in duty.evaluators),
                people=[asdict(values[a.user_id]) for a in sorted(context_actors, key=lambda a: str(a.user_id))],
            )
        )
        approved = frozenset(values[a.user_id].person_id for a in voters)
        for a in actors:
            if self.person(a) != values[a.user_id]:
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        try:
            reread = self.assignments.read(target, connection=connection)
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
        if reread != duty:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return BoundDutyFacts(
            values[applicant.user_id].person_id,
            frozenset(values[a.user_id].person_id for a in duty.submitters),
            frozenset(values[a.user_id].person_id for a in duty.executors),
            frozenset(values[a.user_id].person_id for a in duty.evaluators),
            approved,
            digest(
                dict(
                    context=context,
                    bindings=[asdict(v) for v in values.values()],
                    approved=sorted(str(p) for p in approved),
                )
            ),
            target,
            MappingProxyType(values),
            context,
            min(float(duty.valid_until), current + 5, *[float(v.valid_until) for v in values.values()]),
        )

    def _bound(self, facts: DutyFacts) -> BoundDutyFacts:
        if (
            not isinstance(facts, BoundDutyFacts)
            or not isinstance(facts.target, RuleTarget)
            or not isinstance(facts.applicant, UUID)
            or not isinstance(facts.bindings, Mapping)
            or any(
                type(v) is not frozenset or any(not isinstance(p, UUID) for p in v)
                for v in (facts.submitters, facts.executors, facts.evaluators, facts.approved_people)
            )
            or any(
                not isinstance(v, str) or re.fullmatch(r"[0-9a-f]{64}", v) is None
                for v in (facts.version_digest, facts.context_digest)
            )
            or type(facts.valid_until) not in (float, int)
            or not math.isfinite(facts.valid_until)
            or facts.valid_until <= self.current_time()
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        if any(
            not isinstance(k, UUID)
            or not isinstance(v, VerifiedPerson)
            or not isinstance(v.actor, Actor)
            or v.actor.user_id != k
            or v.actor.org_id != facts.target.org_id
            or not isinstance(v.person_id, UUID)
            or not valid_key(v.mapping_version, 1024)
            or type(v.valid_until) is not int
            or v.valid_until <= self.current_time()
            for k, v in facts.bindings.items()
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        bound_people = frozenset(v.person_id for v in facts.bindings.values())
        if (
            not ({facts.applicant} | facts.submitters | facts.executors | facts.evaluators | facts.approved_people)
            <= bound_people
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return facts

    def review(
        self,
        scope: Scope,
        task: Mapping[str, Any],
        context: Mapping[str, Any],
        *,
        connection: Connection,
    ) -> None:
        if not isinstance(task.get("created_by"), UUID):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        item = dict(
            object_type="task",
            object_id=task["task_id"],
            object_version=task["row_version"],
            purpose="review",
            policy_version=context["policy_version"],
            run_version=context["run_version"],
            result_version=context["result_version"],
            requested_by=task["created_by"],
        )
        facts = self.collect(scope, item, [], connection=connection, extra_actors=frozenset({scope.actor}))
        self.candidate(scope.actor, facts)

    def candidate(self, actor: Actor, facts: DutyFacts) -> UUID:
        value = self._bound(facts)
        person = value.bindings.get(actor.user_id)
        if person is None or person.actor != actor or self.person(actor) != person:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        blocked = {value.applicant} | value.submitters | value.executors | value.evaluators | value.approved_people
        if person.person_id in blocked:
            raise BusinessError("INDEPENDENT_APPROVER_REQUIRED", 403)
        return person.person_id

    def decision_proof(self, actor: Actor, facts: DutyFacts) -> dict[str, Any]:
        value = self._bound(facts)
        person = value.bindings.get(actor.user_id)
        if person is None or person.actor != actor:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return dict(
            version=1,
            context_digest=value.context_digest,
            person_id=str(person.person_id),
            mapping_version=person.mapping_version,
            person_valid_until=person.valid_until,
        )

    def validate_records(self, facts: DutyFacts, records: Sequence[Mapping[str, Any]]) -> None:
        value = self._bound(facts)
        for record in records:
            if record["decision"] != "approve":
                continue
            actor = Actor(UUID(str(record["decision_actor_id"])), value.target.org_id)
            if record["evidence_refs"].get("independence") != self.decision_proof(actor, value):
                raise BusinessError("INDEPENDENT_APPROVER_REQUIRED", 403)

    @staticmethod
    def _rule(rule: ApprovalRule) -> None:
        if (
            not isinstance(rule, ApprovalRule)
            or not valid_key(rule.version, 1024)
            or type(rule.ttl_seconds) is not int
            or not 1 <= rule.ttl_seconds <= 1800
            or type(rule.independent_approvers) is not int
            or rule.independent_approvers < 1
        ):
            raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)

    def validate_approval(self, facts: DutyFacts, rule: ApprovalRule) -> None:
        value = self._bound(facts)
        self._rule(rule)
        minimum = dict(review=1, confirmation=1, seal=2, report_export=2, training_feedback=2, model_release=2).get(
            value.target.purpose or ""
        )
        if minimum is None or rule.independent_approvers < minimum:
            raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)
        if (
            value.approved_people & ({value.applicant} | value.submitters | value.executors | value.evaluators)
            or len(value.approved_people) < rule.independent_approvers
        ):
            raise BusinessError("INDEPENDENT_APPROVER_REQUIRED", 403)

    def approval_live(self, created: datetime, expires: datetime | None, rule: ApprovalRule) -> bool:
        self._rule(rule)
        if (
            not isinstance(created, datetime)
            or created.tzinfo is None
            or not isinstance(expires, datetime)
            or expires.tzinfo is None
        ):
            return False
        current = self.current_time()
        return created.timestamp() <= current < expires.timestamp() <= created.timestamp() + rule.ttl_seconds

    def check(self, principal: Principal, target: RuleTarget, facts: DutyFacts, rule: ApprovalRule) -> None:
        validate_principal(principal, self.clock)
        value = self._bound(facts)
        self.person(principal.actor)
        if value.target != target or principal.actor.org_id != target.org_id:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        self.validate_approval(value, rule)
