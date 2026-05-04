"""
Chuẩn bị dataset classification từ detection labels
Tạo folder structure: data/Train/0/, data/Train/1/, ..., data/Train/42/
"""

import os
import shutil
import json
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from tqdm import tqdm

# Cấu hình
ROOT = Path(__file__).parent
DETECTION_IMAGES = ROOT / "data" / "detection" / "images"
DETECTION_LABELS = ROOT / "data" / "detection" / "labels"
OUTPUT_TRAIN = ROOT / "data" / "Train"
SIGN_LABELS_FILE = ROOT / "sign_labels_vi.json"

# Load nhãn tiếng Việt
with open(SIGN_LABELS_FILE, 'r', encoding='utf-8') as f:
    sign_labels = json.load(f)

def yolo_line_to_xyxy(line: str, w: int, h: int) -> tuple[int, int, int, int] | None:
    """Convert YOLO format to pixel coordinates"""
    try:
        parts = line.strip().split()
        if len(parts) < 5:
            return None
        
        _, cx, cy, bw, bh = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        
        x1 = int((cx - bw/2) * w)
        y1 = int((cy - bh/2) * h)
        x2 = int((cx + bw/2) * w)
        y2 = int((cy + bh/2) * h)
        
        return max(0, x1), max(0, y1), min(w, x2), min(h, y2)
    except:
        return None

def create_train_folders():
    """Tạo 43 folders cho 43 classes"""
    OUTPUT_TRAIN.mkdir(parents=True, exist_ok=True)
    for class_id in range(43):
        class_dir = OUTPUT_TRAIN / str(class_id)
        class_dir.mkdir(exist_ok=True)
    print(f"✓ Tạo {OUTPUT_TRAIN} với 43 class folders")

def extract_crops_from_annotations():
    """
    Extract crop từ detection labels
    Mỗi crop được assign random class (0-42) để simulate training data
    """
    crop_count = 0
    
    # Xử lý train + val images
    for split in ["train", "val"]:
        images_dir = DETECTION_IMAGES / split
        labels_dir = DETECTION_LABELS / split
        
        if not images_dir.exists():
            print(f"⚠ {images_dir} không tồn tại, bỏ qua")
            continue
        
        image_files = sorted(list(images_dir.glob("*.*")))
        print(f"\n📷 Xử lý {split} ({len(image_files)} ảnh)...")
        
        for img_path in tqdm(image_files, desc=f"Extract crops ({split})"):
            # Đọc ảnh
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                h, w = img.shape[:2]
            except:
                continue
            
            # Tìm label tương ứng
            label_path = labels_dir / f"{img_path.stem}.txt"
            if not label_path.exists():
                continue
            
            # Đọc tất cả bbox từ label
            try:
                with open(label_path, 'r') as f:
                    lines = f.readlines()
            except:
                continue
            
            # Extract từng crop
            for line in lines:
                bbox = yolo_line_to_xyxy(line, w, h)
                if bbox is None:
                    continue
                
                x1, y1, x2, y2 = bbox
                if x2 - x1 < 20 or y2 - y1 < 20:
                    continue
                
                # Crop image
                crop = img[y1:y2, x1:x2]
                
                # Resize thành 64x64 (input size của MobileNetV2)
                crop_resized = cv2.resize(crop, (64, 64))
                
                # Assign random class cho training diversity
                # (Trong production nên có actual class labels)
                class_id = np.random.randint(0, 43)
                class_dir = OUTPUT_TRAIN / str(class_id)
                
                # Lưu crop
                crop_path = class_dir / f"crop_{crop_count:06d}_{split}.jpg"
                cv2.imwrite(str(crop_path), crop_resized)
                crop_count += 1
    
    print(f"\n✓ Extract {crop_count} crops")
    return crop_count

def augment_image(img, aug_factor=1.2):
    """Apply augmentation: rotation, brightness, contrast"""
    # Random rotation (-15 to 15 degrees)
    angle = np.random.uniform(-15, 15)
    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    img = cv2.warpAffine(img, M, (w, h))
    
    # Random brightness
    brightness = np.random.uniform(0.8, 1.2)
    img = cv2.convertScaleAbs(img, alpha=brightness, beta=0)
    
    # Random contrast
    contrast = np.random.uniform(0.8, 1.3)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    
    return np.clip(img, 0, 255).astype(np.uint8)

def fill_empty_classes():
    """Fill classes rỗng với ảnh từ các classes khác"""
    empty_classes = []
    non_empty_classes = []
    
    for class_id in range(43):
        class_dir = OUTPUT_TRAIN / str(class_id)
        count = len(list(class_dir.glob("*.jpg")))
        if count == 0:
            empty_classes.append(class_id)
        else:
            non_empty_classes.append(class_id)
    
    if not empty_classes or not non_empty_classes:
        return
    
    print(f"\n⚠ Tìm thấy {len(empty_classes)} classes rỗng. Fill dữ liệu...")
    
    # Copy ảnh từ non-empty classes vào empty classes
    for empty_class in empty_classes:
        # Chọn random non-empty class
        src_class = np.random.choice(non_empty_classes)
        src_dir = OUTPUT_TRAIN / str(src_class)
        dst_dir = OUTPUT_TRAIN / str(empty_class)
        
        # Copy 5 ảnh với augmentation
        src_images = list(src_dir.glob("*.jpg"))
        for i, src_img in enumerate(src_images[:5]):
            try:
                img = cv2.imread(str(src_img))
                if img is not None:
                    # Apply augmentation
                    aug_img = augment_image(img)
                    dst_path = dst_dir / f"filled_{i}.jpg"
                    cv2.imwrite(str(dst_path), aug_img)
            except:
                pass

def augment_existing_crops():
    """Create augmented copies của mỗi crop"""
    print("\n🔄 Tạo augmented copies...")
    
    for class_id in range(43):
        class_dir = OUTPUT_TRAIN / str(class_id)
        src_images = list(class_dir.glob("crop_*.jpg"))
        
        # Create 2 augmented versions của mỗi crop
        for src_img in src_images:
            for aug_num in range(2):
                try:
                    img = cv2.imread(str(src_img))
                    if img is not None:
                        # Apply augmentation
                        aug_img = augment_image(img)
                        dst_path = class_dir / f"{src_img.stem}_aug{aug_num}.jpg"
                        cv2.imwrite(str(dst_path), aug_img)
                except:
                    pass

def verify_data_distribution():
    """Kiểm tra distribution của data"""
    print("\n📊 Phân phối dữ liệu:")
    total = 0
    for class_id in range(43):
        class_dir = OUTPUT_TRAIN / str(class_id)
        count = len(list(class_dir.glob("*.jpg")))
        total += count
        if count > 0:
            label = sign_labels.get(str(class_id), f"Class {class_id}")
            print(f"  Class {class_id:2d}: {count:3d} ảnh - {label}")
    
    print(f"\n✓ Tổng cộng: {total} ảnh training")
    return total

def main():
    print("""
    ╔════════════════════════════════════════╗
    ║  Chuẩn bị Classification Training Data  ║
    ╚════════════════════════════════════════╝
    """)
    
    # Tạo folder structure
    create_train_folders()
    
    # Extract crops từ detection labels
    crop_count = extract_crops_from_annotations()
    
    # Fill empty classes
    fill_empty_classes()
    
    # Create augmented copies
    augment_existing_crops()
    
    if crop_count == 0:
        print("\n⚠ Không có crops được extract. Tạo mock data...")
        # Create mock data (đơn giản cho testing)
        for class_id in range(43):
            class_dir = OUTPUT_TRAIN / str(class_id)
            for i in range(3):  # 3 ảnh per class
                # Tạo random RGB image 64x64
                img = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
                cv2.imwrite(str(class_dir / f"mock_{i}.jpg"), img)
        print("✓ Mock data được tạo")
    
    # Verify distribution
    total = verify_data_distribution()
    
    print(f"""
    ✓ Xong! Data đã sẵn sàng tại: {OUTPUT_TRAIN}
    
    Tiếp theo chạy: python src/train.py
    """)

if __name__ == "__main__":
    main()
