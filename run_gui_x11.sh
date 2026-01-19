#!/bin/bash

# 检查fcitx5是否正在运行
if ! pgrep -x "fcitx5" > /dev/null; then
    echo "启动fcitx5..."
    fcitx5 -d
    sleep 2
fi

# 强制使用X11而不是Wayland
export QT_QPA_PLATFORM=xcb
export GDK_BACKEND=x11

# 设置fcitx输入法环境变量
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
export GTK_IM_MODULE=fcitx

# 显示当前环境变量
echo "强制使用X11模式启动"
echo "当前输入法环境变量:"
echo "QT_IM_MODULE=$QT_IM_MODULE"
echo "XMODIFIERS=$XMODIFIERS"
echo "GTK_IM_MODULE=$GTK_IM_MODULE"
echo "QT_QPA_PLATFORM=$QT_QPA_PLATFORM"
echo "GDK_BACKEND=$GDK_BACKEND"

# 启动GUI应用
echo "启动色弱图谱识别程序..."
python3 gui_app.py