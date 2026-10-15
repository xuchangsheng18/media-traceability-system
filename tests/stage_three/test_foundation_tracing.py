import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import httpx
import pytest
from app.observability import configure
from app.tracing import safe_log, trace_context


def test_default_uvicorn_access_logger_cannot_emit_raw_targets(caplog):
    app = FastAPI()
    configure(app)
    with caplog.at_level("INFO"):
        logging.getLogger("uvicorn.access").info("GET /raw-private-target?token=private-query-sentinel")
    assert "raw-private-target" not in caplog.text
    assert "private-query-sentinel" not in caplog.text


def test_poc_unmatched_and_sensitive_http_exceptions_use_uniform_errors():
    from fastapi import HTTPException

    app = FastAPI()
    configure(app)

    @app.get("/unsafe")
    def unsafe():
        raise HTTPException(400, "private-sensitive-exception")

    client = TestClient(app)
    missing, unsafe_response = client.get("/absent"), client.get("/unsafe")
    assert missing.json().get("code") == "RESOURCE_NOT_FOUND"
    assert missing.headers["X-Trace-Id"]
    assert unsafe_response.json()["code"] == "HTTP_STATUS_400"
    assert "private-sensitive-exception" not in unsafe_response.text


from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_request_trace_is_uuid_derived_and_secret_free(caplog):
    app = FastAPI()
    configure(app, trust_request_id=True)

    @app.get("/items/{item_id}")
    def item(item_id: str):
        return {"ok": True}

    request_id = str(uuid4())
    with caplog.at_level("INFO", logger="media_trace"):
        response = TestClient(app).get(
            "/items/private-path?token=private-query",
            headers={
                "X-Request-Id": request_id,
                "Authorization": "Bearer private-header",
            },
        )
    assert response.headers.get("X-Trace-Id") == request_id.replace("-", "")
    records = [json.loads(record.message) for record in caplog.records if record.name == "media_trace"]
    assert records[-1]["trace_id"] == request_id.replace("-", "")
    assert records[-1]["route"] == "/items/{item_id}"
    assert not any(value in caplog.text for value in ["private-path", "private-query", "private-header"])


def test_parallel_requests_do_not_share_trace_context():
    app = FastAPI()
    configure(app, trust_request_id=True)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    identifiers = [str(uuid4()) for _ in range(8)]

    def run(identifier):
        response = TestClient(app).get("/ok", headers={"X-Request-Id": identifier})
        return response.headers.get("X-Trace-Id")

    with ThreadPoolExecutor(max_workers=4) as pool:
        actual = list(pool.map(run, identifiers))
    assert actual == [value.replace("-", "") for value in identifiers]


def test_interleaved_requests_keep_each_internal_log_bound_to_its_request(caplog):
    app = FastAPI()
    configure(app, trust_request_id=True)
    identities = {str(uuid4()): str(uuid4()) for _ in range(8)}

    async def exercise():
        ready = asyncio.Event()
        entered = 0

        @app.get("/trace/{task_id}")
        async def traced(task_id: str):
            nonlocal entered
            safe_log("test.route.entered", task_id=task_id)
            entered += 1
            if entered == len(identities):
                ready.set()
            await asyncio.wait_for(ready.wait(), timeout=10)
            safe_log("test.route.resumed", task_id=task_id)
            return {"ok": True}

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://self-owned.test") as http:
            responses = await asyncio.gather(
                *[
                    http.get(f"/trace/{task}", headers={"X-Request-Id": identifier})
                    for task, identifier in identities.items()
                ]
            )
        assert all(response.status_code == 200 for response in responses)
        safe_log("test.after.requests.without.context")

    with caplog.at_level("INFO", logger="media_trace"):
        asyncio.run(exercise())
    records = [json.loads(record.message) for record in caplog.records if record.name == "media_trace"]
    inner = [record for record in records if record["event"] in {"test.route.entered", "test.route.resumed"}]
    assert len(inner) == 2 * len(identities)
    assert {record["task_id"] for record in inner} == set(identities)
    for task, identifier in identities.items():
        task_records = [record for record in inner if record["task_id"] == task]
        assert {record["event"] for record in task_records} == {"test.route.entered", "test.route.resumed"}
        assert all(
            record["request_id"] == identifier and record["trace_id"] == identifier.replace("-", "")
            for record in task_records
        )
    assert not any(record["event"] == "test.after.requests.without.context" for record in records)


def test_nested_trace_exception_restores_outer_context_and_clears_at_exit(caplog):
    outer, inner = str(uuid4()), str(uuid4())
    with caplog.at_level("INFO", logger="media_trace"):
        with trace_context(outer):
            safe_log("test.outer.before")
            with pytest.raises(RuntimeError, match="CONTROLLED_SELF_OWNED_FAILURE"):
                with trace_context(inner):
                    safe_log("test.inner.before.failure")
                    raise RuntimeError("CONTROLLED_SELF_OWNED_FAILURE")
            safe_log("test.outer.after")
        safe_log("test.outside.context")
    records = [json.loads(record.message) for record in caplog.records if record.name == "media_trace"]
    assert [(record["event"], record["request_id"]) for record in records] == [
        ("test.outer.before", outer),
        ("test.inner.before.failure", inner),
        ("test.outer.after", outer),
    ]
