from pathlib import Path
import math

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = ROOT / "image"
LABEL_DIR = ROOT / "labels"

# Single-class detector label for task 1 (traffic sign region).
CLASS_ID = 0


def iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0 else 0.0


def nms(boxes, scores, threshold=0.4):
    if not boxes:
        return []

    order = sorted(range(len(boxes)), key=lambda index: scores[index], reverse=True)
    keep = []

    while order:
        current = order.pop(0)
        keep.append(current)
        order = [idx for idx in order if iou(boxes[current], boxes[idx]) < threshold]

    return [boxes[index] for index in keep]


def find_candidate_boxes(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Red ranges in HSV for common prohibition/speed-limit signs.
    lower_red_1 = np.array([0, 70, 50])
    upper_red_1 = np.array([10, 255, 255])
    lower_red_2 = np.array([170, 70, 50])
    upper_red_2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
    mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
    mask = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width = image.shape[:2]
    min_area = max(50, int(0.00012 * width * height))

    boxes = []
    scores = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if w < 8 or h < 8:
            continue

        aspect_ratio = w / float(h)
        if aspect_ratio < 0.45 or aspect_ratio > 1.8:
            continue

        circularity = 4.0 * math.pi * area / (perimeter * perimeter)
        fill_ratio = area / float(w * h)

        # Keep red sign-like shapes (circle/triangle) with enough area coverage.
        if circularity < 0.25 or fill_ratio < 0.18:
            continue

        x2, y2 = x + w, y + h
        boxes.append((x, y, x2, y2))

        score = (circularity * 0.6) + (fill_ratio * 0.4)
        scores.append(score)

    return nms(boxes, scores, threshold=0.35)


def to_yolo_line(box, img_w, img_h):
    x1, y1, x2, y2 = box
    bw = x2 - x1
    bh = y2 - y1
    cx = x1 + bw / 2.0
    cy = y1 + bh / 2.0

    return (
        f"{CLASS_ID} "
        f"{cx / img_w:.6f} "
        f"{cy / img_h:.6f} "
        f"{bw / img_w:.6f} "
        f"{bh / img_h:.6f}"
    )


def main():
    LABEL_DIR.mkdir(parents=True, exist_ok=True)

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = [path for path in sorted(IMAGE_DIR.iterdir()) if path.suffix.lower() in image_exts]

    total = 0
    non_empty = 0

    for image_path in images:
        image = cv2.imread(str(image_path))
        if image is None:
            continue

        h, w = image.shape[:2]
        boxes = find_candidate_boxes(image)
        lines = [to_yolo_line(box, w, h) for box in boxes]

        label_path = LABEL_DIR / f"{image_path.stem}.txt"
        content = "\n".join(lines)
        if content:
            content += "\n"
            non_empty += 1

        label_path.write_text(content, encoding="utf-8")
        total += 1

    print(f"Processed {total} images")
    print(f"Generated non-empty labels for {non_empty} images")
    print("Label format: YOLO single-class (class_id=0 => traffic_sign)")


if __name__ == "__main__":
    main()