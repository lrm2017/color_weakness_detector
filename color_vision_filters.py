#!/usr/bin/env python3
"""
色觉辅助滤镜
提供多种滤镜来帮助色觉缺陷用户更好地识别图像内容
"""

import cv2
import numpy as np
from enum import Enum
from image_utils import imread_unicode, imwrite_unicode


class FilterType(Enum):
    """滤镜类型"""
    NONE = "none"
    PROTANOPIA_ASSIST = "protanopia_assist"      # 红色盲辅助
    DEUTERANOPIA_ASSIST = "deuteranopia_assist"  # 绿色盲辅助
    TRITANOPIA_ASSIST = "tritanopia_assist"      # 蓝色盲辅助
    HIGH_CONTRAST = "high_contrast"              # 高对比度
    EDGE_ENHANCEMENT = "edge_enhancement"        # 边缘增强
    BRIGHTNESS_BOOST = "brightness_boost"        # 亮度增强
    SATURATION_BOOST = "saturation_boost"        # 饱和度增强
    GRAYSCALE = "grayscale"                      # 灰度
    INVERTED = "inverted"                        # 反色
    WARM_COOL_HIGHLIGHT = "warm_cool_highlight"  # 暖冷色高亮
    RED_GREEN_SEPARATE = "red_green_separate"    # 红绿分离
    BLUE_YELLOW_SEPARATE = "blue_yellow_separate" # 蓝黄分离


class ColorVisionFilters:
    """色觉辅助滤镜类"""
    
    @staticmethod
    def apply_filter(image, filter_type: FilterType):
        """
        应用指定的滤镜
        
        Args:
            image: 输入图像 (BGR格式)
            filter_type: 滤镜类型
            
        Returns:
            处理后的图像
        """
        if filter_type == FilterType.NONE:
            return image.copy()
        elif filter_type == FilterType.PROTANOPIA_ASSIST:
            return ColorVisionFilters._protanopia_assist(image)
        elif filter_type == FilterType.DEUTERANOPIA_ASSIST:
            return ColorVisionFilters._deuteranopia_assist(image)
        elif filter_type == FilterType.TRITANOPIA_ASSIST:
            return ColorVisionFilters._tritanopia_assist(image)
        elif filter_type == FilterType.HIGH_CONTRAST:
            return ColorVisionFilters._high_contrast(image)
        elif filter_type == FilterType.EDGE_ENHANCEMENT:
            return ColorVisionFilters._edge_enhancement(image)
        elif filter_type == FilterType.BRIGHTNESS_BOOST:
            return ColorVisionFilters._brightness_boost(image)
        elif filter_type == FilterType.SATURATION_BOOST:
            return ColorVisionFilters._saturation_boost(image)
        elif filter_type == FilterType.GRAYSCALE:
            return ColorVisionFilters._grayscale(image)
        elif filter_type == FilterType.INVERTED:
            return ColorVisionFilters._inverted(image)
        elif filter_type == FilterType.WARM_COOL_HIGHLIGHT:
            return ColorVisionFilters._warm_cool_highlight(image)
        elif filter_type == FilterType.RED_GREEN_SEPARATE:
            return ColorVisionFilters._red_green_separate(image)
        elif filter_type == FilterType.BLUE_YELLOW_SEPARATE:
            return ColorVisionFilters._blue_yellow_separate(image)
        else:
            return image.copy()
    
    @staticmethod
    def _protanopia_assist(image):
        """红色盲辅助滤镜 - 将红色转换为更容易识别的颜色"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 创建红色掩码
        red_mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
        red_mask2 = cv2.inRange(hsv, np.array([170, 50, 50]), np.array([180, 255, 255]))
        red_mask = red_mask1 | red_mask2
        
        result = image.copy()
        
        # 将红色区域转换为蓝色（更容易被红色盲识别）
        result[red_mask > 0] = [255, 100, 0]  # 蓝色
        
        # 增强对比度
        result = cv2.convertScaleAbs(result, alpha=1.2, beta=10)
        
        return result
    
    @staticmethod
    def _deuteranopia_assist(image):
        """绿色盲辅助滤镜 - 将绿色转换为更容易识别的颜色"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 创建绿色掩码
        green_mask = cv2.inRange(hsv, np.array([40, 50, 50]), np.array([80, 255, 255]))
        
        result = image.copy()
        
        # 将绿色区域转换为紫色（更容易被绿色盲识别）
        result[green_mask > 0] = [128, 0, 128]  # 紫色
        
        # 增强对比度
        result = cv2.convertScaleAbs(result, alpha=1.2, beta=10)
        
        return result
    
    @staticmethod
    def _tritanopia_assist(image):
        """蓝色盲辅助滤镜 - 将蓝色转换为更容易识别的颜色"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 创建蓝色掩码
        blue_mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([130, 255, 255]))
        
        result = image.copy()
        
        # 将蓝色区域转换为红色（更容易被蓝色盲识别）
        result[blue_mask > 0] = [0, 0, 255]  # 红色
        
        # 增强对比度
        result = cv2.convertScaleAbs(result, alpha=1.2, beta=10)
        
        return result
    
    @staticmethod
    def _high_contrast(image):
        """高对比度滤镜"""
        # 转换为LAB色彩空间
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 应用CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # 合并通道
        lab = cv2.merge([l, a, b])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 进一步增强对比度
        result = cv2.convertScaleAbs(result, alpha=1.5, beta=0)
        
        return result
    
    @staticmethod
    def _edge_enhancement(image):
        """边缘增强滤镜"""
        # 转换为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用拉普拉斯算子检测边缘
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian = np.uint8(np.absolute(laplacian))
        
        # 将边缘信息叠加到原图
        result = image.copy()
        for i in range(3):
            result[:, :, i] = cv2.addWeighted(result[:, :, i], 0.8, laplacian, 0.2, 0)
        
        return result
    
    @staticmethod
    def _brightness_boost(image):
        """亮度增强滤镜"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # 增强亮度
        v = cv2.add(v, 30)
        v = np.clip(v, 0, 255)
        
        hsv = cv2.merge([h, s, v])
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return result
    
    @staticmethod
    def _saturation_boost(image):
        """饱和度增强滤镜"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # 增强饱和度
        s = cv2.multiply(s, 1.5)
        s = np.clip(s, 0, 255)
        
        hsv = cv2.merge([h, s, v])
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return result
    
    @staticmethod
    def _grayscale(image):
        """灰度滤镜"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return result
    
    @staticmethod
    def _inverted(image):
        """反色滤镜"""
        result = 255 - image
        return result
    
    @staticmethod
    def _warm_cool_highlight(image):
        """暖冷色高亮滤镜"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 暖色掩码 (红、橙、黄)
        warm_mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([30, 255, 255]))
        warm_mask2 = cv2.inRange(hsv, np.array([150, 50, 50]), np.array([180, 255, 255]))
        warm_mask = warm_mask1 | warm_mask2
        
        # 冷色掩码 (绿、青、蓝、紫)
        cool_mask = cv2.inRange(hsv, np.array([30, 50, 50]), np.array([150, 255, 255]))
        
        result = image.copy()
        
        # 暖色区域用红色边框标记
        contours_warm, _ = cv2.findContours(warm_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result, contours_warm, -1, (0, 0, 255), 3)
        
        # 冷色区域用蓝色边框标记
        contours_cool, _ = cv2.findContours(cool_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result, contours_cool, -1, (255, 0, 0), 3)
        
        return result
    
    @staticmethod
    def _red_green_separate(image):
        """红绿分离滤镜 - 用不同模式显示红绿色"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 红色掩码
        red_mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
        red_mask2 = cv2.inRange(hsv, np.array([170, 50, 50]), np.array([180, 255, 255]))
        red_mask = red_mask1 | red_mask2
        
        # 绿色掩码
        green_mask = cv2.inRange(hsv, np.array([40, 50, 50]), np.array([80, 255, 255]))
        
        result = image.copy()
        
        # 红色区域用条纹模式
        red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in red_contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 绘制斜条纹
            for i in range(0, w + h, 10):
                cv2.line(result, (x, y + i), (x + i, y), (0, 0, 255), 2)
        
        # 绿色区域用点状模式
        green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in green_contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 绘制点状图案
            for i in range(x, x + w, 15):
                for j in range(y, y + h, 15):
                    cv2.circle(result, (i, j), 3, (0, 255, 0), -1)
        
        return result
    
    @staticmethod
    def _blue_yellow_separate(image):
        """蓝黄分离滤镜 - 用不同模式显示蓝黄色"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 蓝色掩码
        blue_mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([130, 255, 255]))
        
        # 黄色掩码
        yellow_mask = cv2.inRange(hsv, np.array([20, 50, 50]), np.array([30, 255, 255]))
        
        result = image.copy()
        
        # 蓝色区域用方格模式
        blue_contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in blue_contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 绘制方格
            for i in range(x, x + w, 20):
                for j in range(y, y + h, 20):
                    cv2.rectangle(result, (i, j), (i + 10, j + 10), (255, 0, 0), 2)
        
        # 黄色区域用三角形模式
        yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in yellow_contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 绘制三角形
            for i in range(x, x + w, 25):
                for j in range(y, y + h, 25):
                    pts = np.array([[i, j + 15], [i + 7, j], [i + 15, j + 15]], np.int32)
                    cv2.fillPoly(result, [pts], (0, 255, 255))
        
        return result
    
    @staticmethod
    def get_filter_description(filter_type: FilterType):
        """获取滤镜描述"""
        descriptions = {
            FilterType.NONE: "无滤镜",
            FilterType.PROTANOPIA_ASSIST: "红色盲辅助 - 将红色转为蓝色",
            FilterType.DEUTERANOPIA_ASSIST: "绿色盲辅助 - 将绿色转为紫色",
            FilterType.TRITANOPIA_ASSIST: "蓝色盲辅助 - 将蓝色转为红色",
            FilterType.HIGH_CONTRAST: "高对比度 - 增强图像对比度",
            FilterType.EDGE_ENHANCEMENT: "边缘增强 - 突出图像边缘",
            FilterType.BRIGHTNESS_BOOST: "亮度增强 - 提高图像亮度",
            FilterType.SATURATION_BOOST: "饱和度增强 - 提高颜色饱和度",
            FilterType.GRAYSCALE: "灰度模式 - 转为黑白图像",
            FilterType.INVERTED: "反色模式 - 颜色反转",
            FilterType.WARM_COOL_HIGHLIGHT: "暖冷色高亮 - 用边框标记暖冷色",
            FilterType.RED_GREEN_SEPARATE: "红绿分离 - 用图案区分红绿色",
            FilterType.BLUE_YELLOW_SEPARATE: "蓝黄分离 - 用图案区分蓝黄色"
        }
        return descriptions.get(filter_type, "未知滤镜")


def main():
    """测试滤镜功能"""
    import argparse
    
    parser = argparse.ArgumentParser(description="色觉辅助滤镜测试")
    parser.add_argument("image", help="输入图像路径")
    parser.add_argument("--filter", choices=[f.value for f in FilterType], 
                        default="none", help="滤镜类型")
    parser.add_argument("--output", help="输出图像路径")
    parser.add_argument("--show", action="store_true", help="显示结果")
    
    args = parser.parse_args()
    
    # 读取图像
    image = imread_unicode(args.image)
    if image is None:
        print(f"错误：无法读取图像 {args.image}")
        return 1
    
    # 应用滤镜
    filter_type = FilterType(args.filter)
    filtered_image = ColorVisionFilters.apply_filter(image, filter_type)
    
    print(f"应用滤镜: {ColorVisionFilters.get_filter_description(filter_type)}")
    
    # 保存结果
    if args.output:
        imwrite_unicode(args.output, filtered_image)
        print(f"结果已保存到: {args.output}")
    
    # 显示结果
    if args.show:
        cv2.imshow("Original", image)
        cv2.imshow("Filtered", filtered_image)
        print("按任意键关闭窗口...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    return 0


if __name__ == "__main__":
    exit(main())