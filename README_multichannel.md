# 多通道色觉检测系统

## 概述

基于原有的色弱图谱识别程序，我们添加了多通道色觉测试功能，提供更精确和全面的色觉缺陷诊断。

## 新增功能

### 1. 多通道色觉检测器 (`multi_channel_color_detector.py`)

**核心功能：**
- **红绿通道测试**：专门检测红色盲/弱（Protanopia/Protanomaly）和绿色盲/弱（Deuteranopia/Deuteranomaly）
- **蓝黄通道测试**：专门检测蓝色盲/弱（Tritanopia/Tritanomaly）
- **综合色觉评估**：整合多通道结果，提供全面诊断

**技术特点：**
- 基于HSV色彩空间的精确颜色分割
- 使用色觉混淆线理论进行分析
- 支持连通组件分析和形态学操作去噪
- 生成详细的JSON测试报告

**使用方法：**
```bash
# 全通道测试
python multi_channel_color_detector.py image.jpg --channel all --report

# 单通道测试
python multi_channel_color_detector.py image.jpg --channel red_green
python multi_channel_color_detector.py image.jpg --channel blue_yellow
```

### 2. 简化测试工具 (`simple_color_test.py`)

**功能：**
- 快速颜色分布分析
- 批量图像测试
- 简化的诊断输出

**使用方法：**
```bash
# 单图测试
python simple_color_test.py image.jpg

# 批量测试
python simple_color_test.py image_folder/ --batch --max-files 10
```

### 3. 可视化分析工具 (`visualize_color_test.py`)

**功能：**
- 生成多通道颜色分布可视化
- 创建颜色分布饼图和柱状图
- 高亮显示各颜色通道区域

**使用方法：**
```bash
python visualize_color_test.py image.jpg --show
```

### 4. 批量测试工具 (`batch_color_test.py`)

**功能：**
- 批量处理多个图像
- 生成汇总统计报告
- 支持自定义输出目录

## 色觉检测原理

### 颜色通道定义

**红绿通道 (Red-Green Channel):**
- 红色范围：H值 0-10° 和 156-180°
- 橙色范围：H值 10-25°
- 绿色范围：H值 35-85°
- 黄绿色范围：H值 35-50°

**蓝黄通道 (Blue-Yellow Channel):**
- 蓝色范围：H值 105-130°
- 青色范围：H值 85-105°
- 紫色范围：H值 130-156°
- 黄色范围：H值 25-35°

### 诊断算法

1. **像素统计分析**：计算各颜色通道的像素数量和比例
2. **区域检测**：使用连通组件分析识别色块区域
3. **混淆模式识别**：基于颜色分布检测异常模式
4. **置信度评估**：根据检测结果计算诊断置信度

### 支持的色觉缺陷类型

- **Protanomaly/Protanopia**：红色弱/红色盲
- **Deuteranomaly/Deuteranopia**：绿色弱/绿色盲  
- **Tritanomaly/Tritanopia**：蓝色弱/蓝色盲
- **Normal**：正常色觉

## 测试结果示例

### 批量测试统计
```
=== 批量测试汇总 ===
诊断统计:
  possible_deuteranomaly: 5 个
  possible_tritanomaly: 2 个
  normal: 1 个
```

### 单图详细分析
```
测试图像: 001.jpg
  总彩色像素: 93385
  红绿通道 - 红色: 60.8%, 绿色: 39.2%
  蓝黄通道 - 蓝色: 72.7%, 黄色: 27.3%
  颜色分布:
    red: 32.3%
    orange: 4.5%
    yellow: 9.7%
    green: 23.7%
    cyan: 25.3%
  诊断: normal
```

## 输出文件

### 图像输出
- `*_red_green.jpg`：红绿通道检测结果
- `*_blue_yellow.jpg`：蓝黄通道检测结果
- `*_comprehensive.jpg`：综合分析结果
- `*_visualization.png`：可视化分析图
- `*_chart.png`：颜色分布图表

### 数据输出
- `*_report.json`：详细测试报告
- `batch_test_summary.json`：批量测试汇总

## 技术优势

1. **多通道分析**：分别测试红绿、蓝黄通道，提供更精确的诊断
2. **科学依据**：基于色觉混淆线理论和CIE色彩空间
3. **自动化处理**：支持批量测试和自动报告生成
4. **可视化展示**：直观的图表和高亮显示
5. **灵活配置**：支持多种测试模式和参数调整

## 应用场景

- **医疗筛查**：色觉缺陷的初步筛查和评估
- **职业测试**：需要色觉要求的职业准入测试
- **教育研究**：色觉相关的教学和研究
- **产品设计**：考虑色觉缺陷用户的界面设计

## 依赖包

```
opencv-python>=4.5.0
numpy>=1.19.0
matplotlib>=3.5.0
```

## 注意事项

1. 测试结果仅供参考，不能替代专业医学诊断
2. 显示器色彩校准会影响测试准确性
3. 环境光线条件可能影响结果
4. 建议结合多种测试方法进行综合评估