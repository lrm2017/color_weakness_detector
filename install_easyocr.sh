#!/bin/bash
# EasyOCR安装脚本

echo "安装EasyOCR相关依赖..."

# 安装EasyOCR
echo "安装EasyOCR..."
pip install easyocr

# 安装其他必要依赖
echo "安装其他依赖..."
pip install opencv-python pillow requests numpy

echo "EasyOCR安装完成！"

# 测试安装
echo "测试EasyOCR安装..."
python -c "
try:
    import easyocr
    print('✓ EasyOCR导入成功')
    reader = easyocr.Reader(['ch_sim', 'en'])
    print('✓ EasyOCR初始化成功')
except Exception as e:
    print(f'✗ EasyOCR测试失败: {e}')
"

echo "如果看到成功信息，说明EasyOCR安装正确！"