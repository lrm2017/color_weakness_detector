#!/usr/bin/env python3
"""
图像处理工具函数
解决中文路径问题和其他常见图像处理需求
"""

import cv2
import numpy as np
from pathlib import Path


def imread_unicode(image_path, flags=cv2.IMREAD_COLOR):
    """
    支持中文路径的图像读取函数
    
    Args:
        image_path: 图像路径（支持中文）
        flags: 读取标志，默认为彩色图像
        
    Returns:
        numpy.ndarray: 图像数组，如果读取失败返回None
    """
    try:
        # 转换为Path对象
        path = Path(image_path)
        
        # 使用numpy读取文件字节
        with open(path, 'rb') as f:
            image_bytes = f.read()
        
        # 转换为numpy数组
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        
        # 使用cv2.imdecode解码图像
        image = cv2.imdecode(image_array, flags)
        
        return image
        
    except Exception as e:
        print(f"读取图像失败 {image_path}: {e}")
        return None


def imwrite_unicode(image_path, image, params=None):
    """
    支持中文路径的图像保存函数
    
    Args:
        image_path: 保存路径（支持中文）
        image: 图像数组
        params: 编码参数
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 转换为Path对象
        path = Path(image_path)
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 获取文件扩展名
        ext = path.suffix.lower()
        
        # 编码图像
        success, encoded_image = cv2.imencode(ext, image, params)
        
        if success:
            # 写入文件
            with open(path, 'wb') as f:
                f.write(encoded_image.tobytes())
            return True
        else:
            print(f"图像编码失败: {image_path}")
            return False
            
    except Exception as e:
        print(f"保存图像失败 {image_path}: {e}")
        return False


def get_image_info(image_path):
    """
    获取图像信息
    
    Args:
        image_path: 图像路径
        
    Returns:
        dict: 图像信息字典
    """
    image = imread_unicode(image_path)
    
    if image is None:
        return None
    
    height, width = image.shape[:2]
    channels = image.shape[2] if len(image.shape) == 3 else 1
    
    return {
        'path': str(image_path),
        'width': width,
        'height': height,
        'channels': channels,
        'size': (width, height),
        'dtype': str(image.dtype)
    }


def resize_image_keep_ratio(image, target_size, fill_color=(0, 0, 0)):
    """
    按比例缩放图像，保持宽高比
    
    Args:
        image: 输入图像
        target_size: 目标尺寸 (width, height)
        fill_color: 填充颜色
        
    Returns:
        numpy.ndarray: 缩放后的图像
    """
    target_w, target_h = target_size
    h, w = image.shape[:2]
    
    # 计算缩放比例
    scale = min(target_w / w, target_h / h)
    
    # 计算新尺寸
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # 缩放图像
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # 创建目标尺寸的画布
    if len(image.shape) == 3:
        canvas = np.full((target_h, target_w, image.shape[2]), fill_color, dtype=image.dtype)
    else:
        canvas = np.full((target_h, target_w), fill_color[0], dtype=image.dtype)
    
    # 计算居中位置
    y_offset = (target_h - new_h) // 2
    x_offset = (target_w - new_w) // 2
    
    # 将缩放后的图像放到画布中心
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
    
    return canvas


def test_unicode_path():
    """
    测试中文路径读取功能
    """
    print("测试中文路径图像读取功能...")
    
    # 查找测试图像
    test_paths = [
        "downloaded_images/俞自萍第五版/001.jpg",
        "downloaded_images/俞自萍第六版/001.jpg",
        "downloaded_images/石原忍版/001.jpg"
    ]
    
    for path in test_paths:
        if Path(path).exists():
            print(f"\n测试路径: {path}")
            
            # 使用新方法读取
            image = imread_unicode(path)
            if image is not None:
                print(f"  ✓ 成功读取，尺寸: {image.shape}")
                
                # 获取图像信息
                info = get_image_info(path)
                if info:
                    print(f"  ✓ 图像信息: {info['width']}x{info['height']}, {info['channels']}通道")
                
                # 测试保存
                test_output = Path("test_results/unicode_test.jpg")
                if imwrite_unicode(test_output, image):
                    print(f"  ✓ 成功保存到: {test_output}")
                else:
                    print(f"  ✗ 保存失败")
            else:
                print(f"  ✗ 读取失败")
            break
    else:
        print("未找到测试图像")


if __name__ == "__main__":
    test_unicode_path()