import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from torch.utils.data import DataLoader
from preprocessing import prepare_data 
import os

def train_model():
    # 1. Load dữ liệu (Hàm prepare_data sẽ tự động nhận diện thư mục '43' mới)
    print("Đang tải dữ liệu...")
    train_ds, val_ds, _ = prepare_data('../data/Train')
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    
    # 2. Định nghĩa Model
    print("Đang khởi tạo mô hình...")
    model = models.mobilenet_v2(weights='DEFAULT')
    
    # QUAN TRỌNG: Thay đổi số lớp thành 44 (43 biển báo + 1 background)
    model.classifier[1] = nn.Linear(model.last_channel, 44) 

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    # 3. Cấu hình huấn luyện
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    num_epochs = 5 # Có thể tăng lên 10-15 nếu máy bạn chạy nhanh
    
    # 4. Vòng lặp huấn luyện
    print(f"Bắt đầu huấn luyện trên {device}...")
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad() # Xóa gradient cũ
            outputs = model(inputs) # Suy luận
            loss = criterion(outputs, labels) # Tính sai số
            loss.backward() # Lan truyền ngược
            optimizer.step() # Cập nhật trọng số
            
            running_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {running_loss/len(train_loader):.4f}")
    
    # 5. Lưu model mới
    os.makedirs('../output', exist_ok=True)
    torch.save(model.state_dict(), '../output/model.pth')
    print("Đã huấn luyện xong và lưu model mới (44 lớp) vào thư mục output/model.pth")

if __name__ == '__main__':
    train_model()