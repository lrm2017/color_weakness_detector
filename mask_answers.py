#!/usr/bin/env python3
"""
使用OCR识别并遮挡图片左下角的答案区域
"""

import cv2
import numpy as np
import easyocr
from pathlib import Path
import argparse


def mask_answer_with_ocr(image_path, reader, output_path=None, padding=5):
    """
    使用OCR识别左下角文字并遮挡
    
    Args:
        image_path: 输入图片路径
        reader: easyocr Reader实例
        output_path: 输出路径（默认覆盖原图）
        padding: 遮挡区域的额外边距
    
    Returns:
        (处理后的图片, 识别到的文字)
    """
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"无法读取图片: {image_path}")
        return None, None
    
    h, w = image.shape[:2]
    
    # 只检测左下角区域（左1/3，下1/4）
    roi_w = int(w * 0.35)
    roi_h = int(h * 0.25)
    roi = image[h - roi_h:h, 0:roi_w]
    
    # OCR识别
    results = reader.readtext(roi)
    
    detected_text = ""
    
    if results:
        # 遮挡所有识别到的文字区域
        for (bbox, text, confidence) in results:
            if confidence > 0.3:  # 置信度阈值
                detected_text = text
                
                # bbox是四个角点坐标
                pts = np.array(bbox, dtype=np.int32)
                
                # 转换到原图坐标（加上ROI的偏移）
                pts[:, 1] += (h - roi_h)
                
                # 计算边界框并添加padding
                x_min = max(0, pts[:, 0].min() - padding)
                x_max = min(w, pts[:, 0].max() + padding)
                y_min = max(0, pts[:, 1].min() - padding)
                y_max = min(h, pts[:, 1].max() + padding)
                
                # 用灰色遮挡
                cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (128, 128, 128), -1)
    
    # 保存结果
    if output_path is None:
        output_path = image_path
    cv2.imwrite(str(output_path), image)
    
    return image, detected_text


def process_folder(folder_path, backup=True):
    """
    处理文件夹中的所有图片
    
    Args:
        folder_path: 图片文件夹路径
        backup: 是否备份原图
    """
    folder = Path(folder_path)
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
    
    # 获取所有图片
    images = [f for f in folder.iterdir() 
              if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not images:
        print(f"文件夹 {folder} 中没有图片")
        return
    
    print(f"找到 {len(images)} 张图片")
    
    # 创建备份文件夹
    if backup:
        backup_dir = folder / "backup_original"
        backup_dir.mkdir(exist_ok=True)
        print(f"原图将备份到: {backup_dir}")
    
    # 初始化OCR（只初始化一次，提高效率）
    print("正在加载OCR模型...")
    reader = easyocr.Reader(['en', 'ch_sim'], gpu=False, verbose=False)
    print("OCR模型加载完成")
    
    success_count = 0
    
    for i, img_path in enumerate(images, 1):
        print(f"处理 {i}/{len(images)}: {img_path.name}", end=" ")
        
        # 备份原图
        if backup:
            backup_path = backup_dir / img_path.name
            if not backup_path.exists():
                import shutil
                shutil.copy2(img_path, backup_path)
        
        # 处理图片
        result, text = mask_answer_with_ocr(img_path, reader)
        
        if result is not None:
            if text:
                print(f"-> 识别到: {text}")
            else:
                print("-> 未识别到文字")
            success_count += 1
        else:
            print("-> 处理失败")
    
    print(f"\n完成! 成功处理 {success_count}/{len(images)} 张图片")


def main():
    parser = argparse.ArgumentParser(description="OCR识别并遮挡图片答案")
    parser.add_argument("folder", help="图片文件夹路径")
    parser.add_argument("--no-backup", action="store_true", help="不备份原图")
    
    args = parser.parse_args()
    
    folder = Path(args.folder)
    if not folder.exists():
        print(f"文件夹不存在: {folder}")
        return 1
    
    process_folder(folder, backup=not args.no_backup)
    return 0


if __name__ == "__main__":
    exit(main())
