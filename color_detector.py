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
    阈值基于题库图片颜色分布统计：
    - 红色：0-10 和 156-180
    - 橙色：10-20
    - 黄色：20-30 (不含黄绿色，黄绿色归入冷色)
    - S >= 25 (题库5%分位数约为23-26)
    - V >= 40 (题库5%分位数约为78-108，适当放宽)
    """
    # 红色范围1 (0-10)
    lower_red1 = np.array([0, 25, 40])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    
    # 红色范围2 (156-180)
    lower_red2 = np.array([156, 25, 40])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    
    # 橙色范围 (10-20)
    lower_orange = np.array([10, 25, 40])
    upper_orange = np.array([20, 255, 255])
    mask_orange = cv2.inRange(hsv_image, lower_orange, upper_orange)
    
    # 黄色范围 (20-30)
    lower_yellow = np.array([20, 25, 40])
    upper_yellow = np.array([30, 255, 255])
    mask_yellow = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    
    # 合并所有暖色掩码
    warm_mask = mask_red1 | mask_red2 | mask_orange | mask_yellow
    return warm_mask


def get_cool_mask(hsv_image):
    """
    获取冷色掩码（绿、青、蓝、紫）
    HSV中H值范围（基于题库统计）：
    - 黄绿+绿色：30-85 (包含黄绿色，因为题库中黄绿色属于背景冷色)
    - 青色：85-105
    - 蓝色：105-130
    - 紫色：130-156
    - S >= 25 (与暖色保持一致)
    - V >= 40 (与暖色保持一致)
    """
    # 黄绿+绿色范围 (30-85)
    lower_green = np.array([30, 25, 40])
    upper_green = np.array([85, 255, 255])
    mask_green = cv2.inRange(hsv_image, lower_green, upper_green)
    
    # 青色范围 (85-105)
    lower_cyan = np.array([85, 25, 40])
    upper_cyan = np.array([105, 255, 255])
    mask_cyan = cv2.inRange(hsv_image, lower_cyan, upper_cyan)
    
    # 蓝色范围 (105-130)
    lower_blue = np.array([105, 25, 40])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(hsv_image, lower_blue, upper_blue)
    
    # 紫色范围 (130-156)
    lower_purple = np.array([130, 25, 40])
    upper_purple = np.array([156, 255, 255])
    mask_purple = cv2.inRange(hsv_image, lower_purple, upper_purple)
    
    # 合并所有冷色掩码
    cool_mask = mask_green | mask_cyan | mask_blue | mask_purple
    return cool_mask


def find_and_draw_contours(image, mask, color, min_area=100):
    """
    在图像上找到并绘制连通组件
    
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
    
    # 查找连通组件
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    
    result = image.copy()
    count = 0
    
    # 找到最大的连通组件
    if num_labels > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]  # 跳过背景
        sorted_indices = np.argsort(areas)[::-1]  # 降序
        
        for idx in sorted_indices[:2]:  # 最大的两个
            real_idx = idx + 1
            area = stats[real_idx, cv2.CC_STAT_AREA]
            if area > min_area:
                x = stats[real_idx, cv2.CC_STAT_LEFT]
                y = stats[real_idx, cv2.CC_STAT_TOP]
                w = stats[real_idx, cv2.CC_STAT_WIDTH]
                h = stats[real_idx, cv2.CC_STAT_HEIGHT]
                
                cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
                count += 1
    
    return result, count


def is_warm(h):
    """
    判断H值是否为暖色
    """
    return (0 <= h <= 30) or (150 <= h <= 180)


def process_image(image_path, output_path=None, min_area=100):
    """
    处理图像，识别并圈出少数派颜色，使用颜色分布和动态阈值
    
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
    
    # 过滤低饱和度和低亮度的像素（背景）
    mask_colorful = cv2.inRange(hsv, np.array([0, 20, 40]), np.array([180, 255, 255]))
    colorful_pixels = hsv[mask_colorful > 0]
    
    if len(colorful_pixels) == 0:
        print("警告：未检测到明显的彩色区域")
        return image
    
    # 提取像素进行K-means聚类
    pixel_values = colorful_pixels.reshape((-1, 3))
    pixel_values = np.float32(pixel_values)
    
    # K-means参数
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    k = 15  # 增加聚类数量
    _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = centers.astype(np.uint8)  # 确保是uint8
    
    # 计算每个簇的像素数
    unique, counts = np.unique(labels, return_counts=True)
    cluster_counts = dict(zip(unique, counts))
    
    # 分类簇为暖色或冷色
    warm_clusters = []
    cool_clusters = []
    for i, center in enumerate(centers):
        h, s, v = center
        count = cluster_counts[i]
        if is_warm(h):
            warm_clusters.append((i, count, center))
        else:
            cool_clusters.append((i, count, center))
    
    # 计算总暖色和冷色像素
    total_warm = sum(count for _, count, _ in warm_clusters)
    total_cool = sum(count for _, count, _ in cool_clusters)
    
    total_colored = total_warm + total_cool
    if total_colored == 0:
        print("警告：未检测到明显的暖色或冷色区域")
        return image
    
    warm_ratio = total_warm / total_colored * 100
    cool_ratio = total_cool / total_colored * 100
    
    print(f"暖色簇数量: {len(warm_clusters)}, 冷色簇数量: {len(cool_clusters)}")
    for i, (idx, count, center) in enumerate(warm_clusters):
        print(f"暖色簇{i}: 像素数{count}, HSV{center}")
    for i, (idx, count, center) in enumerate(cool_clusters):
        print(f"冷色簇{i}: 像素数{count}, HSV{center}")
    
    # 根据背景色调决定圈出哪种颜色
    if total_cool > total_warm:
        # 背景冷色调，圈出暖色中数量较多的色块
        if warm_clusters:
            # 找出暖色簇中像素数最多的两个
            sorted_warm = sorted(warm_clusters, key=lambda x: x[1], reverse=True)
            target_clusters = sorted_warm[:2]
            print("背景冷色调，圈出暖色中数量较多的色块（用红色框标记）")
            label = "Warm colors marked (cool background)"
            color = (0, 0, 255)  # 红色
        else:
            print("未检测到暖色簇")
            return image
    else:
        # 背景暖色调，圈出冷色中数量较多的色块
        if cool_clusters:
            # 找出冷色簇中像素数最多的两个
            sorted_cool = sorted(cool_clusters, key=lambda x: x[1], reverse=True)
            target_clusters = sorted_cool[:2]
            print("背景暖色调，圈出冷色中数量较多的色块（用蓝色框标记）")
            label = "Cool colors marked (warm background)"
            color = (255, 0, 0)  # 蓝色
        else:
            print("未检测到冷色簇")
            return image
    
    # 创建所有目标簇的联合掩码
    combined_mask = np.zeros_like(hsv[:, :, 0], dtype=np.uint8)
    for cluster_idx, _, center in target_clusters:
        h_center = int(center[0])
        s_center = int(center[1])
        v_center = int(center[2])
        h_range = 10
        s_range = 30
        v_range = 30
        
        lower = np.array([
            max(0, h_center - h_range),
            max(0, s_center - s_range),
            max(0, v_center - v_range)
        ], dtype=np.uint8)
        upper = np.array([
            min(180, h_center + h_range),
            min(255, s_center + s_range),
            min(255, v_center + v_range)
        ], dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower, upper)
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    
    # 绘制轮廓
    result, count = find_and_draw_contours(image, combined_mask, color, min_area)
    
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
