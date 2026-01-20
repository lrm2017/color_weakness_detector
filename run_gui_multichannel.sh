#!/bin/bash
"""
启动多通道色觉检测GUI应用
"""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查依赖包
echo "检查依赖包..."
python3 -c "
import sys
try:
    import cv2
    import numpy as np
    import PySide6
    import matplotlib
    print('✓ 所有依赖包已安装')
except ImportError as e:
    print(f'✗ 缺少依赖包: {e}')
    print('请运行: pip install -r requirements.txt')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 检查必要文件
echo "检查必要文件..."
required_files=(
    "gui_app.py"
    "multi_channel_color_detector.py"
    "simple_color_test.py"
    "color_detector.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "✗ 缺少文件: $file"
        exit 1
    fi
done

echo "✓ 所有必要文件存在"

# 创建必要目录
mkdir -p test_results
mkdir -p downloaded_images

echo "启动多通道色觉检测GUI应用..."
echo "功能特性:"
echo "  • 原始冷暖色识别"
echo "  • 红绿通道专项测试"
echo "  • 蓝黄通道专项测试"
echo "  • 综合多通道分析"
echo "  • 快速颜色分析"
echo "  • 测试结果管理"
echo ""

# 启动GUI应用
python3 gui_app.py

echo "应用已退出"