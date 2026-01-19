#!/usr/bin/env python3
"""
色弱图谱识别程序
功能：识别图片中的暖色和冷色块，圈出少数派颜色
暖色：红、橙、黄
冷色：蓝、绿、紫、青
"""

import cv2
import numpy as np
import argparse
from pathlib import Path


def get_warm_mask(hsv_image):
    """
    获取暖色掩码（红、橙、黄）
    HSV中H值范围：0-180（OpenCV）
    - 红色：0-10 和 160-180
    - 橙色：10-25
    - 黄色：25-40
    """
    # 红色范围1 (0-10)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    
    # 红色范围2 (160-180)
    lower_red2 = np.array([160, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    
    # 橙色范围 (10-25)
    lower_orange = np.array([10, 70, 50])
    upper_orange = np.array([25, 255, 255])
    mask_orange = cv2.inRange(hsv_image, lower_orange, upper_orange)
    
    # 黄色范围 (25-40)
    lower_yellow = np.array([25, 70, 50])
    upper_yellow = np.array([40, 255, 255])
    mask_yellow = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    
    # 合并所有暖色掩码
    warm_mask = mask_red1 | mask_red2 | mask_orange | mask_yellow
    return warm_mask


def get_cool_mask(hsv_image):
    """
    获取冷色掩码（绿、青、蓝、紫）
    HSV中H值范围：
    - 绿色：40-80
    - 青色：80-100
    - 蓝色：100-130
    - 紫色：130-160
    """
    # 绿色范围 (40-80)
    lower_green = np.array([40, 70, 50])
    upper_green = np.array([80, 255, 255])
    mask_green = cv2.inRange(hsv_image, lower_green, upper_green)
    
    # 青色范围 (80-100)
    lower_cyan = np.array([80, 70, 50])
    upper_cyan = np.array([100, 255, 255])
    mask_cyan = cv2.inRange(hsv_image, lower_cyan, upper_cyan)
    
    # 蓝色范围 (100-130)
    lower_blue = np.array([100, 70, 50])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(hsv_image, lower_blue, upper_blue)
    
    # 紫色范围 (130-160)
    lower_purple = np.array([130, 70, 50])
    upper_purple = np.array([160, 255, 255])
    mask_purple = cv2.inRange(hsv_image, lower_purple, upper_purple)
    
    # 合并所有冷色掩码
    cool_mask = mask_green | mask_cyan | mask_blue | mask_purple
    return cool_mask


def find_and_draw_contours(image, mask, color, min_area=100):
    """
    在图像上找到并绘制轮廓
    
    Args:
        image: 原始图像
        mask: 颜色掩码
        color: 绘制轮廓的颜色 (BGR)
        min_area: 最小区域面积，过滤噪点
    
    Returns:
        绘制了轮廓的图像
    """
    # 形态学操作，去除噪点
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    result = image.copy()
    count = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            # 绘制轮廓
            cv2.drawContours(result, [contour], -1, color, 3)
            
            # 绘制边界框
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
            count += 1
    
    return result, count


def process_image(image_path, output_path=None, min_area=100):
    """
    处理图像，识别并圈出少数派颜色
    
    Args:
        image_path: 输入图像路径
        output_path: 输出图像路径（可选）
        min_area: 最小区域面积
    
    Returns:
        处理后的图像
    """
    # 读取图像
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")
    
    # 转换为HSV色彩空间
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 获取暖色和冷色掩码
    warm_mask = get_warm_mask(hsv)
    cool_mask = get_cool_mask(hsv)
    
    # 计算暖色和冷色像素数量
    warm_pixels = cv2.countNonZero(warm_mask)
    cool_pixels = cv2.countNonZero(cool_mask)
    
    total_colored = warm_pixels + cool_pixels
    if total_colored == 0:
        print("警告：未检测到明显的暖色或冷色区域")
        return image
    
    warm_ratio = warm_pixels / total_colored * 100
    cool_ratio = cool_pixels / total_colored * 100
    
    print(f"暖色像素: {warm_pixels} ({warm_ratio:.1f}%)")
    print(f"冷色像素: {cool_pixels} ({cool_ratio:.1f}%)")
    
    # 根据比例决定圈出哪种颜色
    if warm_pixels > cool_pixels:
        print("暖色居多，圈出冷色块（用蓝色框标记）")
        result, count = find_and_draw_contours(image, cool_mask, (255, 0, 0), min_area)
        label = "Cool colors marked (warm dominant)"
    else:
        print("冷色居多，圈出暖色块（用红色框标记）")
        result, count = find_and_draw_contours(image, warm_mask, (0, 0, 255), min_area)
        label = "Warm colors marked (cool dominant)"
    
    print(f"检测到 {count} 个色块")
    
    # 添加标签
    cv2.putText(result, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(result, f"Warm: {warm_ratio:.1f}% | Cool: {cool_ratio:.1f}%", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    # 保存结果
    if output_path:
        cv2.imwrite(str(output_path), result)
        print(f"结果已保存到: {output_path}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="色弱图谱识别程序")
    parser.add_argument("image", help="输入图像路径")
    parser.add_argument("-o", "--output", help="输出图像路径（默认为原文件名_result）")
    parser.add_argument("--min-area", type=int, default=100, 
                        help="最小色块面积（像素），默认100")
    parser.add_argument("--show", action="store_true", help="显示结果窗口")
    
    args = parser.parse_args()
    
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"错误：文件不存在: {image_path}")
        return 1
    
    # 生成输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = image_path.parent / f"{image_path.stem}_result{image_path.suffix}"
    
    try:
        result = process_image(image_path, output_path, args.min_area)
        
        if args.show:
            cv2.imshow("Color Detection Result", result)
            print("按任意键关闭窗口...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        return 0
    except Exception as e:
        print(f"错误：{e}")
        return 1


if __name__ == "__main__":
    exit(main())
