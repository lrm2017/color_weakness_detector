#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能答案遮挡工具 - 自动检测答案位置并进行遮挡
"""

import cv2
import numpy as np
import json
import easyocr
from pathlib import Path
import argparse
import time

class SmartAnswerMasker:
    def __init__(self):
        """初始化智能答案遮挡器"""
        print("初始化EasyOCR...")
        self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        print("EasyOCR初始化完成")
        
    def detect_answer_regions(self, image_path, expected_answer=None, debug=False):
        """
        检测图像中的答案区域
        
        Args:
            image_path: 图像路径
            expected_answer: 预期的答案文本（用于验证）
            debug: 是否显示调试信息
            
        Returns:
            list: 检测到的答案区域列表，每个区域包含坐标和置信度
        """
        img = cv2.imread(image_path)
        if img is None:
            if debug:
                print(f"无法读取图像: {image_path}")
            return []
        
        height, width = img.shape[:2]
        if debug:
            print(f"图像尺寸: {width}x{height}")
        
        # 定义可能的答案区域（优先级从高到低）
        search_regions = [
            # 左下角区域
            {"name": "left_bottom", "coords": (0, int(height*0.75), int(width*0.4), height), "priority": 1},
            {"name": "left_bottom_large", "coords": (0, int(height*0.7), int(width*0.5), height), "priority": 2},
            
            # 右下角区域
            {"name": "right_bottom", "coords": (int(width*0.6), int(height*0.75), width, height), "priority": 1},
            {"name": "right_bottom_large", "coords": (int(width*0.5), int(height*0.7), width, height), "priority": 2},
            
            # 底部区域
            {"name": "bottom_center", "coords": (int(width*0.2), int(height*0.8), int(width*0.8), height), "priority": 3},
            {"name": "full_bottom", "coords": (0, int(height*0.85), width, height), "priority": 4},
            
            # 左右侧边
            {"name": "left_side", "coords": (0, int(height*0.3), int(width*0.3), height), "priority": 5},
            {"name": "right_side", "coords": (int(width*0.7), int(height*0.3), width, height), "priority": 5},
            
            # 四个角落
            {"name": "top_left", "coords": (0, 0, int(width*0.3), int(height*0.3)), "priority": 6},
            {"name": "top_right", "coords": (int(width*0.7), 0, width, int(height*0.3)), "priority": 6},
        ]
        
        detected_regions = []
        
        for region in search_regions:
            x1, y1, x2, y2 = region["coords"]
            roi = img[y1:y2, x1:x2]
            
            if roi.size == 0:
                continue
            
            try:
                # 使用EasyOCR检测文字
                results = self.reader.readtext(roi)
                
                for (bbox, text, confidence) in results:
                    if text and text.strip() and confidence > 0.3:  # 置信度阈值
                        # 将相对坐标转换为绝对坐标
                        abs_bbox = []
                        for point in bbox:
                            abs_x = int(point[0] + x1)
                            abs_y = int(point[1] + y1)
                            abs_bbox.append([abs_x, abs_y])
                        
                        detected_region = {
                            'text': text.strip(),
                            'confidence': confidence,
                            'bbox': abs_bbox,
                            'region_name': region["name"],
                            'priority': region["priority"],
                            'area_coords': (x1, y1, x2, y2)
                        }
                        
                        # 如果提供了预期答案，检查匹配度
                        if expected_answer:
                            if self._is_answer_match(text.strip(), expected_answer):
                                detected_region['is_expected'] = True
                                detected_region['priority'] = 0  # 最高优先级
                            else:
                                detected_region['is_expected'] = False
                        
                        detected_regions.append(detected_region)
                        
                        if debug:
                            print(f"  {region['name']}: '{text.strip()}' (置信度: {confidence:.2f})")
                            if expected_answer:
                                match = "✓" if detected_region.get('is_expected', False) else "✗"
                                print(f"    预期匹配: {match}")
                
            except Exception as e:
                if debug:
                    print(f"  {region['name']} OCR失败: {e}")
                continue
        
        # 按优先级和置信度排序
        detected_regions.sort(key=lambda x: (x['priority'], -x['confidence']))
        
        if debug:
            print(f"\n检测到 {len(detected_regions)} 个文字区域")
            for i, region in enumerate(detected_regions[:5]):  # 显示前5个
                print(f"  {i+1}. '{region['text']}' (优先级: {region['priority']}, 置信度: {region['confidence']:.2f})")
        
        return detected_regions
    
    def _is_answer_match(self, detected_text, expected_answer):
        """检查检测到的文字是否与预期答案匹配"""
        if not detected_text or not expected_answer:
            return False
        
        # 清理文本
        detected_clean = detected_text.strip().lower()
        expected_clean = expected_answer.strip().lower()
        
        # 完全匹配
        if detected_clean == expected_clean:
            return True
        
        # 包含匹配
        if expected_clean in detected_clean or detected_clean in expected_clean:
            return True
        
        # 去除常见的OCR错误字符后匹配
        ocr_error_chars = {'o': '0', '0': 'o', 'i': '1', '1': 'i', 'l': '1'}
        for old, new in ocr_error_chars.items():
            if detected_clean.replace(old, new) == expected_clean:
                return True
        
        return False
    
    def create_mask_for_region(self, image_shape, bbox, padding=5):
        """
        为指定区域创建遮挡蒙版
        
        Args:
            image_shape: 图像形状 (height, width, channels)
            bbox: 边界框坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            padding: 遮挡区域的扩展像素
            
        Returns:
            numpy.ndarray: 遮挡蒙版
        """
        height, width = image_shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # 将bbox转换为numpy数组
        points = np.array(bbox, dtype=np.int32)
        
        # 扩展边界框
        center_x = np.mean(points[:, 0])
        center_y = np.mean(points[:, 1])
        
        expanded_points = []
        for point in points:
            # 向外扩展
            dx = point[0] - center_x
            dy = point[1] - center_y
            
            if dx != 0:
                dx = dx + (padding if dx > 0 else -padding)
            if dy != 0:
                dy = dy + (padding if dy > 0 else -padding)
            
            new_x = max(0, min(width-1, int(center_x + dx)))
            new_y = max(0, min(height-1, int(center_y + dy)))
            expanded_points.append([new_x, new_y])
        
        expanded_points = np.array(expanded_points, dtype=np.int32)
        
        # 填充多边形区域
        cv2.fillPoly(mask, [expanded_points], 255)
        
        return mask
    
    def apply_smart_mask(self, image_path, output_path, expected_answer=None, 
                        mask_color=(128, 128, 128), debug=False):
        """
        应用智能遮挡
        
        Args:
            image_path: 输入图像路径
            output_path: 输出图像路径
            expected_answer: 预期答案（用于验证）
            mask_color: 遮挡颜色 (B, G, R)
            debug: 是否显示调试信息
            
        Returns:
            dict: 处理结果信息
        """
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "无法读取图像"}
        
        if debug:
            print(f"处理图像: {image_path}")
        
        # 检测答案区域
        detected_regions = self.detect_answer_regions(image_path, expected_answer, debug)
        
        if not detected_regions:
            if debug:
                print("未检测到任何文字区域")
            return {"success": False, "error": "未检测到文字区域"}
        
        # 选择最佳的答案区域进行遮挡
        masked_regions = []
        result_img = img.copy()
        
        # 如果有预期答案，优先遮挡匹配的区域
        if expected_answer:
            matching_regions = [r for r in detected_regions if r.get('is_expected', False)]
            if matching_regions:
                target_regions = matching_regions[:1]  # 只遮挡最匹配的一个
            else:
                # 如果没有匹配的，选择优先级最高的
                target_regions = detected_regions[:1]
        else:
            # 没有预期答案时，遮挡所有可能的答案区域（优先级高的）
            target_regions = [r for r in detected_regions if r['priority'] <= 2][:3]  # 最多遮挡3个区域
        
        for region in target_regions:
            # 创建遮挡蒙版
            mask = self.create_mask_for_region(img.shape, region['bbox'], padding=8)
            
            # 应用遮挡
            result_img[mask > 0] = mask_color
            
            masked_regions.append({
                'text': region['text'],
                'confidence': region['confidence'],
                'region_name': region['region_name'],
                'bbox': region['bbox']
            })
            
            if debug:
                print(f"遮挡区域: '{region['text']}' (置信度: {region['confidence']:.2f})")
        
        # 保存结果
        cv2.imwrite(output_path, result_img)
        
        return {
            "success": True,
            "masked_regions": masked_regions,
            "total_detected": len(detected_regions),
            "total_masked": len(masked_regions)
        }
    
    def batch_mask_dataset(self, dataset_path, output_dir=None, debug=False):
        """
        批量处理数据集
        
        Args:
            dataset_path: 数据集路径
            output_dir: 输出目录（默认为数据集路径下的masked_images）
            debug: 是否显示调试信息
        """
        dataset_path = Path(dataset_path)
        
        if output_dir is None:
            output_dir = dataset_path / "masked_images"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(exist_ok=True)
        
        # 读取答案文件
        answers_file = dataset_path / "answers.json"
        answers_data = {}
        
        if answers_file.exists():
            try:
                with open(answers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for entry in data:
                    answers_data[entry['filename']] = entry.get('answer', '')
            except Exception as e:
                print(f"读取答案文件失败: {e}")
        
        # 优先使用original_images目录中的原始图像
        original_images_dir = dataset_path / "original_images"
        if original_images_dir.exists():
            print(f"使用原始图像目录: {original_images_dir}")
            image_files = list(original_images_dir.glob("*.jpg")) + list(original_images_dir.glob("*.png"))
        else:
            print(f"使用主目录图像: {dataset_path}")
            image_files = list(dataset_path.glob("*.jpg")) + list(dataset_path.glob("*.png"))
        
        if not image_files:
            print(f"在 {dataset_path} 中未找到图像文件")
            return
        
        print(f"开始处理 {len(image_files)} 个图像...")
        
        results = []
        success_count = 0
        
        for i, image_file in enumerate(image_files):
            print(f"\n处理 {i+1}/{len(image_files)}: {image_file.name}")
            
            expected_answer = answers_data.get(image_file.name, None)
            output_path = output_dir / image_file.name
            
            result = self.apply_smart_mask(
                str(image_file), 
                str(output_path), 
                expected_answer, 
                debug=debug
            )
            
            result['filename'] = image_file.name
            result['expected_answer'] = expected_answer
            results.append(result)
            
            if result['success']:
                success_count += 1
                print(f"  ✓ 成功遮挡 {result['total_masked']} 个区域")
                if debug and result.get('masked_regions'):
                    for region in result['masked_regions']:
                        print(f"    - 遮挡: '{region['text']}' (置信度: {region['confidence']:.2f})")
            else:
                print(f"  ✗ 失败: {result.get('error', '未知错误')}")
        
        # 保存处理结果
        results_file = output_dir / "masking_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 批量处理完成 ===")
        print(f"总计: {len(image_files)}")
        print(f"成功: {success_count}")
        print(f"失败: {len(image_files) - success_count}")
        print(f"成功率: {success_count/len(image_files)*100:.1f}%")
        print(f"结果保存到: {output_dir}")
        print(f"详细结果: {results_file}")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='智能答案遮挡工具')
    parser.add_argument('--image', help='单个图像文件路径')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--dataset', help='数据集目录路径')
    parser.add_argument('--answer', help='预期答案（用于验证）')
    parser.add_argument('--debug', action='store_true', help='显示调试信息')
    
    args = parser.parse_args()
    
    masker = SmartAnswerMasker()
    
    if args.image:
        # 处理单个图像
        if not args.output:
            args.output = args.image.replace('.jpg', '_masked.jpg').replace('.png', '_masked.png')
        
        result = masker.apply_smart_mask(args.image, args.output, args.answer, debug=args.debug)
        
        if result['success']:
            print(f"成功遮挡图像，保存到: {args.output}")
            print(f"遮挡了 {result['total_masked']} 个区域")
        else:
            print(f"处理失败: {result.get('error', '未知错误')}")
    
    elif args.dataset:
        # 批量处理数据集
        masker.batch_mask_dataset(args.dataset, debug=args.debug)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()