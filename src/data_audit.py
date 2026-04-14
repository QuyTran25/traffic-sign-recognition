import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from tqdm import tqdm
import glob

def any_image_check(root_dir):
    print(f"Scanning directory: {root_dir}")
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    image_data = []

    # Walk through the directory recursively
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(image_extensions):
                full_path = os.path.join(root, file)
                try:
                    with Image.open(full_path) as img:
                        width, height = img.size
                        mode = img.mode
                        fmt = img.format
                        image_data.append({
                            'path': full_path,
                            'name': file,
                            'folder': os.path.basename(root),
                            'width': width,
                            'height': height,
                            'mode': mode,
                            'format': fmt,
                            'size_kb': os.path.getsize(full_path) / 1024
                        })
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")

    if not image_data:
        print("No images found!")
        return None

    df = pd.DataFrame(image_data)
    print(f"Found {len(df)} images.")
    return df

def visualize_data(df, output_dir=None):
    if output_dir is None:
        # Tự động tìm đến thư mục report ở cấp cha của thư mục src
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, 'report', 'data_audit')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Image Format Distribution
    plt.figure(figsize=(10, 6))
    df['format'].value_counts().plot(kind='pie', autopct='%1.1f%%', startangle=140)
    plt.title('Distribution of Image Formats')
    plt.ylabel('')
    plt.savefig(os.path.join(output_dir, 'format_distribution.png'))
    plt.close()

    # 2. Image Size Distribution (Width vs Height)
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=df, x='width', y='height', alpha=0.5)
    plt.title('Image Dimensions Distribution (Width vs Height)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(output_dir, 'dimensions_scatter.png'))
    plt.close()

    # 3. Histograms of Width and Height
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    sns.histplot(df['width'], bins=30, ax=axes[0], color='skyblue')
    axes[0].set_title('Distribution of Widths')
    sns.histplot(df['height'], bins=30, ax=axes[1], color='salmon')
    axes[1].set_title('Distribution of Heights')
    plt.savefig(os.path.join(output_dir, 'dimensions_hist.png'))
    plt.close()

    # 4. Collage of Random Images
    n_samples = 16
    samples = df.sample(min(n_samples, len(df)))
    
    plt.figure(figsize=(12, 12))
    for i, (idx, row) in enumerate(samples.iterrows()):
        plt.subplot(4, 4, i + 1)
        img = Image.open(row['path'])
        plt.imshow(img)
        plt.title(f"{row['width']}x{row['height']}\n{row['folder']}", fontsize=8)
        plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'image_samples.png'))
    plt.close()

    # 5. Top Folder distribution (if classes)
    plt.figure(figsize=(12, 6))
    df['folder'].value_counts().head(20).plot(kind='bar')
    plt.title('Top 20 Folders by Image Count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'folder_distribution.png'))
    plt.close()

    print(f"Reports saved to {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    # Thử tìm trong thư mục data của project trước, nếu không có thì dùng đường dẫn tuyệt đối của bạn
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_data_path = os.path.join(base_dir, 'data')
    
    if os.path.exists(project_data_path) and any(os.scandir(project_data_path)):
        dataset_path = project_data_path
    else:
        dataset_path = r'd:\xulyanh' # Đường dẫn gốc của bạn
        
    dfImages = any_image_check(dataset_path)
    
    if dfImages is not None:
        # Summary statistics
        print("\n--- Summary Statistics ---")
        print(f"Total Images: {len(dfImages)}")
        print(f"Common Formats: {dfImages['format'].unique()}")
        print(f"Unique Modes (e.g., RGB, L): {dfImages['mode'].unique()}")
        print(f"Mean Width: {dfImages['width'].mean():.2f}")
        print(f"Mean Height: {dfImages['height'].mean():.2f}")
        print(f"Max Size: {dfImages['width'].max()}x{dfImages['height'].max()}")
        print(f"Min Size: {dfImages['width'].min()}x{dfImages['height'].min()}")
        
        visualize_data(dfImages)
    else:
        print("Check if the path is correct or if images exist.")
