#!/usr/bin/env python3
"""
遮挡图片左下角的答案区域（固定位置）
"""

import cv2
from pathlib import Path
import shutil
import argparse


def mask_answer_fixed(image_path, output_path=None):
    """
    固定位置遮挡左下角答案区域
    """
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"无法读取图片: {image_path}")
        return None
    
    h, w = image.shape[:2]
    
    # 固定遮挡左下角区域（根据实际图片调整）
    # 答案区域大约在：宽度30%，高度10%
    mask_w = int(w * 0.30)
    mask_h = int(h * 0.10)
    
    # 用白色遮挡（与背景更接近）
    cv2.rectangle(image, (0, h - mask_h), (mask_w, h), (255, 255, 255), -1)
    
    # 保存结果
    if output_path is None:
        output_path = image_path
    cv2.imwrite(str(output_path), image)
    
    return image


def process_folder(folder_path):
    """处理文件夹中的所有图片"""
    folder = Path(folder_path)
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
    
    # 获取所有图片（排除backup目录）
    images = [f for f in folder.iterdir() 
              if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not images:
        print(f"文件夹 {folder} 中没有图片")
        return
    
    print(f"找到 {len(images)} 张图片")
    
    # 检查是否有备份，如果有则从备份恢复原图再处理
    backup_dir = folder / "backup_original"
    if backup_dir.exists():
        print(f"从备份目录恢复原图: {backup_dir}")
        for img in images:
            backup_file = backup_dir / img.name
            if backup_file.exists():
                shutil.copy2(backup_file, img)
    else:
        # 创建备份
        backup_dir.mkdir(exist_ok=True)
        print(f"备份原图到: {backup_dir}")
        for img in images:
            backup_file = backup_dir / img.name
            if not backup_file.exists():
                shutil.copy2(img, backup_file)
    
    # 处理所有图片
    for i, img_path in enumerate(images, 1):
        print(f"处理 {i}/{len(images)}: {img_path.name}")
        mask_answer_fixed(img_path)
    
    print(f"\n完成! 已处理 {len(images)} 张图片")


def main():
    parser = argparse.ArgumentParser(description="固定位置遮挡图片答案")
    parser.add_argument("folder", help="图片文件夹路径")
    args = parser.parse_args()
    
    folder = Path(args.folder)
    if not folder.exists():
        print(f"文件夹不存在: {folder}")
        return 1
    
    process_folder(folder)
    return 0


if __name__ == "__main__":
    exit(main())
