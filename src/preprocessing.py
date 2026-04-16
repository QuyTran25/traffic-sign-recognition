import torch
from torchvision import datasets, transforms
from torch.utils.data import random_split

def prepare_data(data_dir, batch_size=32):
    # 1. Định nghĩa công cụ xử lý ảnh (Resize và chuyển thành Tensor)
    # Tuyệt đối không còn dấu 3 chấm ở đây nữa
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # 2. Load dữ liệu từ thư mục và áp dụng transform
    full_dataset = datasets.ImageFolder(root=data_dir, transform=transform)
    
    # 3. Chia tập dữ liệu (80% để Train, 20% để Validation)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    
    train_ds, val_ds = random_split(full_dataset, [train_size, val_size])
    
    # Trả về 3 biến (biến thứ 3 để None cho khớp với train.py)
    return train_ds, val_ds, None