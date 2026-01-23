#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单OCR测试工具
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import cv2
        print("✓ OpenCV已安装")
    except ImportError:
        print("✗ OpenCV未安装，请运行: pip install opencv-python")
        return False
        
    try:
        import pytesseract
        print("✓ pytesseract已安装")
    except ImportError:
        print("✗ pytesseract未安装，请运行: pip install pytesseract")
        return False
        
    try:
        from PIL import Image
        print("✓ Pillow已安装")
    except ImportError:
        print("✗ Pillow未安装，请运行: pip install pillow")
        return False
    
    # 检查tesseract命令
    import subprocess
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Tesseract OCR引擎已安装")
            print(f"版本: {result.stdout.split()[1]}")
        else:
            print("✗ Tesseract OCR引擎未安装")
            return False
    except FileNotFoundError:
        print("✗ Tesseract OCR引擎未安装，请运行安装脚本")
        return False
    
    # 检查中文语言包
    try:
        result = subprocess.run(['tesseract', '--list-langs'], capture_output=True, text=True)
        if 'chi_sim' in result.stdout:
            print("✓ 中文语言包已安装")
        else:
            print("✗ 中文语言包未安装")
            return False
    except:
        print("✗ 无法检查语言包")
        return False
    
    return True

def test_ocr_on_image(image_path):
    """测试单个图像的OCR"""
    import cv2
    import pytesseract
    import numpy as np
    
    try:
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            print(f"无法读取图像: {image_path}")
            return
            
        height, width = img.shape[:2]
        print(f"图像尺寸: {width}x{height}")
        
        # 提取左下角区域 (30%区域)
        region_ratio = 0.3
        start_y = int(height * (1 - region_ratio))
        end_y = height
        start_x = 0
        end_x = int(width * region_ratio)
        
        roi = img[start_y:end_y, start_x:end_x]
        print(f"提取区域: ({start_x},{start_y}) 到 ({end_x},{end_y})")
        
        # 转换为灰度图
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 简单二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 放大图像
        scale_factor = 3
        resized = cv2.resize(binary, None, fx=scale_factor, fy=scale_factor, 
                           interpolation=cv2.INTER_CUBIC)
        
        # 保存处理后的图像用于调试
        debug_path = f"debug_{os.path.basename(image_path)}"
        cv2.imwrite(debug_path, resized)
        print(f"调试图像已保存: {debug_path}")
        
        # OCR识别
        print("正在进行OCR识别...")
        
        # 尝试中文识别
        try:
            text_chi = pytesseract.image_to_string(resized, lang='chi_sim')
            print(f"中文识别结果: '{text_chi.strip()}'")
        except Exception as e:
            print(f"中文识别失败: {e}")
            text_chi = ""
        
        # 尝试英文识别
        try:
            text_eng = pytesseract.image_to_string(resized, lang='eng')
            print(f"英文识别结果: '{text_eng.strip()}'")
        except Exception as e:
            print(f"英文识别失败: {e}")
            text_eng = ""
        
        # 选择更好的结果
        final_text = text_chi if len(text_chi.strip()) > len(text_eng.strip()) else text_eng
        print(f"最终识别结果: '{final_text.strip()}'")
        
    except Exception as e:
        print(f"OCR测试失败: {e}")

def main():
    print("=== OCR依赖检查 ===")
    if not check_dependencies():
        print("\n请先安装缺失的依赖，然后重新运行此脚本")
        print("运行安装脚本: ./install_ocr_dependencies.sh")
        return
    
    print("\n=== OCR功能测试 ===")
    
    # 测试图像路径
    test_dir = Path("downloaded_images/李春慧新编")
    if not test_dir.exists():
        print(f"测试目录不存在: {test_dir}")
        return
    
    # 找一个测试图像
    test_images = list(test_dir.glob("00[1-5].jpg"))
    if not test_images:
        print("未找到测试图像")
        return
    
    test_image = test_images[0]
    print(f"使用测试图像: {test_image}")
    
    test_ocr_on_image(str(test_image))

if __name__ == "__main__":
    main()