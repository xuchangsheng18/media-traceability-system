"""Recovery readiness includes usable administration, without retrying business writes."""

from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from tests.identity.recovery_lab import LabAdmin, RecoveryLab


def readiness_lab(monkeypatch, failures):
    from tests.identity import recovery_lab

    ticks = iter([0, 0, 1, 181])
    sleeps: list[float] = []
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(recovery_lab.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(recovery_lab.time, "sleep", sleeps.append)

    class Admin:
        def request(self, method, path):
            calls.append((method, path))
            if len(calls) <= failures:
                raise RuntimeError("RECOVERY_LAB_ADMIN_AUTH_UNAVAILABLE")
            return SimpleNamespace(status_code=200)

    lab = RecoveryLab.__new__(RecoveryLab)
    lab.public_url = "https://self-owned.example.invalid"
    monkeypatch.setattr(lab, "readiness", lambda: {"status": "UP"})
    monkeypatch.setattr(
        lab, "http", lambda: nullcontext(SimpleNamespace(get=lambda url: SimpleNamespace(status_code=200)))
    )
    monkeypatch.setattr(lab, "admin", Admin(), raising=False)
    return lab, calls, sleeps


def test_public_discovery_does_not_claim_readiness_before_admin_authentication(monkeypatch):
    lab, calls, sleeps = readiness_lab(monkeypatch, failures=1)
    lab.wait_ready()
    assert calls == [("GET", "/admin/realms/master"), ("GET", "/admin/realms/master")]
    assert sleeps == [1]


def test_permanent_admin_failure_retains_the_existing_readiness_deadline(monkeypatch):
    lab, calls, _ = readiness_lab(monkeypatch, failures=100)
    with pytest.raises(RuntimeError, match="^RECOVERY_LAB_READINESS_TIMEOUT$"):
        lab.wait_ready()
    assert len(calls) == 2


def test_ready_admin_returns_without_sleep_or_mutation(monkeypatch):
    lab, calls, sleeps = readiness_lab(monkeypatch, failures=0)
    lab.wait_ready()
    assert calls == [("GET", "/admin/realms/master")]
    assert sleeps == []


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "RECOVERY_LAB_ADMIN_AUTH_REJECTED"),
        (401, "RECOVERY_LAB_ADMIN_AUTH_REJECTED"),
        (403, "RECOVERY_LAB_ADMIN_AUTH_REJECTED"),
        (500, "RECOVERY_LAB_ADMIN_AUTH_UNAVAILABLE"),
        (502, "RECOVERY_LAB_ADMIN_AUTH_UNAVAILABLE"),
        (503, "RECOVERY_LAB_ADMIN_AUTH_UNAVAILABLE"),
        (302, "RECOVERY_LAB_ADMIN_AUTH_FAILED"),
        (404, "RECOVERY_LAB_ADMIN_AUTH_FAILED"),
    ],
)
def test_admin_authentication_failure_has_only_a_static_nonsecret_reason(status, code):
    private = "self-owned-auth-response-marker-not-a-real-credential"
    posts = []

    def post(url, **kwargs):
        posts.append(url)
        return SimpleNamespace(status_code=status, text=private)

    def forbidden_operation(*args, **kwargs):
        pytest.fail("an unauthenticated administrative operation must never execute")

    client = SimpleNamespace(post=post, request=forbidden_operation)
    lab = SimpleNamespace(
        public_url="https://self-owned.example.invalid",
        admin_url="https://admin.self-owned.example.invalid",
        bootstrap_secret=private,
        http=lambda: nullcontext(client),
    )
    with pytest.raises(RuntimeError) as failure:
        LabAdmin(lab).request("POST", "/admin/realms", body={"realm": private}, expected=(201,))
    assert str(failure.value) == code
    assert private not in repr(failure.value)
    assert len(posts) == 1
