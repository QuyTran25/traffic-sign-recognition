from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from classical_detector import detect_classical
from classical_detector import load_params


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "classical_detector.json"
DEFAULT_OUTDIR = ROOT / "output" / "classical_detector_debug"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Single-image debug runner for classical traffic sign detector.")
    p.add_argument("--image", type=str, required=True, help="Path to an image.")
    p.add_argument("--config", type=str, default=str(DEFAULT_CONFIG), help="Path to JSON config.")
    p.add_argument("--outdir", type=str, default=str(DEFAULT_OUTDIR), help="Output directory.")
    return p.parse_args()


def _save_gray(path: Path, img: np.ndarray) -> None:
    if img is None:
        return
    if img.ndim == 2:
        cv2.imwrite(str(path), img)
    else:
        cv2.imwrite(str(path), img)


def main() -> None:
    args = parse_args()
    image_path = Path(args.image)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    params = load_params(args.config)

    bgr = cv2.imread(str(image_path))
    if bgr is None:
        raise SystemExit(f"Cannot read image: {image_path}")

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    result = detect_classical(rgb, params, return_debug=True)

    # Save intermediate debug images
    debug = result.get("debug", {})
    if debug:
        pre = debug.get("preprocessed")
        mask = debug.get("mask_color")
        edges = debug.get("edges")
        combined = debug.get("combined")
        overlay_shapes = debug.get("overlay_shapes")
        overlay = debug.get("overlay")

        if pre is not None:
            cv2.imwrite(str(outdir / "01_preprocessed.jpg"), pre)
        if mask is not None:
            cv2.imwrite(str(outdir / "02_mask_color.png"), mask)
        if edges is not None:
            cv2.imwrite(str(outdir / "03_edges.png"), edges)
        if combined is not None:
            cv2.imwrite(str(outdir / "04_combined.png"), combined)
        if overlay_shapes is not None:
            cv2.imwrite(str(outdir / "05_shapes_overlay.jpg"), overlay_shapes)
        if overlay is not None:
            cv2.imwrite(str(outdir / "06_final_overlay.jpg"), overlay)

    # Also write a small text summary
    lines = []
    for bb, sc in zip(result["bboxes"], result["scores"]):
        lines.append(f"{bb} score={sc:.3f}")

    (outdir / "detections.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Saved debug outputs to: {outdir}")
    print(f"Detections: {len(result['bboxes'])}")


if __name__ == "__main__":
    main()
