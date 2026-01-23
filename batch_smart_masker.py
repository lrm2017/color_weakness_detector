#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量智能答案遮挡工具 - 处理多个数据集
"""

import json
import time
from pathlib import Path
import argparse
from smart_answer_masker import SmartAnswerMasker

class BatchSmartMasker:
    def __init__(self):
        """初始化批量遮挡器"""
        self.masker = SmartAnswerMasker()
    
    def process_all_datasets(self, base_dir="downloaded_images", debug=False):
        """处理所有数据集"""
        base_path = Path(base_dir)
        
        if not base_path.exists():
            print(f"基础目录不存在: {base_path}")
            return
        
        # 查找所有包含answers.json的子目录
        datasets = []
        for subdir in base_path.iterdir():
            if subdir.is_dir():
                answers_file = subdir / "answers.json"
                if answers_file.exists():
                    datasets.append(subdir)
        
        if not datasets:
            print(f"在 {base_path} 中未找到包含answers.json的数据集")
            return
        
        print(f"发现 {len(datasets)} 个数据集:")
        for dataset in datasets:
            print(f"  - {dataset.name}")
        
        print(f"\n开始批量处理...")
        
        total_images = 0
        total_success = 0
        dataset_results = []
        
        for i, dataset_path in enumerate(datasets):
            print(f"\n{'='*60}")
            print(f"处理数据集 {i+1}/{len(datasets)}: {dataset_path.name}")
            print(f"{'='*60}")
            
            start_time = time.time()
            
            try:
                results = self.masker.batch_mask_dataset(dataset_path, debug=debug)
                
                if results:
                    success_count = sum(1 for r in results if r['success'])
                    total_count = len(results)
                    
                    dataset_result = {
                        'dataset_name': dataset_path.name,
                        'total_images': total_count,
                        'success_count': success_count,
                        'success_rate': success_count / total_count * 100 if total_count > 0 else 0,
                        'processing_time': time.time() - start_time,
                        'results': results
                    }
                    
                    dataset_results.append(dataset_result)
                    total_images += total_count
                    total_success += success_count
                    
                    print(f"\n数据集 {dataset_path.name} 处理完成:")
                    print(f"  图像总数: {total_count}")
                    print(f"  成功遮挡: {success_count}")
                    print(f"  成功率: {success_count/total_count*100:.1f}%")
                    print(f"  处理时间: {time.time() - start_time:.1f}秒")
                else:
                    print(f"数据集 {dataset_path.name} 处理失败")
                    
            except Exception as e:
                print(f"处理数据集 {dataset_path.name} 时出错: {e}")
        
        # 保存总体结果
        summary_file = base_path / "batch_masking_summary.json"
        summary = {
            'total_datasets': len(datasets),
            'total_images': total_images,
            'total_success': total_success,
            'overall_success_rate': total_success / total_images * 100 if total_images > 0 else 0,
            'datasets': dataset_results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 打印总结
        print(f"\n{'='*60}")
        print(f"批量处理总结")
        print(f"{'='*60}")
        print(f"处理数据集: {len(datasets)}")
        print(f"总图像数: {total_images}")
        print(f"成功遮挡: {total_success}")
        print(f"总体成功率: {total_success/total_images*100:.1f}%" if total_images > 0 else "0%")
        print(f"详细结果保存到: {summary_file}")
        
        # 显示各数据集统计
        print(f"\n各数据集详细统计:")
        print(f"{'数据集名称':<20} {'图像数':<8} {'成功数':<8} {'成功率':<10} {'处理时间':<10}")
        print(f"{'-'*60}")
        
        for result in dataset_results:
            print(f"{result['dataset_name']:<20} "
                  f"{result['total_images']:<8} "
                  f"{result['success_count']:<8} "
                  f"{result['success_rate']:<9.1f}% "
                  f"{result['processing_time']:<9.1f}s")
        
        return summary
    
    def create_comparison_report(self, base_dir="downloaded_images"):
        """创建对比报告，显示遮挡前后的效果"""
        base_path = Path(base_dir)
        summary_file = base_path / "batch_masking_summary.json"
        
        if not summary_file.exists():
            print(f"未找到批量处理结果文件: {summary_file}")
            return
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        # 创建HTML报告
        html_content = self._generate_html_report(summary, base_path)
        
        report_file = base_path / "masking_comparison_report.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"对比报告已生成: {report_file}")
        return report_file
    
    def _generate_html_report(self, summary, base_path):
        """生成HTML对比报告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能答案遮挡效果报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .summary {{ background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .dataset {{ background-color: white; margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .dataset-header {{ background-color: #34495e; color: white; padding: 15px; }}
        .dataset-content {{ padding: 20px; }}
        .stats {{ display: flex; justify-content: space-around; margin-bottom: 20px; }}
        .stat-item {{ text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .stat-label {{ color: #7f8c8d; }}
        .image-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .image-pair {{ border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
        .image-pair img {{ width: 100%; height: auto; display: block; }}
        .image-label {{ padding: 10px; background-color: #ecf0f1; text-align: center; font-weight: bold; }}
        .success {{ color: #27ae60; }}
        .failure {{ color: #e74c3c; }}
        .progress-bar {{ width: 100%; height: 20px; background-color: #ecf0f1; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background-color: #3498db; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 智能答案遮挡效果报告</h1>
        <p>生成时间: {summary.get('timestamp', 'Unknown')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 总体统计</h2>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{summary.get('total_datasets', 0)}</div>
                <div class="stat-label">数据集</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{summary.get('total_images', 0)}</div>
                <div class="stat-label">总图像数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{summary.get('total_success', 0)}</div>
                <div class="stat-label">成功遮挡</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{summary.get('overall_success_rate', 0):.1f}%</div>
                <div class="stat-label">总体成功率</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {summary.get('overall_success_rate', 0)}%"></div>
        </div>
    </div>
"""
        
        # 添加各数据集的详细信息
        for dataset in summary.get('datasets', []):
            dataset_name = dataset['dataset_name']
            success_rate = dataset['success_rate']
            status_class = 'success' if success_rate > 80 else 'failure'
            
            html += f"""
    <div class="dataset">
        <div class="dataset-header">
            <h3>📁 {dataset_name}</h3>
        </div>
        <div class="dataset-content">
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{dataset['total_images']}</div>
                    <div class="stat-label">图像总数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number {status_class}">{dataset['success_count']}</div>
                    <div class="stat-label">成功遮挡</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number {status_class}">{success_rate:.1f}%</div>
                    <div class="stat-label">成功率</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{dataset['processing_time']:.1f}s</div>
                    <div class="stat-label">处理时间</div>
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate}%"></div>
            </div>
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html

def main():
    parser = argparse.ArgumentParser(description='批量智能答案遮挡工具')
    parser.add_argument('--base-dir', default='downloaded_images', help='基础目录路径')
    parser.add_argument('--debug', action='store_true', help='显示调试信息')
    parser.add_argument('--report', action='store_true', help='生成对比报告')
    
    args = parser.parse_args()
    
    batch_masker = BatchSmartMasker()
    
    if args.report:
        # 生成对比报告
        batch_masker.create_comparison_report(args.base_dir)
    else:
        # 批量处理所有数据集
        batch_masker.process_all_datasets(args.base_dir, args.debug)

if __name__ == "__main__":
    main()