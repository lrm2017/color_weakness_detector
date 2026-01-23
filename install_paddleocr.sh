#!/bin/bash
# PaddleOCR安装脚本

echo "安装PaddleOCR相关依赖..."

# 安装PaddleOCR
echo "安装PaddleOCR..."
pip install paddlepaddle paddleocr

# 安装其他必要依赖
echo "安装其他依赖..."
pip install opencv-python pillow requests numpy

echo "PaddleOCR安装完成！"

# 测试安装
echo "测试PaddleOCR安装..."
python -c "
try:
    from paddleocr import PaddleOCR
    print('✓ PaddleOCR导入成功')
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    print('✓ PaddleOCR初始化成功')
except Exception as e:
    print(f'✗ PaddleOCR测试失败: {e}')
"

echo "如果看到成功信息，说明PaddleOCR安装正确！"