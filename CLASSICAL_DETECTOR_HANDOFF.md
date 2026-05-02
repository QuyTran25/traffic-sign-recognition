# Classical Detector (Người 1) — Handoff

Mục tiêu: detector cổ điển (CV, image-only) để đề tài **Detect 1 class traffic_sign → crop → classify (43 + background)**.

## 1) Output contract (chuẩn để Người 4 cắm)

- Input: **1 ảnh RGB** bất kỳ (`H×W×3`, dtype bất kỳ miễn OpenCV đọc được).
- Output (duy nhất 1 format):
  - `bboxes`: `List[[x1,y1,x2,y2]]` theo **pixel trên ảnh gốc** (int)
  - `scores`: `List[float]` (0..1) cùng thứ tự với `bboxes`
  - `debug` (tuỳ chọn): chứa ảnh trung gian/overlay để báo cáo

Quy ước:
- bbox đã **clip trong biên ảnh**
- bbox quá nhỏ (< 12×12) bị loại
- đã có NMS để gộp bbox trùng

API chính cho tích hợp: xem [src/classical_detector.py](src/classical_detector.py).

## 2) Pipeline theo chương (Ch.2–Ch.4)

Nguồn chính: [src/cv_region_proposal.py](src/cv_region_proposal.py)

- **Khối A — Tiền xử lý ánh sáng/nhiễu (Ch.2)**
  - Gamma correction
  - CLAHE trên LAB (kênh L)
  - Denoise (median/gaussian)

- **Khối B — Tách màu biển báo (Ch.2 + Ch.4)**
  - HSV threshold cho: đỏ (2 dải Hue), xanh, vàng
  - Morphology: opening + closing

- **Khối C — Tìm biên/hình dạng (Ch.3)**
  - Canny edges
  - Contour + polygon approximation
  - Hough circles + Hough lines (dùng như tín hiệu hỗ trợ score)

- **Khối D — Lọc hình học + NMS (Ch.3/Ch.4)**
  - contour boundingRect
  - lọc theo area/aspect/circularity/fill
  - NMS thủ công (IoU)

## 3) Scoring (rule-based, có threshold rõ ràng)

Trong [src/cv_region_proposal.py](src/cv_region_proposal.py) mỗi bbox có:
- `score_color`: tỉ lệ pixel thuộc mask màu trong bbox
- `score_shape`: tín hiệu hình (polygon vertices + Hough circle/line)
- `score_edge`: mật độ edges trong bbox

Tổng hợp:

$$\text{score} = w_c\,\text{color} + w_s\,\text{shape} + w_e\,\text{edge}$$

Ngưỡng cuối `det_threshold` đặt ở config để Người 4 xử lý nhánh “low confidence / no detection”.

## 4) Chạy debug 1 ảnh (bắt buộc để soi lỗi nhanh)

Script: [src/run_classical_detector_debug.py](src/run_classical_detector_debug.py)

Ví dụ:

```bash
.venv/Scripts/python.exe src/run_classical_detector_debug.py --image data/detection/images/val/OIP\ (10).jpg --outdir output/classical_detector_debug/demo
```

Output thư mục sẽ có:
- preprocessed
- mask_color
- edges
- combined
- shapes overlay (contour/hough)
- final bbox overlay

## 5) Evaluate batch (IoU@0.5 + Precision/Recall/F1)

Script: [src/eval_classical_detector.py](src/eval_classical_detector.py)

```bash
.venv/Scripts/python.exe src/eval_classical_detector.py --dataset data/detection --split val --config configs/classical_detector.json --outdir output/classical_detector_eval
```

Kết quả:
- `output/classical_detector_eval/<split>/summary.json`
- `output/classical_detector_eval/<split>/per_image.json`

## 6) Hard negative mining

Script: [src/mine_hard_negatives.py](src/mine_hard_negatives.py)

```bash
.venv/Scripts/python.exe src/mine_hard_negatives.py --dataset data/detection --split val --outdir output/hard_negatives/val --config configs/classical_detector.json
```

## 7) File cấu hình

Config mặc định: [configs/classical_detector.json](configs/classical_detector.json)

Bạn có thể tune:
- gamma/CLAHE/denoise
- HSV thresholds
- morphology kernel/iters
- canny thresholds
- lọc hình học (area/aspect/circularity/fill)
- NMS IoU
- weights `w_color/w_shape/w_edge` và `det_threshold`

## 8) Ablation (cho báo cáo)

Script: [src/run_ablation_classical_detector.py](src/run_ablation_classical_detector.py)

Chạy nhanh 3–4 biến thể phổ biến:
- base
- no_clahe
- no_gamma
- no_shape

```bash
.venv/Scripts/python.exe src/run_ablation_classical_detector.py --dataset data/detection --split val --config configs/classical_detector.json --outdir output/classical_detector_eval/ablation
```

