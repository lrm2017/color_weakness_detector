#!/bin/bash

echo "=== 最终输入法修复方案 ==="

# 确保fcitx5运行
if ! pgrep -x "fcitx5" > /dev/null; then
    echo "启动fcitx5..."
    fcitx5 -d
    sleep 2
fi

# 激活fcitx5
echo "激活fcitx5输入法..."
fcitx5-remote -o

# 检查状态
status=$(fcitx5-remote)
if [ "$status" = "2" ]; then
    echo "✓ fcitx5已激活"
else
    echo "✗ fcitx5未激活，状态: $status"
fi

# 设置环境变量
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
export GTK_IM_MODULE=fcitx

echo "环境变量:"
echo "  QT_IM_MODULE=$QT_IM_MODULE"
echo "  XMODIFIERS=$XMODIFIERS"
echo "  GTK_IM_MODULE=$GTK_IM_MODULE"

echo ""
echo "=== 启动程序 ==="
echo "输入法使用说明:"
echo "1. 程序启动后，点击输入框"
echo "2. 按 Ctrl+Space 切换到中文输入法"
echo "3. 直接输入拼音，应该会出现候选词"
echo ""

# 启动PyQt5版本（通常兼容性更好）
python3 gui_app_pyqt5.py