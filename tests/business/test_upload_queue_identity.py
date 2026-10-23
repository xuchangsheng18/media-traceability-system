"""Routing is selected-upload identity, never permission or a legacy fallback."""

from dataclasses import replace
from typing import Any, cast
from uuid import UUID

import pytest
from business_app.errors import BusinessError
from business_app.types import Actor, Scope
from business_app.uploads.messaging import validation_queue_name

USER = UUID("10000000-0000-4000-8000-000000000001")
ORG = UUID("20000000-0000-4000-8000-000000000001")
CASE = UUID("30000000-0000-4000-8000-000000000001")
UPLOAD = UUID("40000000-0000-4000-8000-000000000001")
OTHER = UUID("90000000-0000-4000-8000-000000000001")
SCOPE = Scope(Actor(USER, ORG), CASE)


def test_queue_is_versioned_deterministic_and_contains_exact_org_case_upload():
    expected = f"mt_business_validation_v2_{ORG.hex}_{CASE.hex}_{UPLOAD.hex}"
    assert validation_queue_name(SCOPE, UPLOAD) == expected
    assert validation_queue_name(SCOPE, UUID(str(UPLOAD).upper())) == expected
    assert expected.isascii() and len(expected.encode("ascii")) <= 255
    assert expected != "mt_business_validation_" + CASE.hex


@pytest.mark.parametrize("changed", ["org", "case", "upload"])
def test_each_routing_identity_component_partitions_the_queue(changed):
    scope, upload = SCOPE, UPLOAD
    if changed == "org":
        scope = replace(scope, actor=replace(scope.actor, org_id=OTHER))
    elif changed == "case":
        scope = replace(scope, case_id=OTHER)
    else:
        upload = OTHER
    assert validation_queue_name(scope, upload) != validation_queue_name(SCOPE, UPLOAD)


def test_another_actor_does_not_create_an_alternate_queue_for_the_same_upload():
    # Existing work authorization and delivery/owner checks remain mandatory;
    # queue selection alone does not grant a second actor any access.
    other = replace(SCOPE, actor=replace(SCOPE.actor, user_id=OTHER))
    assert validation_queue_name(other, UPLOAD) == validation_queue_name(SCOPE, UPLOAD)


@pytest.mark.parametrize("field", ["user", "org", "case", "upload"])
@pytest.mark.parametrize("invalid", [None, "not-uuid", "40000000-0000-4000-8000-000000000001", UUID(int=0), 1, True])
def test_missing_non_uuid_or_nil_identity_fails_closed(field, invalid):
    scope: Any = SCOPE
    upload: Any = UPLOAD
    if field in {"user", "org"}:
        scope = replace(scope, actor=replace(scope.actor, **{field + "_id": invalid}))
    elif field == "case":
        scope = replace(scope, case_id=invalid)
    else:
        upload = invalid
    with pytest.raises(BusinessError) as failure:
        validation_queue_name(cast(Scope, scope), cast(UUID, upload))
    assert (failure.value.code, failure.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)


@pytest.mark.parametrize("scope", [None, {}, object(), Scope(cast(Actor, None), CASE)])
def test_wrong_scope_shape_cannot_construct_a_queue(scope):
    with pytest.raises(BusinessError) as failure:
        validation_queue_name(cast(Scope, scope), UPLOAD)
    assert (failure.value.code, failure.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)
