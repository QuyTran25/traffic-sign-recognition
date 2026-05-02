from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from classical_detector import detect_classical
from classical_detector import load_params


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "classical_detector.json"
DEFAULT_DATASET = ROOT / "data" / "detection"
DEFAULT_OUTDIR = ROOT / "output" / "hard_negatives"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mine hard negatives (false positives) for classical detector.")
    p.add_argument("--images", type=str, default="", help="Optional: image folder to mine (no labels).")
    p.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET), help="YOLO dataset root (images/labels).")
    p.add_argument("--split", type=str, default="val", choices=["train", "val"], help="Split when using --dataset.")
    p.add_argument("--config", type=str, default=str(DEFAULT_CONFIG), help="Detector config JSON.")
    p.add_argument("--outdir", type=str, default=str(DEFAULT_OUTDIR), help="Output folder to store crops.")
    p.add_argument("--iou", type=float, default=0.3, help="If labels exist: IoU threshold to consider as match (not FP).")
    p.add_argument("--max-per-image", type=int, default=10, help="Max crops per image.")
    return p.parse_args()


def iou_xyxy(a: list[int], b: list[int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    iw = max(0, inter_x2 - inter_x1)
    ih = max(0, inter_y2 - inter_y1)
    inter = iw * ih
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter
    return float(inter / union) if union > 0 else 0.0


def read_yolo_labels(path: Path, w: int, h: int) -> list[list[int]]:
    if not path.exists():
        return []
    out: list[list[int]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.strip().split()
        if len(parts) != 5:
            continue
        try:
            _cls = int(parts[0])
            xc, yc, bw, bh = map(float, parts[1:])
        except ValueError:
            continue
        x_center = xc * w
        y_center = yc * h
        box_w = bw * w
        box_h = bh * h
        x1 = int(round(x_center - box_w / 2.0))
        y1 = int(round(y_center - box_h / 2.0))
        x2 = int(round(x_center + box_w / 2.0))
        y2 = int(round(y_center + box_h / 2.0))
        x1 = max(0, min(w - 1, x1))
        y1 = max(0, min(h - 1, y1))
        x2 = max(0, min(w, x2))
        y2 = max(0, min(h, y2))
        if x2 <= x1 or y2 <= y1:
            continue
        out.append([x1, y1, x2, y2])
    return out


def main() -> None:
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    params = load_params(args.config)

    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    if args.images:
        img_dir = Path(args.images)
        lbl_dir = None
    else:
        dataset = Path(args.dataset)
        img_dir = dataset / "images" / args.split
        lbl_dir = dataset / "labels" / args.split

    saved = 0

    for img_path in sorted(img_dir.iterdir()):
        if img_path.suffix.lower() not in exts:
            continue

        bgr = cv2.imread(str(img_path))
        if bgr is None:
            continue

        h, w = bgr.shape[:2]
        gts: list[list[int]] = []
        if lbl_dir is not None:
            gts = read_yolo_labels(lbl_dir / f"{img_path.stem}.txt", w, h)

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        det = detect_classical(rgb, params, return_debug=False)
        preds = det["bboxes"]
        scores = det["scores"]

        # Sort preds by score and keep at most N per image.
        order = sorted(range(len(preds)), key=lambda i: scores[i], reverse=True)[: int(args.max_per_image)]

        for rank, i in enumerate(order):
            bb = preds[i]
            is_fp = True
            if gts:
                for gt in gts:
                    if iou_xyxy(bb, gt) >= float(args.iou):
                        is_fp = False
                        break
            if not is_fp:
                continue

            x1, y1, x2, y2 = bb
            crop = bgr[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            out_path = outdir / f"{img_path.stem}_fp{rank:02d}_s{scores[i]:.3f}.jpg"
            cv2.imwrite(str(out_path), crop)
            saved += 1

    print(f"Saved hard negatives: {saved}")
    print(f"Output folder: {outdir}")


if __name__ == "__main__":
    main()
