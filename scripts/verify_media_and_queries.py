"""Small real CPU/media/SQL checks; never substitute for business-scale acceptance."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import httpx
import imageio_ffmpeg
import numpy as np
import psycopg
from poc_control import ROOT, RUNTIME


def main():
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append({"name": name, "status": "PASS"})

    exe = imageio_ffmpeg.get_ffmpeg_exe()
    info = subprocess.run([exe, "-version"], check=True, text=True, capture_output=True).stdout
    with tempfile.TemporaryDirectory(prefix="mt-synthetic-media-") as folder:
        path = Path(folder)/"synthetic.mp4"
        subprocess.run([exe, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                        "color=c=blue:s=64x64:r=10:d=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
        frames = subprocess.run([exe, "-hide_banner", "-loglevel", "error", "-i", str(path),
                                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
        check("ffmpeg_encode_decode_10_frames", len(frames) == 10*64*64*3)
    credentials = json.loads((RUNTIME/"credentials.json").read_text())
    with psycopg.connect(host="127.0.0.1", port=14432, dbname="media_trace_poc", user="poc_app",
                         password=credentials["app"]) as connection:
        result = connection.execute("""WITH RECURSIVE edges(a,b) AS (VALUES(1,2),(2,3),(3,1)),
          walk(node,path) AS (SELECT 1,ARRAY[1] UNION ALL
            SELECT e.b,w.path||e.b FROM walk w JOIN edges e ON e.a=w.node WHERE NOT e.b=ANY(w.path))
          SELECT node FROM walk ORDER BY node""").fetchall()
        check("postgres_recursive_graph_cycle_guard", result == [(1,), (2,), (3,)])
        result = connection.execute("SELECT to_tsvector('simple','media trace evidence') @@ plainto_tsquery('simple','trace evidence')").fetchone()[0]
        check("postgres_simple_fulltext_query", result is True)
    vectors = np.array([[1, 0], [0.8, 0.6], [0, 1]], dtype=np.float32)
    ranking = np.argsort(-(vectors@np.array([1, 0], dtype=np.float32))).tolist()
    check("numpy_exact_vector_ranking", ranking == [0, 1, 2])
    check("internal_inference_requires_auth", httpx.post("http://127.0.0.1:14201/internal/v1/inference/retrieval.image_embedding", json={}).status_code == 401)
    check("internal_inference_validates_contract", httpx.post("http://127.0.0.1:14201/internal/v1/inference/retrieval.image_embedding",
          headers={"Authorization": "Bearer "+credentials["internal_token"]}, json={}).status_code == 422)
    report = {"status": "PASS", "scope": "synthetic_media_and_tiny_query_checks", "checks": checks,
              "ffmpeg_version_output": info, "ffmpeg_sha256": hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
              "source_timestamp_mapping_validated": False, "chinese_search_validated": False,
              "large_vector_index_validated": False, "business_model_validated": False}
    (ROOT/"docs/00-project/validation/media-query-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "checks": len(checks)}))


if __name__ == "__main__":
    main()
