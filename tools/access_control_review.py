"""Executable candidate design for synthetic case-resource review, never an authority provider."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ReviewRequest:
    subject_id: str
    subject_org_id: str
    roles: tuple[str, ...]
    resource_org_id: str
    case_id: str
    object_id: str
    permission: str
    purpose: str
    labels: tuple[str, ...]
    policy_revision: str
    identity_verified: bool
    account_enabled: bool
    membership_org_id: str
    membership_case_id: str
    membership_expires_at: datetime
    membership_revoked: bool
    role_expires_at: datetime
    role_revoked: bool


@dataclass(frozen=True)
class ReviewGrant:
    subject_id: str
    role: str
    permission: str
    org_id: str
    case_id: str
    object_id: str
    purposes: tuple[str, ...]
    labels: tuple[str, ...]
    policy_revision: str
    valid_from: datetime
    expires_at: datetime
    revoked: bool


@dataclass(frozen=True)
class ReviewDecision:
    effect: str
    reason: str
    runtime_authorization: bool = False


def aware(value: datetime) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def nonblank(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evaluate_review(
    model: dict[str, Any],
    request: ReviewRequest,
    grants: tuple[ReviewGrant, ...],
    *,
    now: datetime,
    mode: str = "synthetic_review",
) -> ReviewDecision:
    """Return a review prediction. All inputs are self-owned fixtures, not trusted HTTP claims."""
    if mode != "synthetic_review" or model.get("production_enabled") is not False:
        return ReviewDecision("DENY", "REVIEW_ONLY")
    if not aware(now):
        return ReviewDecision("DENY", "CLOCK_INVALID")
    if not request.subject_id:
        return ReviewDecision("DENY", "SUBJECT_MISSING")
    if request.identity_verified is not True:
        return ReviewDecision("DENY", "IDENTITY_NOT_VERIFIED")
    if request.account_enabled is not True:
        return ReviewDecision("DENY", "ACCOUNT_DISABLED")
    roles = {role["code"]: role for role in model["roles"]}
    if not request.roles or any(role not in roles for role in request.roles):
        return ReviewDecision("DENY", "ROLE_MISSING_OR_UNKNOWN")
    if request.permission not in model["permissions"]:
        return ReviewDecision("DENY", "PERMISSION_UNKNOWN")
    if request.permission not in model["case_review_permissions"]:
        return ReviewDecision("DENY", "REVIEW_SCOPE_UNSUPPORTED")
    if request.role_revoked is not False or not aware(request.role_expires_at) or now >= request.role_expires_at:
        return ReviewDecision("DENY", "ROLE_BINDING_INACTIVE")
    if not request.subject_org_id or not (
        request.subject_org_id == request.resource_org_id == request.membership_org_id
    ):
        return ReviewDecision("DENY", "ORGANIZATION_MISMATCH")
    if (
        not request.case_id
        or request.case_id != request.membership_case_id
        or request.membership_revoked is not False
        or not aware(request.membership_expires_at)
        or now >= request.membership_expires_at
    ):
        return ReviewDecision("DENY", "CASE_MEMBERSHIP_INACTIVE")
    if not request.object_id:
        return ReviewDecision("DENY", "OBJECT_MISSING")
    if (
        not nonblank(request.purpose)
        or not request.labels
        or not all(nonblank(label) for label in request.labels)
        or not nonblank(request.policy_revision)
    ):
        return ReviewDecision("DENY", "PURPOSE_OR_CLASSIFICATION_UNCONFIRMED")
    if any(roles[role]["permission_review"][request.permission] == "SOURCE_RESTRICTION" for role in request.roles):
        return ReviewDecision("DENY", "SOURCE_ROLE_RESTRICTION")
    for grant in grants:
        if (
            grant.revoked is False
            and aware(grant.valid_from)
            and aware(grant.expires_at)
            and grant.valid_from <= now < grant.expires_at
            and grant.subject_id == request.subject_id
            and grant.role in request.roles
            and grant.permission == request.permission
            and grant.org_id == request.subject_org_id
            and grant.case_id == request.case_id
            and grant.object_id == request.object_id
            and request.purpose in grant.purposes
            and set(request.labels).issubset(grant.labels)
            and grant.policy_revision == request.policy_revision
        ):
            return ReviewDecision("CANDIDATE_ALLOW", "REVIEW_MATCH")
    return ReviewDecision("DENY", "NO_MATCHING_EXPLICIT_GRANT")
