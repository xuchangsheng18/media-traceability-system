"""Validate actual source PTS on marked lossless synthetic frames, including a nonzero origin."""
import hashlib
import json
import re
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from poc_control import ROOT


def main():
    executable = imageio_ffmpeg.get_ffmpeg_exe()
    frames = np.zeros((10, 64, 64, 3), dtype=np.uint8)
    for index in range(10):
        frames[index, :, :, :] = [index*20, 100, 30]
    with tempfile.TemporaryDirectory(prefix="mt-pts-") as folder:
        source = Path(folder)/"synthetic-offset.mkv"
        subprocess.run([executable, "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", "64x64", "-r", "10", "-i", "-", "-vf", "setpts=PTS+5/TB", "-c:v", "ffv1", str(source)],
                       input=frames.tobytes(), capture_output=True, check=True)
        decoded = subprocess.run([executable, "-hide_banner", "-copyts", "-i", str(source),
                                  "-vf", r"select=not(mod(n\,5)),showinfo", "-fps_mode", "passthrough", "-pix_fmt", "rgb24",
                                  "-f", "rawvideo", "-"], capture_output=True, check=True)
        log = decoded.stderr.decode()
        base = re.search(r"config in time_base:\s*(\d+)/(\d+)", log)
        assert base, "SOURCE_TIME_BASE_NOT_OBSERVED"
        time_base = Fraction(int(base[1]), int(base[2]))
        timestamps = [(int(m[1]), Fraction(m[2])) for m in re.finditer(r"\bn:\s*\d+\s+pts:\s*(\d+)\s+pts_time:\s*([\d.]+)", log)]
        assert len(decoded.stdout) == 2*64*64*3 and len(timestamps) == 2
        samples = np.frombuffer(decoded.stdout, dtype=np.uint8).reshape(2, 64, 64, 3)
        assert samples[0, 0, 0, 0] == 0 and samples[1, 0, 0, 0] == 100
        source_ms = [int(pts*time_base*1000) for pts, _ in timestamps]
        assert source_ms == [5000, 5500], "SOURCE_OFFSET_OR_FRAME_MAPPING_LOST"
        assert all(pts*time_base == printed for pts, printed in timestamps)
        mapping = [{"derived_frame_index": index, "source_frame_index": original, "source_pts": timestamps[index][0],
                    "source_time_base": {"numerator": time_base.numerator, "denominator": time_base.denominator},
                    "source_time_ms": source_ms[index], "derived_time_ms": source_ms[index]-source_ms[0]}
                   for index, original in enumerate([0, 5])]
        report = {"status": "PASS", "scope": "lossless_synthetic_frame_sampling_and_source_pts", "mapping_version": "synthetic-pts-map-1",
                  "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "source_nonzero_origin_ms": 5000,
                  "mapping": mapping, "source_bytes_preserved": True, "business_video_pipeline_validated": False,
                  "variable_frame_rate_validated": False}
    (ROOT/"docs/00-project/validation/media-timestamp-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "sampled_frames": len(mapping), "nonzero_source_origin_preserved": True}))


if __name__ == "__main__":
    main()
