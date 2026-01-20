#!/bin/bash

# 检查fcitx5是否正在运行
if ! pgrep -x "fcitx5" > /dev/null; then
    echo "启动fcitx5..."
    fcitx5 -d
    sleep 2
fi

# 设置fcitx输入法环境变量（注意使用fcitx而不是fcitx5）
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
export GTK_IM_MODULE=fcitx

# 对于Wayland环境，可能需要额外设置
export QT_QPA_PLATFORM=wayland
export QT_WAYLAND_DISABLE_WINDOWDECORATION=1

# 显示当前环境变量
echo "当前输入法环境变量:"
echo "QT_IM_MODULE=$QT_IM_MODULE"
echo "XMODIFIERS=$XMODIFIERS"
echo "GTK_IM_MODULE=$GTK_IM_MODULE"
echo "QT_QPA_PLATFORM=$QT_QPA_PLATFORM"

# 启动GUI应用
echo "启动色弱图谱识别程序..."
python3 gui_app.py