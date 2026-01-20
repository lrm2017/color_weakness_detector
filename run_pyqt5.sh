#!/bin/bash

echo "=== fcitx5输入法诊断和修复 ==="

# 检查fcitx5是否运行
if ! pgrep -x "fcitx5" > /dev/null; then
    echo "fcitx5未运行，正在启动..."
    fcitx5 -d
    sleep 3
else
    echo "fcitx5正在运行"
fi

# 重启fcitx5以确保配置生效
echo "重启fcitx5..."
pkill fcitx5
sleep 1
fcitx5 -d
sleep 2

# 设置环境变量
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
export GTK_IM_MODULE=fcitx

echo "环境变量设置:"
echo "  QT_IM_MODULE=$QT_IM_MODULE"
echo "  XMODIFIERS=$XMODIFIERS"
echo "  GTK_IM_MODULE=$GTK_IM_MODULE"

# 检查输入法状态
echo "检查输入法状态:"
fcitx5-remote -s
echo "当前输入法: $(fcitx5-remote -n)"

echo ""
echo "=== 启动PyQt5版本程序 ==="
echo "使用提示:"
echo "1. 点击输入框"
echo "2. 按 Ctrl+Space 或 Shift 切换到中文输入法"
echo "3. 开始输入拼音"
echo ""

python3 gui_app_pyqt5.py