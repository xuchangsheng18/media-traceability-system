import datetime
import hashlib
import hmac
import io
import json
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import torch
from app.common import ROOT, get_object, put_object
from fastapi import FastAPI, Header, HTTPException
from jsonschema import Draft202012Validator, FormatChecker
from PIL import Image
from referencing import Registry, Resource

torch.set_num_threads(1)
MODEL_PATH = Path(os.environ.get("MODEL_DIR", "/runtime")) / "synthetic-encoder.pt"
SCHEMAS = {}
for schema_path in (ROOT / "schemas").rglob("*.schema.json"):
    schema = json.loads(schema_path.read_text())
    SCHEMAS[schema["$id"]] = schema
REGISTRY = Registry().with_resources((k, Resource.from_contents(v)) for k, v in SCHEMAS.items())
VALIDATORS = {kind: Draft202012Validator(SCHEMAS[f"urn:media-trace:model:M15:{kind}:0.1.0"], registry=REGISTRY,
              format_checker=FormatChecker()) for kind in ["request", "response"]}
encoder = torch.nn.Sequential(torch.nn.Linear(16, 8), torch.nn.Tanh())


def initialize_model():
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MODEL_PATH.exists():
        torch.manual_seed(20261012)
        encoder.apply(lambda layer: layer.reset_parameters() if hasattr(layer, "reset_parameters") else None)
        decoder = torch.nn.Linear(8, 16)
        x = torch.rand(64, 16)
        optimizer = torch.optim.Adam([*encoder.parameters(), *decoder.parameters()], lr=0.02)
        losses = []
        for _ in range(120):
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(decoder(encoder(x)), x)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        torch.save(encoder.state_dict(), MODEL_PATH)
        (MODEL_PATH.parent / "experiment.json").write_text(json.dumps({"seed": 20261012, "samples": 64,
          "dataset": "synthetic-uniform-16d", "steps": 120, "first_loss": losses[0], "last_loss": losses[-1],
          "torch": torch.__version__, "device": "cpu", "business_model": False}, indent=2))
    encoder.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
    encoder.eval()


@asynccontextmanager
async def lifespan(_):
    initialize_model()
    yield


app = FastAPI(title="Synthetic CPU inference baseline", lifespan=lifespan)


@app.get("/healthz")
def health():
    return {"status": "ok", "python_profile": "py310", "python": sys.version.split()[0], "torch": torch.__version__, "device": "cpu",
            "model_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(), "business_model": False}


@app.post("/internal/v1/inference/retrieval.image_embedding")
def inference(body: dict, authorization: str | None = Header(default=None)):
    if not authorization or not hmac.compare_digest(authorization, "Bearer "+os.environ["INTERNAL_TOKEN"]):
        raise HTTPException(401, "AUTH_REQUIRED")
    errors = list(VALIDATORS["request"].iter_errors(body))
    if errors:
        raise HTTPException(422, "MODEL_CONTRACT_INVALID")
    if body["model_name"] != "synthetic-cpu-encoder" or body["model_version"] != "demo-1" or len(body["object_refs"]) != 1:
        raise HTTPException(422, "MODEL_NOT_SUPPORTED")
    if datetime.datetime.fromisoformat(body["deadline_at"].replace("Z", "+00:00")) <= datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(422, "DEADLINE_EXPIRED")
    started = time.monotonic()
    raw = get_object(body["object_refs"][0], "analysis")
    with Image.open(io.BytesIO(raw)) as image:
        x = torch.from_numpy(np.asarray(image.convert("L").resize((4, 4)), dtype=np.float32).reshape(1, 16)/255)
    with torch.no_grad():
        vector = torch.nn.functional.normalize(encoder(x), dim=1).numpy().astype("float32")
    ref = put_object(str(uuid.uuid4()), vector.tobytes(), "vectors")
    result = {"request_id": body["request_id"], "task_id": body["task_id"], "run_version": body["run_version"],
              "capability": body["capability"], "model_name": body["model_name"], "model_version": body["model_version"],
              "preprocessing_version": body["preprocessing_version"], "mapping_version": body["mapping_version"],
              "status": "SUCCEEDED", "output_kind": "embedding", "findings": [], "artifacts": [ref],
              "missing_modalities": [], "warnings": ["synthetic CPU model; not SSCD; not validated for business retrieval"],
              "reason": None, "latency_ms": int((time.monotonic()-started)*1000), "mock": False,
              "payload": {"dimension": 8, "dtype": "float32", "normalization": "l2", "vector_ref": ref}}
    VALIDATORS["response"].validate(result)
    return result
