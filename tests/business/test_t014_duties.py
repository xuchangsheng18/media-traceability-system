"""Named synthetic person mappings, distinct humans, current duties and approval TTL."""

import time
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.controls.providers import ApprovalRule
from business_app.errors import BusinessError
from business_app.permissions.types import Principal
from business_app.types import Actor, Scope

from tests.business.test_controls import AUTH, approve, decision, export_fixture, request_approval, review_body
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_module

NOW = 2_000_000_000


def environment():
    module = permission_module("duties")
    org, case = uuid4(), uuid4()
    actors = [Actor(uuid4(), org) for _ in range(6)]
    persons = {a: module.VerifiedPerson(a, uuid4(), "synthetic-person-v1", NOW + 600) for a in actors}

    class People:
        def resolve(self, actor):
            return persons[actor]

    class Assignments:
        submitters = frozenset({actors[0]})
        executors = frozenset({actors[0]})
        evaluators: frozenset[Actor] = frozenset()
        version = "a" * 64

        def read(self, target, *, connection):
            return module.DutyActors(target, self.submitters, self.executors, self.evaluators, self.version, NOW + 500)

    assignments = Assignments()
    clock = [NOW]
    duties = module.IndependentDuties(People(), assignments, clock=lambda: clock[0])
    item = dict(
        object_type="task",
        object_id=uuid4(),
        object_version=1,
        purpose="seal",
        policy_version="synthetic-policy-v1",
        run_version=1,
        result_version=1,
        requested_by=actors[0].user_id,
    )
    scope = Scope(actors[0], case)
    return SimpleNamespace(
        module=module,
        actors=actors,
        persons=persons,
        assignments=assignments,
        duties=duties,
        clock=clock,
        item=item,
        scope=scope,
    )


def collect(env, votes, extra=()):
    rows = [dict(decision="approve", decision_actor_id=a.user_id, evidence_refs={}) for a in votes]
    return env.duties.collect(env.scope, env.item, rows, connection=None, extra_actors=frozenset(extra))


def test_two_subjects_or_two_users_for_same_person_count_once():
    e = environment()
    first, alias = e.actors[1:3]
    e.persons[alias] = replace(e.persons[alias], person_id=e.persons[first].person_id)
    facts = collect(e, [first, alias])
    assert len(facts.approved_people) == 1
    with pytest.raises(BusinessError) as caught:
        e.duties.validate_approval(facts, ApprovalRule("synthetic-policy-v1", 1800, 2))
    assert (caught.value.code, caught.value.http_status) == ("INDEPENDENT_APPROVER_REQUIRED", 403)
    one = collect(e, [first], extra=[alias])
    with pytest.raises(BusinessError):
        e.duties.candidate(alias, one)


@pytest.mark.parametrize("duty", ["applicant", "submitters", "executors", "evaluators"])
def test_applicant_submitter_executor_or_evaluator_cannot_approve(duty):
    e = environment()
    actor = e.actors[0] if duty == "applicant" else e.actors[1]
    if duty != "applicant":
        setattr(e.assignments, duty, frozenset({actor}))
    facts = collect(e, [], extra=[actor])
    with pytest.raises(BusinessError) as caught:
        e.duties.candidate(actor, facts)
    assert (caught.value.code, caught.value.http_status) == ("INDEPENDENT_APPROVER_REQUIRED", 403)


def test_changed_executor_invalidates_approval_consumption():
    e = environment()
    first, second = e.actors[1:3]
    facts = collect(e, [first, second])
    rule = ApprovalRule("synthetic-policy-v1", 1800, 2)
    e.duties.validate_approval(facts, rule)
    proof = e.duties.decision_proof(first, facts)
    e.assignments.executors = frozenset({first})
    e.assignments.version = "b" * 64
    changed = collect(e, [first, second])
    assert changed.context_digest != facts.context_digest
    with pytest.raises(BusinessError):
        e.duties.validate_approval(changed, rule)
    with pytest.raises(BusinessError):
        e.duties.validate_records(
            changed, [dict(decision="approve", decision_actor_id=first.user_id, evidence_refs={"independence": proof})]
        )


def test_one_approval_cannot_satisfy_high_risk_rule():
    e = environment()
    facts = collect(e, [e.actors[1]])
    with pytest.raises(BusinessError) as caught:
        e.duties.validate_approval(facts, ApprovalRule("synthetic-policy-v1", 1800, 2))
    assert caught.value.http_status == 403
    with pytest.raises(BusinessError) as invalid_rule:
        e.duties.validate_approval(facts, ApprovalRule("synthetic-policy-v1", 1800, 1))
    assert invalid_rule.value.http_status == 503


def test_approval_expiry_at_1800_seconds_is_invalid():
    e = environment()
    rule = ApprovalRule("synthetic-policy-v1", 1800, 2)
    created = datetime.fromtimestamp(NOW, timezone.utc)
    expires = datetime.fromtimestamp(NOW + 1800, timezone.utc)
    e.clock[0] = NOW + 1799
    assert e.duties.approval_live(created, expires, rule) is True
    e.clock[0] = NOW + 1800
    assert e.duties.approval_live(created, expires, rule) is False
    e.clock[0] = NOW
    assert e.duties.approval_live(created, datetime.fromtimestamp(NOW + 1801, timezone.utc), rule) is False


@pytest.mark.parametrize("defect", ["missing", "actor", "person", "mapping", "expired", "bool_expiry"])
def test_human_provider_is_explicit_and_mapping_is_validated(defect):
    e = environment()
    person = e.persons[e.actors[1]]
    if defect == "missing":
        e.duties.people = None
    else:
        values = {
            "actor": replace(person, actor=e.actors[2]),
            "person": replace(person, person_id="same-name-is-not-a-person-id"),
            "mapping": replace(person, mapping_version=""),
            "expired": replace(person, valid_until=NOW),
            "bool_expiry": replace(person, valid_until=True),
        }
        e.persons[e.actors[1]] = values[defect]
    with pytest.raises(BusinessError) as caught:
        collect(e, [e.actors[1]])
    assert caught.value.http_status == 503


def test_current_mapping_version_and_object_are_bound_to_each_vote():
    e = environment()
    first, second = e.actors[1:3]
    facts = collect(e, [first, second])
    records = [
        dict(
            decision="approve",
            decision_actor_id=a.user_id,
            evidence_refs={"independence": e.duties.decision_proof(a, facts)},
        )
        for a in [first, second]
    ]
    e.duties.validate_records(facts, records)
    e.persons[first] = replace(e.persons[first], mapping_version="synthetic-person-v2")
    changed = collect(e, [first, second])
    with pytest.raises(BusinessError):
        e.duties.validate_records(changed, records)
    principal = Principal(e.actors[0], "https://synthetic.example.test", "self-owned", NOW + 600)
    wrong = replace(facts.target, object_id=uuid4())
    with pytest.raises(BusinessError):
        e.duties.check(principal, wrong, facts, ApprovalRule("synthetic-policy-v1", 1800, 2))


def test_plain_unbound_duty_facts_cannot_authorize():
    e = environment()
    facts = e.module.DutyFacts(uuid4(), frozenset(), frozenset(), frozenset(), frozenset({uuid4(), uuid4()}), "a" * 64)
    with pytest.raises(BusinessError):
        e.duties.validate_approval(facts, ApprovalRule("synthetic-policy-v1", 1800, 2))


def install_http_duties(c, same_person=False):
    m = permission_module("duties")
    deadline = int(time.time()) + 1800
    actors = [c["actor"], *c["reviewers"]]
    persons = {a: m.VerifiedPerson(a, uuid4(), "explicit-synthetic-person-v1", deadline) for a in actors}
    if same_person:
        persons[actors[2]] = replace(persons[actors[2]], person_id=persons[actors[1]].person_id)

    class People:
        def resolve(self, actor):
            return persons[actor]

    class Duties:
        executors = frozenset({actors[0]})
        version = "a" * 64

        def read(self, target, *, connection):
            return m.DutyActors(target, frozenset({actors[0]}), self.executors, frozenset(), self.version, deadline)

    class Rules:
        ttl = 1800

        def approval(self, scope, purpose, version):
            return ApprovalRule(version, self.ttl, 2)

    assignments = Duties()
    rules = Rules()
    port = m.IndependentDuties(People(), assignments)
    c["control_app"].state.approvals.duties = port
    c["control_app"].state.approvals.rules = rules
    return port, assignments, rules


def test_real_approval_two_users_same_person_never_write_approved(control_context):
    c = control_context
    install_http_duties(c, same_person=True)
    identifier = request_approval(c)
    first = decision(c, identifier, "test-only-reviewer-1")
    assert first.status_code == 201 and first.json()["state"] == "REQUESTED"
    second = decision(c, identifier, "test-only-reviewer-2")
    assert second.status_code == 403
    assert second.json()["code"] == "INDEPENDENT_APPROVER_REQUIRED"
    with psycopg.connect(c["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT state FROM mt.approval_request WHERE approval_id=%s", (identifier,)
        ).fetchone() == ("REQUESTED",)
        assert admin.execute(
            "SELECT count(*) FROM mt.approval_decision WHERE approval_id=%s", (identifier,)
        ).fetchone() == (1,)


def test_real_current_executor_change_invalidates_without_deleting_votes(control_context):
    c = control_context
    _, assignments, _ = install_http_duties(c)
    identifier = request_approval(c)
    approve(c, identifier)
    assignments.executors = frozenset({c["reviewers"][0]})
    assignments.version = "b" * 64
    response = c["control_http"].get("/api/v1/approvals/" + identifier, headers=AUTH)
    assert response.status_code == 200
    assert response.json()["approval"]["state"] == "INVALIDATED"
    assert len(response.json()["decisions"]) == 2
    with psycopg.connect(c["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT state FROM mt.approval_request WHERE approval_id=%s", (identifier,)
        ).fetchone() == ("APPROVED",)


@pytest.mark.parametrize("defect", ["missing_provider", "ttl_over_1800"])
def test_real_approval_missing_people_or_extended_TTL_has_no_write(control_context, defect):
    c = control_context
    _, _, rules = install_http_duties(c)
    if defect == "missing_provider":
        c["control_app"].state.approvals.duties = None
    else:
        rules.ttl = 1801
    body = dict(
        case_id=str(c["case_id"]),
        object_type="task",
        object_id=str(c["task_id"]),
        object_version=1,
        purpose="review",
        policy_version="policy-dev-1",
        reason="self-owned",
        run_version=1,
        result_version=1,
    )
    response = c["control_http"].post(
        "/api/v1/approvals", json=body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    )
    assert response.status_code == 503
    with psycopg.connect(c["admin_dsn"]) as admin:
        assert admin.execute("SELECT count(*) FROM mt.approval_request").fetchone() == (0,)


def test_legacy_votes_without_person_binding_are_not_consumable(control_context):
    c = control_context
    install_http_duties(c)
    identifier = request_approval(c)
    with psycopg.connect(c["admin_dsn"]) as admin:
        for actor in c["reviewers"]:
            admin.execute(
                "INSERT INTO mt.approval_decision(decision_id,org_id,case_id,approval_id,decision,decision_actor_id,reason,evidence_refs,policy_version) VALUES(%s,%s,%s,%s,'approve',%s,'synthetic legacy fixture','{}'::jsonb,'policy-dev-1')",
                (uuid4(), actor.org_id, c["case_id"], identifier, actor.user_id),
            )
        admin.execute(
            "UPDATE mt.approval_request SET state='APPROVED',row_version=row_version+1 WHERE approval_id=%s",
            (identifier,),
        )
    response = c["control_http"].get("/api/v1/approvals/" + identifier, headers=AUTH)
    assert response.status_code == 200
    assert response.json()["approval"]["state"] == "INVALIDATED"


@pytest.mark.parametrize("defect", ["unbound_approved_person", "wrong_mapping_type", "wrong_actor_type"])
def test_bound_duties_reject_unverified_people_or_malformed_bindings(defect):
    e = environment()
    facts = collect(e, e.actors[1:3])
    if defect == "unbound_approved_person":
        facts = replace(facts, approved_people=facts.approved_people | {uuid4()})
    else:
        bindings = dict(facts.bindings)
        first = e.actors[1]
        person = bindings[first.user_id]
        bindings[first.user_id] = replace(
            person, **({"mapping_version": None} if defect == "wrong_mapping_type" else {"actor": None})
        )
        facts = replace(facts, bindings=bindings)
    with pytest.raises(BusinessError) as caught:
        e.duties.validate_approval(facts, ApprovalRule("synthetic-policy-v1", 1800, 2))
    assert caught.value.http_status == 503


def test_failed_assignment_reread_is_a_safe_unavailable_error():
    e = environment()
    original = e.assignments

    class UnavailableOnReread:
        calls = 0

        def read(self, target, *, connection):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("synthetic upstream unavailable")
            return original.read(target, connection=connection)

    e.duties.assignments = UnavailableOnReread()
    with pytest.raises(BusinessError) as caught:
        collect(e, e.actors[1:3])
    assert caught.value.http_status == 503


def post_review(c, token):
    http = c["control_http"]
    current = http.get(f"/api/v1/analysis/tasks/{c['task_id']}/review-context", headers=AUTH)
    assert current.status_code == 200
    return http.post(
        "/api/v1/reviews",
        json=review_body(c),
        headers={
            "Authorization": "Bearer " + token,
            "If-Match": current.headers["ETag"],
            "Idempotency-Key": uuid4().hex,
        },
    )


@pytest.mark.parametrize("conflict", ["creator", "same_person_alias", "current_executor", "missing_provider"])
def test_real_review_checks_human_independence_before_any_write(control_context, conflict):
    c = control_context
    port, assignments, _ = install_http_duties(c)
    token = "test-only-reviewer-1"
    if conflict == "creator":
        token = "test-only-valid-token"
    elif conflict == "same_person_alias":
        creator_person = port.person(c["actor"])
        original = port.people

        class AliasedPerson:
            def resolve(self, actor):
                assert original is not None
                value = original.resolve(actor)
                return replace(value, person_id=creator_person.person_id) if actor == c["reviewers"][0] else value

        port.people = AliasedPerson()
    elif conflict == "current_executor":
        assignments.executors = frozenset({c["reviewers"][0]})
    c["control_app"].state.reviews.duties = None if conflict == "missing_provider" else port
    response = post_review(c, token)
    assert response.status_code == (503 if conflict == "missing_provider" else 403), response.json()
    with psycopg.connect(c["admin_dsn"]) as admin:
        assert admin.execute("SELECT count(*) FROM mt.review_record").fetchone() == (0,)
        assert admin.execute(
            "SELECT count(*) FROM mt.idempotency_record WHERE operation='createReview'"
        ).fetchone() == (0,)


def test_real_export_consumer_rejects_current_executor_conflict(control_context):
    c = control_context
    _, assignments, _ = install_http_duties(c)
    identifier, _ = export_fixture(c)
    assignments.executors = frozenset({c["reviewers"][0]})
    assignments.version = "b" * 64
    with pytest.raises(BusinessError) as caught:
        c["control_app"].state.exports.process(Scope(c["actor"], c["case_id"]), UUID(identifier))
    assert (caught.value.code, caught.value.http_status) == ("EXPORT_APPROVAL_INVALID", 403)
    with psycopg.connect(c["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT state,artifact_ref FROM mt.audit_export WHERE export_id=%s", (identifier,)
        ).fetchone() == ("REQUESTED", {})
