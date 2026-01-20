#!/usr/bin/env python3
"""
多通道色弱图谱识别程序
功能：分别测试红绿、蓝黄色觉通道，提供更精确的色觉缺陷诊断
支持：
1. 红绿通道测试 (Protan/Deutan deficiency)
2. 蓝黄通道测试 (Tritan deficiency) 
3. 综合色觉评估
4. 混淆线分析
"""

import cv2
import numpy as np
import argparse
from pathlib import Path
from enum import Enum
import json
from datetime import datetime
from image_utils import imread_unicode, imwrite_unicode


class ColorChannel(Enum):
    """色觉通道枚举"""
    RED_GREEN = "red_green"
    BLUE_YELLOW = "blue_yellow"
    COMPREHENSIVE = "comprehensive"


class ColorDeficiencyType(Enum):
    """色觉缺陷类型"""
    NORMAL = "normal"
    PROTANOMALY = "protanomaly"      # 红色弱
    PROTANOPIA = "protanopia"        # 红色盲
    DEUTERANOMALY = "deuteranomaly"  # 绿色弱
    DEUTERANOPIA = "deuteranopia"    # 绿色盲
    TRITANOMALY = "tritanomaly"      # 蓝色弱
    TRITANOPIA = "tritanopia"        # 蓝色盲


class MultiChannelColorDetector:
    """多通道色觉检测器"""
    
    def __init__(self):
        # 色觉混淆线定义 (基于CIE色彩空间)
        self.confusion_lines = {
            'protan': {'slope': 0.747, 'intercept': 0.253},    # 红色盲混淆线
            'deutan': {'slope': 1.4, 'intercept': -0.4},       # 绿色盲混淆线
            'tritan': {'slope': -2.02, 'intercept': 2.52}      # 蓝色盲混淆线
        }
        
        # 色彩通道HSV范围定义
        self.color_ranges = {
            'red': [(0, 10), (156, 180)],      # 红色 (两个范围)
            'orange': [(10, 25)],              # 橙色
            'yellow': [(25, 35)],              # 黄色
            'yellow_green': [(35, 50)],        # 黄绿色
            'green': [(50, 85)],               # 绿色
            'cyan': [(85, 105)],               # 青色
            'blue': [(105, 130)],              # 蓝色
            'purple': [(130, 156)]             # 紫色
        }
    
    def get_red_green_channel_mask(self, hsv_image, sensitivity=25):
        """
        获取红绿通道掩码
        主要检测红色和绿色区域，用于Protan/Deutan缺陷检测
        """
        # 红色掩码
        red_mask = np.zeros_like(hsv_image[:, :, 0])
        for h_range in self.color_ranges['red']:
            lower = np.array([h_range[0], sensitivity, 40])
            upper = np.array([h_range[1], 255, 255])
            mask = cv2.inRange(hsv_image, lower, upper)
            red_mask = cv2.bitwise_or(red_mask, mask)
        
        # 绿色掩码
        green_mask = np.zeros_like(hsv_image[:, :, 0])
        for color in ['yellow_green', 'green']:
            for h_range in self.color_ranges[color]:
                lower = np.array([h_range[0], sensitivity, 40])
                upper = np.array([h_range[1], 255, 255])
                mask = cv2.inRange(hsv_image, lower, upper)
                green_mask = cv2.bitwise_or(green_mask, mask)
        
        return red_mask, green_mask
    
    def get_blue_yellow_channel_mask(self, hsv_image, sensitivity=25):
        """
        获取蓝黄通道掩码
        主要检测蓝色和黄色区域，用于Tritan缺陷检测
        """
        # 蓝色掩码
        blue_mask = np.zeros_like(hsv_image[:, :, 0])
        for color in ['cyan', 'blue', 'purple']:
            for h_range in self.color_ranges[color]:
                lower = np.array([h_range[0], sensitivity, 40])
                upper = np.array([h_range[1], 255, 255])
                mask = cv2.inRange(hsv_image, lower, upper)
                blue_mask = cv2.bitwise_or(blue_mask, mask)
        
        # 黄色掩码
        yellow_mask = np.zeros_like(hsv_image[:, :, 0])
        for color in ['orange', 'yellow']:
            for h_range in self.color_ranges[color]:
                lower = np.array([h_range[0], sensitivity, 40])
                upper = np.array([h_range[1], 255, 255])
                mask = cv2.inRange(hsv_image, lower, upper)
                yellow_mask = cv2.bitwise_or(yellow_mask, mask)
        
        return blue_mask, yellow_mask
    
    def analyze_color_distribution(self, hsv_image):
        """
        分析图像中的颜色分布
        返回各颜色通道的像素统计
        """
        # 过滤低饱和度像素
        mask_colorful = cv2.inRange(hsv_image, np.array([0, 20, 40]), np.array([180, 255, 255]))
        
        color_stats = {}
        total_pixels = np.sum(mask_colorful > 0)
        
        if total_pixels == 0:
            return color_stats
        
        # 统计各颜色的像素数
        for color_name, ranges in self.color_ranges.items():
            color_mask = np.zeros_like(hsv_image[:, :, 0])
            for h_range in ranges:
                lower = np.array([h_range[0], 25, 40])
                upper = np.array([h_range[1], 255, 255])
                mask = cv2.inRange(hsv_image, lower, upper)
                color_mask = cv2.bitwise_or(color_mask, mask)
            
            # 只计算有颜色的区域
            color_pixels = np.sum(cv2.bitwise_and(color_mask, mask_colorful) > 0)
            color_stats[color_name] = {
                'pixels': color_pixels,
                'percentage': (color_pixels / total_pixels) * 100 if total_pixels > 0 else 0
            }
        
        return color_stats
    
    def detect_confusion_patterns(self, color_stats):
        """
        基于颜色分布检测混淆模式
        """
        # 红绿通道分析
        red_total = color_stats.get('red', {}).get('pixels', 0) + \
                   color_stats.get('orange', {}).get('pixels', 0)
        green_total = color_stats.get('green', {}).get('pixels', 0) + \
                     color_stats.get('yellow_green', {}).get('pixels', 0)
        
        # 蓝黄通道分析
        blue_total = color_stats.get('blue', {}).get('pixels', 0) + \
                    color_stats.get('cyan', {}).get('pixels', 0) + \
                    color_stats.get('purple', {}).get('pixels', 0)
        yellow_total = color_stats.get('yellow', {}).get('pixels', 0)
        
        # 计算通道比例
        rg_total = red_total + green_total
        by_total = blue_total + yellow_total
        
        results = {
            'red_green_ratio': red_total / rg_total if rg_total > 0 else 0,
            'blue_yellow_ratio': blue_total / by_total if by_total > 0 else 0,
            'dominant_channel': None,
            'minority_colors': []
        }
        
        # 确定主导通道和少数派颜色
        if rg_total > by_total:
            results['dominant_channel'] = 'red_green'
            if red_total < green_total * 0.3:  # 红色明显少于绿色
                results['minority_colors'].append('red')
            elif green_total < red_total * 0.3:  # 绿色明显少于红色
                results['minority_colors'].append('green')
        else:
            results['dominant_channel'] = 'blue_yellow'
            if blue_total < yellow_total * 0.3:  # 蓝色明显少于黄色
                results['minority_colors'].append('blue')
            elif yellow_total < blue_total * 0.3:  # 黄色明显少于蓝色
                results['minority_colors'].append('yellow')
        
        return results
    
    def find_and_mark_regions(self, image, mask, color, label, min_area=100):
        """
        找到并标记颜色区域
        """
        # 形态学操作去噪
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找连通组件
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        
        result = image.copy()
        regions_found = 0
        
        if num_labels > 1:
            # 按面积排序
            areas = stats[1:, cv2.CC_STAT_AREA]
            sorted_indices = np.argsort(areas)[::-1]
            
            for idx in sorted_indices[:3]:  # 最大的3个区域
                real_idx = idx + 1
                area = stats[real_idx, cv2.CC_STAT_AREA]
                
                if area > min_area:
                    x = stats[real_idx, cv2.CC_STAT_LEFT]
                    y = stats[real_idx, cv2.CC_STAT_TOP]
                    w = stats[real_idx, cv2.CC_STAT_WIDTH]
                    h = stats[real_idx, cv2.CC_STAT_HEIGHT]
                    
                    # 绘制矩形框
                    cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
                    
                    # 添加标签
                    cv2.putText(result, f"{label}_{regions_found+1}", 
                              (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    
                    regions_found += 1
        
        return result, regions_found
    
    def test_red_green_channel(self, image_path, output_path=None, min_area=100):
        """
        红绿通道测试
        """
        print("\n=== 红绿通道测试 ===")
        
        # 读取图像
        image = imread_unicode(str(image_path))
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 获取红绿通道掩码
        red_mask, green_mask = self.get_red_green_channel_mask(hsv)
        
        # 计算像素统计
        red_pixels = np.sum(red_mask > 0)
        green_pixels = np.sum(green_mask > 0)
        total_rg = red_pixels + green_pixels
        
        print(f"红色像素: {red_pixels} ({red_pixels/total_rg*100:.1f}%)" if total_rg > 0 else "红色像素: 0")
        print(f"绿色像素: {green_pixels} ({green_pixels/total_rg*100:.1f}%)" if total_rg > 0 else "绿色像素: 0")
        
        # 标记区域
        result = image.copy()
        
        # 标记红色区域
        result, red_count = self.find_and_mark_regions(result, red_mask, (0, 0, 255), "RED", min_area)
        
        # 标记绿色区域  
        result, green_count = self.find_and_mark_regions(result, green_mask, (0, 255, 0), "GREEN", min_area)
        
        # 添加测试信息
        cv2.putText(result, "Red-Green Channel Test", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(result, f"Red regions: {red_count} | Green regions: {green_count}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        if total_rg > 0:
            cv2.putText(result, f"Red: {red_pixels/total_rg*100:.1f}% | Green: {green_pixels/total_rg*100:.1f}%", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 保存结果
        if output_path:
            # 确保输出路径有正确的扩展名
            if not output_path.suffix:
                rg_output = output_path.parent / f"{output_path.name}_red_green.jpg"
            else:
                rg_output = output_path.parent / f"{output_path.stem}_red_green{output_path.suffix}"
            imwrite_unicode(str(rg_output), result)
            print(f"红绿通道测试结果已保存到: {rg_output}")
        
        return result, {
            'red_pixels': red_pixels,
            'green_pixels': green_pixels,
            'red_regions': red_count,
            'green_regions': green_count,
            'red_ratio': red_pixels/total_rg if total_rg > 0 else 0,
            'green_ratio': green_pixels/total_rg if total_rg > 0 else 0
        }
    
    def test_blue_yellow_channel(self, image_path, output_path=None, min_area=100):
        """
        蓝黄通道测试
        """
        print("\n=== 蓝黄通道测试 ===")
        
        # 读取图像
        image = imread_unicode(str(image_path))
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 获取蓝黄通道掩码
        blue_mask, yellow_mask = self.get_blue_yellow_channel_mask(hsv)
        
        # 计算像素统计
        blue_pixels = np.sum(blue_mask > 0)
        yellow_pixels = np.sum(yellow_mask > 0)
        total_by = blue_pixels + yellow_pixels
        
        print(f"蓝色像素: {blue_pixels} ({blue_pixels/total_by*100:.1f}%)" if total_by > 0 else "蓝色像素: 0")
        print(f"黄色像素: {yellow_pixels} ({yellow_pixels/total_by*100:.1f}%)" if total_by > 0 else "黄色像素: 0")
        
        # 标记区域
        result = image.copy()
        
        # 标记蓝色区域
        result, blue_count = self.find_and_mark_regions(result, blue_mask, (255, 0, 0), "BLUE", min_area)
        
        # 标记黄色区域
        result, yellow_count = self.find_and_mark_regions(result, yellow_mask, (0, 255, 255), "YELLOW", min_area)
        
        # 添加测试信息
        cv2.putText(result, "Blue-Yellow Channel Test", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(result, f"Blue regions: {blue_count} | Yellow regions: {yellow_count}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        if total_by > 0:
            cv2.putText(result, f"Blue: {blue_pixels/total_by*100:.1f}% | Yellow: {yellow_pixels/total_by*100:.1f}%", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 保存结果
        if output_path:
            # 确保输出路径有正确的扩展名
            if not output_path.suffix:
                by_output = output_path.parent / f"{output_path.name}_blue_yellow.jpg"
            else:
                by_output = output_path.parent / f"{output_path.stem}_blue_yellow{output_path.suffix}"
            imwrite_unicode(str(by_output), result)
            print(f"蓝黄通道测试结果已保存到: {by_output}")
        
        return result, {
            'blue_pixels': blue_pixels,
            'yellow_pixels': yellow_pixels,
            'blue_regions': blue_count,
            'yellow_regions': yellow_count,
            'blue_ratio': blue_pixels/total_by if total_by > 0 else 0,
            'yellow_ratio': yellow_pixels/total_by if total_by > 0 else 0
        }
    
    def comprehensive_test(self, image_path, output_path=None, min_area=100):
        """
        综合色觉测试
        """
        print("\n=== 综合色觉测试 ===")
        
        # 读取图像
        image = imread_unicode(str(image_path))
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 分析颜色分布
        color_stats = self.analyze_color_distribution(hsv)
        
        # 检测混淆模式
        confusion_analysis = self.detect_confusion_patterns(color_stats)
        
        # 创建综合结果图像
        result = image.copy()
        
        # 根据分析结果标记少数派颜色
        y_offset = 30
        cv2.putText(result, "Comprehensive Color Vision Test", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        y_offset += 30
        
        # 显示颜色统计
        for color_name, stats in color_stats.items():
            if stats['percentage'] > 1.0:  # 只显示占比超过1%的颜色
                cv2.putText(result, f"{color_name}: {stats['percentage']:.1f}%", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 20
        
        # 显示主导通道
        cv2.putText(result, f"Dominant: {confusion_analysis['dominant_channel']}", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y_offset += 25
        
        # 显示少数派颜色
        if confusion_analysis['minority_colors']:
            minority_text = "Minority: " + ", ".join(confusion_analysis['minority_colors'])
            cv2.putText(result, minority_text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # 标记少数派颜色区域
        for minority_color in confusion_analysis['minority_colors']:
            if minority_color in ['red', 'orange']:
                red_mask, _ = self.get_red_green_channel_mask(hsv)
                result, _ = self.find_and_mark_regions(result, red_mask, (0, 0, 255), "MINORITY", min_area)
            elif minority_color in ['green', 'yellow_green']:
                _, green_mask = self.get_red_green_channel_mask(hsv)
                result, _ = self.find_and_mark_regions(result, green_mask, (0, 255, 0), "MINORITY", min_area)
            elif minority_color in ['blue', 'cyan', 'purple']:
                blue_mask, _ = self.get_blue_yellow_channel_mask(hsv)
                result, _ = self.find_and_mark_regions(result, blue_mask, (255, 0, 0), "MINORITY", min_area)
            elif minority_color == 'yellow':
                _, yellow_mask = self.get_blue_yellow_channel_mask(hsv)
                result, _ = self.find_and_mark_regions(result, yellow_mask, (0, 255, 255), "MINORITY", min_area)
        
        # 保存结果
        if output_path:
            # 确保输出路径有正确的扩展名
            if not output_path.suffix:
                comp_output = output_path.parent / f"{output_path.name}_comprehensive.jpg"
            else:
                comp_output = output_path.parent / f"{output_path.stem}_comprehensive{output_path.suffix}"
            imwrite_unicode(str(comp_output), result)
            print(f"综合测试结果已保存到: {comp_output}")
        
        return result, {
            'color_stats': color_stats,
            'confusion_analysis': confusion_analysis
        }
    
    def generate_report(self, image_path, rg_results, by_results, comp_results):
        """
        生成测试报告
        """
        # 转换numpy类型为Python原生类型
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'image_path': str(image_path),
            'red_green_channel': convert_numpy_types(rg_results),
            'blue_yellow_channel': convert_numpy_types(by_results),
            'comprehensive_analysis': convert_numpy_types(comp_results),
            'diagnosis': self.diagnose_color_vision(rg_results, by_results, comp_results)
        }
        
        return report
    
    def diagnose_color_vision(self, rg_results, by_results, comp_results):
        """
        基于测试结果诊断色觉类型
        """
        diagnosis = {
            'type': ColorDeficiencyType.NORMAL.value,
            'confidence': 0.0,
            'notes': []
        }
        
        # 红绿通道分析
        rg_ratio = rg_results.get('red_ratio', 0)
        
        if rg_ratio < 0.2:  # 红色严重不足
            if rg_results.get('red_regions', 0) == 0:
                diagnosis['type'] = ColorDeficiencyType.PROTANOPIA.value
                diagnosis['confidence'] = 0.8
                diagnosis['notes'].append("红色区域完全缺失，疑似红色盲")
            else:
                diagnosis['type'] = ColorDeficiencyType.PROTANOMALY.value
                diagnosis['confidence'] = 0.6
                diagnosis['notes'].append("红色识别能力减弱，疑似红色弱")
        
        elif rg_ratio > 0.8:  # 绿色严重不足
            if rg_results.get('green_regions', 0) == 0:
                diagnosis['type'] = ColorDeficiencyType.DEUTERANOPIA.value
                diagnosis['confidence'] = 0.8
                diagnosis['notes'].append("绿色区域完全缺失，疑似绿色盲")
            else:
                diagnosis['type'] = ColorDeficiencyType.DEUTERANOMALY.value
                diagnosis['confidence'] = 0.6
                diagnosis['notes'].append("绿色识别能力减弱，疑似绿色弱")
        
        # 蓝黄通道分析
        by_ratio = by_results.get('blue_ratio', 0)
        
        if by_ratio < 0.2:  # 蓝色严重不足
            if by_results.get('blue_regions', 0) == 0:
                diagnosis['type'] = ColorDeficiencyType.TRITANOPIA.value
                diagnosis['confidence'] = 0.7
                diagnosis['notes'].append("蓝色区域完全缺失，疑似蓝色盲")
            else:
                diagnosis['type'] = ColorDeficiencyType.TRITANOMALY.value
                diagnosis['confidence'] = 0.5
                diagnosis['notes'].append("蓝色识别能力减弱，疑似蓝色弱")
        
        # 综合分析
        minority_colors = comp_results.get('confusion_analysis', {}).get('minority_colors', [])
        if minority_colors:
            diagnosis['notes'].append(f"检测到少数派颜色: {', '.join(minority_colors)}")
        
        return diagnosis


def main():
    parser = argparse.ArgumentParser(description="多通道色弱图谱识别程序")
    parser.add_argument("image", help="输入图像路径")
    parser.add_argument("-o", "--output", help="输出图像路径（默认为原文件名_result）")
    parser.add_argument("--channel", choices=['red_green', 'blue_yellow', 'comprehensive', 'all'], 
                        default='all', help="测试通道选择")
    parser.add_argument("--min-area", type=int, default=100, 
                        help="最小色块面积（像素），默认100")
    parser.add_argument("--show", action="store_true", help="显示结果窗口")
    parser.add_argument("--report", action="store_true", help="生成JSON测试报告")
    
    args = parser.parse_args()
    
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"错误：文件不存在: {image_path}")
        return 1
    
    # 生成输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = image_path.parent / f"{image_path.stem}_multichannel{image_path.suffix}"
    
    try:
        detector = MultiChannelColorDetector()
        
        results = {}
        
        # 执行测试
        if args.channel in ['red_green', 'all']:
            rg_result, rg_data = detector.test_red_green_channel(image_path, output_path, args.min_area)
            results['red_green'] = (rg_result, rg_data)
            
            if args.show:
                cv2.imshow("Red-Green Channel Test", rg_result)
        
        if args.channel in ['blue_yellow', 'all']:
            by_result, by_data = detector.test_blue_yellow_channel(image_path, output_path, args.min_area)
            results['blue_yellow'] = (by_result, by_data)
            
            if args.show:
                cv2.imshow("Blue-Yellow Channel Test", by_result)
        
        if args.channel in ['comprehensive', 'all']:
            comp_result, comp_data = detector.comprehensive_test(image_path, output_path, args.min_area)
            results['comprehensive'] = (comp_result, comp_data)
            
            if args.show:
                cv2.imshow("Comprehensive Test", comp_result)
        
        # 生成报告
        if args.report and 'red_green' in results and 'blue_yellow' in results and 'comprehensive' in results:
            report = detector.generate_report(
                image_path,
                results['red_green'][1],
                results['blue_yellow'][1], 
                results['comprehensive'][1]
            )
            
            report_path = output_path.parent / f"{output_path.stem}_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n测试报告已保存到: {report_path}")
            print(f"诊断结果: {report['diagnosis']['type']}")
            print(f"置信度: {report['diagnosis']['confidence']:.2f}")
            for note in report['diagnosis']['notes']:
                print(f"备注: {note}")
        
        if args.show:
            print("按任意键关闭窗口...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        return 0
        
    except Exception as e:
        print(f"错误：{e}")
        return 1


if __name__ == "__main__":
    exit(main())