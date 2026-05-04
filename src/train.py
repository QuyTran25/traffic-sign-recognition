"""
Train MobileNetV2 classifier cho 43 traffic sign classes
Script hoàn chỉnh với logging, checkpointing, và evaluation
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import models, transforms, datasets
from tqdm import tqdm

# ============================================
# Configuration
# ============================================
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "Train"
OUTPUT_DIR = ROOT / "output"
MODEL_PATH = OUTPUT_DIR / "model.pth"
LOG_PATH = OUTPUT_DIR / "training_log.json"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"

NUM_CLASSES = 43
BATCH_SIZE = 32
NUM_EPOCHS = 50
LEARNING_RATE = 0.001
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============================================
# Setup
# ============================================
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# Data Loading
# ============================================
def get_data_loaders(data_dir: Path, batch_size: int = 32):
    """Load training data using ImageFolder"""
    
    # Image transformations
    train_transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.RandomRotation(15),
        transforms.RandomHorizontalFlip(p=0.3),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    # Load dataset
    full_dataset = datasets.ImageFolder(
        root=str(data_dir),
        transform=train_transform
    )
    
    # Split: 80% train, 20% val
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset,
        [train_size, val_size]
    )
    
    # Update val_dataset transform
    val_dataset.dataset.transform = val_transform
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2
    )
    
    print(f"✓ Train dataset: {train_size} images")
    print(f"✓ Val dataset: {val_size} images")
    print(f"✓ Classes: {len(full_dataset.classes)}")
    
    return train_loader, val_loader, full_dataset.classes

# ============================================
# Model
# ============================================
def create_model(num_classes: int):
    """Create MobileNetV2 model with pretrained weights"""
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    
    # Replace classifier
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, num_classes)
    
    return model

# ============================================
# Training Loop
# ============================================
def train_epoch(model, train_loader, criterion, optimizer, device):
    """Train one epoch"""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(train_loader, desc="Training")
    for images, labels in pbar:
        images = images.to(device)
        labels = labels.to(device)
        
        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Statistics
        total_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'acc': f'{correct/total:.4f}'
        })
    
    avg_loss = total_loss / len(train_loader)
    accuracy = correct / total
    return avg_loss, accuracy

def validate(model, val_loader, criterion, device):
    """Validate model"""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        pbar = tqdm(val_loader, desc="Validating")
        for images, labels in pbar:
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{correct/total:.4f}'
            })
    
    avg_loss = total_loss / len(val_loader)
    accuracy = correct / total
    return avg_loss, accuracy

# ============================================
# Main Training
# ============================================
def main(args):
    print(f"""
    ╔═══════════════════════════════════════╗
    ║  Traffic Sign Classifier Training     ║
    ╚═══════════════════════════════════════╝
    
    Device: {DEVICE}
    Batch Size: {args.batch_size}
    Learning Rate: {args.lr}
    Epochs: {args.epochs}
    """)
    
    # Check data exists
    if not DATA_DIR.exists():
        print(f"❌ Data directory not found: {DATA_DIR}")
        print(f"   Run: python prepare_classification_data.py")
        return
    
    # Load data
    print("\n📊 Loading data...")
    train_loader, val_loader, classes = get_data_loaders(
        DATA_DIR,
        batch_size=args.batch_size
    )
    
    # Create model
    print("\n🏗️ Creating model...")
    model = create_model(NUM_CLASSES)
    model = model.to(DEVICE)
    print(f"✓ Model: MobileNetV2 with {NUM_CLASSES} output classes")
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)
    
    # Training loop
    print("\n🚀 Starting training...\n")
    training_log = {
        "start_time": datetime.now().isoformat(),
        "config": {
            "batch_size": args.batch_size,
            "learning_rate": args.lr,
            "epochs": args.epochs,
            "num_classes": NUM_CLASSES
        },
        "epochs": []
    }
    
    best_val_acc = 0.0
    best_epoch = 0
    
    for epoch in range(args.epochs):
        print(f"\n{'='*50}")
        print(f"Epoch {epoch+1}/{args.epochs}")
        print(f"{'='*50}")
        
        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, DEVICE
        )
        
        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, DEVICE)
        
        # Step scheduler
        scheduler.step()
        
        # Logging
        epoch_log = {
            "epoch": epoch + 1,
            "train_loss": float(train_loss),
            "train_acc": float(train_acc),
            "val_loss": float(val_loss),
            "val_acc": float(val_acc)
        }
        training_log["epochs"].append(epoch_log)
        
        print(f"\nTrain Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
        print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")
        
        # Save checkpoint
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch + 1
            
            # Save best model
            torch.save(model.state_dict(), MODEL_PATH)
            print(f"✓ Best model saved: {MODEL_PATH}")
            
            # Save checkpoint
            checkpoint = {
                "epoch": epoch + 1,
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "val_acc": val_acc
            }
            checkpoint_path = CHECKPOINT_DIR / f"checkpoint_epoch{epoch+1}.pt"
            torch.save(checkpoint, checkpoint_path)
    
    # Final
    training_log["end_time"] = datetime.now().isoformat()
    training_log["best_epoch"] = best_epoch
    training_log["best_val_acc"] = float(best_val_acc)
    
    # Save training log
    with open(LOG_PATH, 'w') as f:
        json.dump(training_log, f, indent=2)
    
    print(f"""
    ╔═══════════════════════════════════════╗
    ║  Training Completed                   ║
    ╚═══════════════════════════════════════╝
    
    ✓ Best Epoch: {best_epoch}
    ✓ Best Val Accuracy: {best_val_acc:.4f}
    ✓ Model saved: {MODEL_PATH}
    ✓ Log saved: {LOG_PATH}
    """)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS)
    args = parser.parse_args()
    
    main(args)