from pathlib import Path

import cv2


ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = ROOT / "image"
LABEL_DIR = ROOT / "labels"
OUTPUT_DIR = ROOT / "output" / "label_preview"


def yolo_to_xyxy(xc: float, yc: float, bw: float, bh: float, w: int, h: int):
    x_center = xc * w
    y_center = yc * h
    box_w = bw * w
    box_h = bh * h

    x1 = int(max(0, x_center - box_w / 2))
    y1 = int(max(0, y_center - box_h / 2))
    x2 = int(min(w - 1, x_center + box_w / 2))
    y2 = int(min(h - 1, y_center + box_h / 2))
    return x1, y1, x2, y2


def read_yolo_labels(label_path: Path):
    boxes = []
    if not label_path.exists():
        return boxes

    for line_no, raw_line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) != 5:
            continue

        try:
            class_id = int(parts[0])
            xc, yc, bw, bh = map(float, parts[1:])
        except ValueError:
            continue

        boxes.append((line_no, class_id, xc, yc, bw, bh))

    return boxes


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    total = 0
    with_boxes = 0

    for image_path in sorted(IMAGE_DIR.iterdir()):
        if image_path.suffix.lower() not in image_exts:
            continue

        image = cv2.imread(str(image_path))
        if image is None:
            continue

        h, w = image.shape[:2]
        label_path = LABEL_DIR / f"{image_path.stem}.txt"
        boxes = read_yolo_labels(label_path)

        canvas = image.copy()
        for line_no, class_id, xc, yc, bw, bh in boxes:
            x1, y1, x2, y2 = yolo_to_xyxy(xc, yc, bw, bh, w, h)
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                canvas,
            f"L{line_no} id:{class_id}",
                (x1, max(15, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )

        out_path = OUTPUT_DIR / image_path.name
        cv2.imwrite(str(out_path), canvas)

        if boxes:
            with_boxes += 1
        total += 1

    print(f"Rendered previews: {total}")
    print(f"Images containing boxes: {with_boxes}")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()