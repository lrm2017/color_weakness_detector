#!/bin/bash
# OCR依赖安装脚本

echo "安装OCR相关依赖..."

# 更新包管理器
sudo apt update

# 安装tesseract OCR引擎和中文语言包
echo "安装Tesseract OCR引擎..."
sudo apt install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng

# 安装Python依赖
echo "安装Python依赖..."
pip install pytesseract opencv-python pillow

echo "依赖安装完成！"

# 验证安装
echo "验证Tesseract安装..."
tesseract --version

echo "验证中文语言包..."
tesseract --list-langs | grep chi_sim

echo "如果看到版本信息和chi_sim，说明安装成功！"