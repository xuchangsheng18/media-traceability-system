"""The actual PoC entry must verify its own built frontend before any API writes."""

import importlib
import json
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]


class FrontendAccepted(Exception):
    """Stop the real entry immediately after its frontend gate, before PoC writes."""


@pytest.mark.parametrize(
    "defect",
    [None, "upstream_502", "other_project", "missing_app", "missing_script", "script_502", "script_html"],
    ids=[
        "current_product",
        "upstream_502",
        "other_project",
        "missing_app",
        "missing_script",
        "script_502",
        "script_html",
    ],
)
def test_actual_poc_entry_checks_current_product_and_delivered_script(tmp_path, monkeypatch, defect):
    module = importlib.import_module("scripts.verify_poc")
    html = (ROOT / "frontend/index.html").read_text(encoding="utf8").replace("/src/main.ts", "/assets/index-current.js")
    if defect == "other_project":
        html = html.replace("短视频与图片智能识别溯源系统", "其他项目")
    elif defect == "missing_app":
        html = html.replace('id="app"', 'id="other"')
    elif defect == "missing_script":
        html = html.replace('type="module"', 'type="application/json"')
    requests = []

    def respond(request):
        requests.append(request.url.path)
        assert request.method == "GET", "frontend gate must finish before any PoC write"
        if request.url.path == "/":
            return httpx.Response(
                502 if defect == "upstream_502" else 200,
                headers={"content-type": "text/html; charset=utf-8"},
                text=html,
            )
        if request.url.path == "/assets/index-current.js":
            return httpx.Response(
                502 if defect == "script_502" else 200,
                headers={"content-type": "text/html" if defect == "script_html" else "application/javascript"},
                text="<html>fallback</html>" if defect == "script_html" else "document.querySelector('#app');",
            )
        assert request.url.path == "/api/v1/health"
        raise FrontendAccepted

    (tmp_path / "credentials.json").write_text(json.dumps({"api_token": "synthetic-only"}), encoding="utf8")
    original_client = httpx.Client
    monkeypatch.setattr(module, "RUNTIME", tmp_path)
    monkeypatch.setattr(
        module.httpx, "Client", lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs)
    )
    if defect is None:
        with pytest.raises(FrontendAccepted):
            module.main()
        assert requests == ["/", "/assets/index-current.js", "/api/v1/health"]
    else:
        with pytest.raises(AssertionError, match="^frontend_served$"):
            module.main()
        assert "/api/v1/health" not in requests
