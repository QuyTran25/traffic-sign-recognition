import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from torch.utils.data import DataLoader
from preprocessing import prepare_data # Gọi hàm từ file bạn đã tạo

# 1. Load dữ liệu
train_ds, val_ds, _ = prepare_data('../data/Train')
train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)

# 2. Định nghĩa Model (MobileNetV2)
model = models.mobilenet_v2(pretrained=True)
model.classifier[1] = nn.Linear(model.last_channel, 43) # GTSRB có 43 classes

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# 3. Chạy AI suy luận
        with torch.no_grad():
            outputs = model(tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted = torch.max(probabilities, 0)
        
        class_id = predicted.item() # Đây là vị trí trong danh sách đã sắp xếp (0, 1, 10, 11...)
        
        # --- GIẢI MÃ THỨ TỰ THỰC TẾ ---
        # Lấy danh sách tên thư mục và sắp xếp theo đúng cách ImageFolder làm
        import os
        # Đường dẫn tới thư mục data/Train của bạn
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'Train')
        class_names = sorted(os.listdir(data_dir)) # Kết quả: ['0', '1', '10', '11'...]
        
        # Lấy ID thư mục thực tế từ class_id của AI
        real_folder_id = int(class_names[class_id])
        
        # 4. Lấy tên biển báo theo ID thật
        sign_name = SIGN_NAMES.get(real_folder_id, f"Biển báo số {real_folder_id}")

# 5. Lưu model
torch.save(model.state_dict(), '../output/model.pth')
print("Đã lưu model vào thư mục output/model.pth")