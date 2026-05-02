from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from eval_classical_detector import main as _eval_main


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "classical_detector.json"
DEFAULT_OUTDIR = ROOT / "output" / "classical_detector_eval" / "ablation"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run simple ablations for classical detector (Người 1).")
    p.add_argument("--dataset", type=str, default=str(ROOT / "data" / "detection"), help="YOLO dataset root.")
    p.add_argument("--split", type=str, default="val", choices=["train", "val"], help="Split.")
    p.add_argument("--config", type=str, default=str(DEFAULT_CONFIG), help="Base config JSON.")
    p.add_argument("--outdir", type=str, default=str(DEFAULT_OUTDIR), help="Output directory.")
    p.add_argument("--iou", type=float, default=0.5, help="IoU threshold.")
    return p.parse_args()


def _run_eval(dataset: str, split: str, config_path: str, outdir: str, iou: float) -> None:
    # Reuse eval script by simulating argv.
    import sys

    old = sys.argv
    try:
        sys.argv = [
            old[0],
            "--dataset",
            dataset,
            "--split",
            split,
            "--config",
            config_path,
            "--outdir",
            outdir,
            "--iou",
            str(iou),
        ]
        _eval_main()
    finally:
        sys.argv = old


def main() -> None:
    args = parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    base_cfg_path = Path(args.config)
    base_cfg = json.loads(base_cfg_path.read_text(encoding="utf-8"))

    variants: dict[str, dict] = {
        "base": deepcopy(base_cfg),
        "no_clahe": {**deepcopy(base_cfg), "clahe_clip_limit": None},
        "no_gamma": {**deepcopy(base_cfg), "gamma": None},
        # Disable shape contributions (and keep only color+edge).
        "no_shape": {
            **deepcopy(base_cfg),
            "w_shape": 0.0,
            "use_hough_circle": False,
            "use_hough_lines": False,
        },
    }

    for name, cfg in variants.items():
        cfg_path = outdir / f"{name}.json"
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        _run_eval(args.dataset, args.split, str(cfg_path), str(outdir), float(args.iou))

    print(f"Saved ablation configs + metrics under: {outdir}")


if __name__ == "__main__":
    main()
