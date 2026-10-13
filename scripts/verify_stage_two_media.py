"""Synthetic VFR/audio/subtitle and pixel coordinates, with source bytes and timestamps preserved."""
import datetime
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
    executable, checks = imageio_ffmpeg.get_ffmpeg_exe(), []

    def run(arguments, data=None):
        return subprocess.run([executable, "-hide_banner", *arguments], input=data, capture_output=True, check=True, timeout=60)

    def check(label, condition):
        assert condition, label
        checks.append({"name": label, "status": "PASS"})

    with tempfile.TemporaryDirectory(prefix="mt-vfr-probe-") as folder:
        folder = Path(folder)
        subtitle = folder/"synthetic.srt"
        subtitle.write_text("1\n00:00:05,100 --> 00:00:05,400\nsynthetic VFR caption\n", encoding="utf-8")
        source = folder/"source.mkv"
        frames = np.zeros((8, 48, 64, 3), dtype=np.uint8)
        for index in range(8):
            frames[index, :, :, :] = [index*20, 10, 30]
            frames[index, 8:20, 4:14, :] = [250, 250, 250]
        run(["-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "64x48", "-r", "10", "-i", "-",
             "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=8000:duration=1.6", "-i", str(subtitle),
             "-map", "0:v", "-map", "1:a", "-map", "2:s", "-vf",
             "settb=1/1000,setpts=5000+N*100+floor(N/2)*200+floor(N/4)*200",
             "-af", "asetpts=PTS+5/TB", "-fps_mode", "passthrough", "-enc_time_base", "1/1000",
             "-c:v", "ffv1", "-c:a", "pcm_s16le", "-c:s", "srt", str(source)], frames.tobytes())
        original_digest = hashlib.sha256(source.read_bytes()).hexdigest()
        decoded = run(["-copyts", "-i", str(source), "-map", "0:v", "-vf", "showinfo", "-fps_mode", "passthrough",
                       "-pix_fmt", "rgb24", "-f", "rawvideo", "-"])
        log = decoded.stderr.decode()
        base = re.search(r"config in time_base:\s*(\d+)/(\d+)", log)
        assert base, "SOURCE_TIME_BASE_MISSING"
        time_base = Fraction(int(base[1]), int(base[2]))
        pts = [int(match[1]) for match in re.finditer(r"\bn:\s*\d+\s+pts:\s*(\d+)\s+pts_time:", log)]
        source_ms = [int(value*time_base*1000) for value in pts]
        expected = [5000, 5100, 5400, 5500, 6000, 6100, 6400, 6500]
        check("vfr_exact_source_pts_and_nonzero_origin", source_ms == expected)
        check("irregular_inter_frame_intervals_observed", len(set(np.diff(source_ms).tolist())) > 1)
        pixels = np.frombuffer(decoded.stdout, dtype=np.uint8).reshape(8, 48, 64, 3)
        check("all_vfr_frames_pixel_exact_no_duplicate_or_drop", np.array_equal(pixels, frames))
        sampled = run(["-copyts", "-i", str(source), "-map", "0:v", "-vf", r"select=not(mod(n\,2)),showinfo",
                       "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"])
        sampled_pts = [int(match[1]) for match in re.finditer(r"\bn:\s*\d+\s+pts:\s*(\d+)\s+pts_time:", sampled.stderr.decode())]
        check("sampled_vfr_source_pts_not_frame_rate_formula", sampled_pts == pts[::2])
        check("sampled_pixels_bound_to_original_frame_indices",
              np.array_equal(np.frombuffer(sampled.stdout, dtype=np.uint8).reshape(4, 48, 64, 3), frames[::2]))
        audio = run(["-copyts", "-i", str(source), "-map", "0:a", "-af", "ashowinfo", "-f", "s16le", "-"])
        first = re.search(r"pts_time:([\d.]+)", audio.stderr.decode())
        check("audio_source_origin_preserved", first is not None and Fraction(first[1]) == 5)
        check("audio_all_samples_preserved", len(audio.stdout) == 12800*2)
        extracted = run(["-loglevel", "error", "-copyts", "-i", str(source), "-map", "0:s", "-c:s", "srt", "-f", "srt", "-"])
        caption = extracted.stdout.decode()
        check("subtitle_source_interval_and_text_preserved", "00:00:05,100 --> 00:00:05,400" in caption and "synthetic VFR caption" in caption)
        rotated = run(["-loglevel", "error", "-i", str(source), "-map", "0:v", "-vf", "transpose=1",
                       "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"])
        rotation = np.frombuffer(rotated.stdout, dtype=np.uint8).reshape(8, 64, 48, 3)
        mask = np.all(rotation[0] == [250, 250, 250], axis=2)
        ys, xs = np.where(mask)
        actual_box = [int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1]
        check("clockwise_rotation_half_open_coordinate_mapping", actual_box == [28, 4, 40, 14])
        check("rotation_pixels_match_expected_transform", np.array_equal(rotation, np.rot90(frames, k=-1, axes=(1, 2))))
        check("original_media_digest_unchanged", hashlib.sha256(source.read_bytes()).hexdigest() == original_digest)
        mapping = [{"source_frame_index": index, "source_pts": pts[index], "source_time_ms": source_ms[index],
                    "derived_frame_index": index//2, "derived_time_ms": source_ms[index]-5000} for index in range(0, 8, 2)]
        report = {"status": "PASS", "scope": "synthetic_lossless_8_frame_VFR_PCM_audio_subtitle_clockwise_pixel_mapping",
                  "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "checks": checks,
                  "source_sha256": original_digest, "time_base": [time_base.numerator, time_base.denominator],
                  "source_pts_ms": source_ms, "sampling_mapping": mapping,
                  "rotation_coordinate_convention": "integer_pixel_half_open_bounds_clockwise_90",
                  "real_authorized_media_or_OCR_ASR_validated": False, "full_business_media_pipeline_validated": False,
                  "arbitrary_rotation_crop_transcoding_validated": False}
    (ROOT/"docs/00-project/validation/stage-two-media-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "checks": len(checks), "synthetic_VFR_frames": 8}))


if __name__ == "__main__":
    main()
