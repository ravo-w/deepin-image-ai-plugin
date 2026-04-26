#!/bin/bash
# AI 抠图插件一键安装脚本（适用于 Deepin V25 磐石系统）

set -e

echo "========================================="
echo "  Deepin AI 抠图插件安装脚本"
echo "========================================="

# 检测是否已有旧版本
if [ -f ~/.local/bin/deepin-image-ai-plugin ]; then
    echo "检测到已安装的版本，将覆盖更新..."
    pkill -f deepin-image-ai-plugin 2>/dev/null || true
fi

# 创建目录
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/dbus-1/services

# 复制主程序
cp main.py ~/.local/bin/deepin-image-ai-plugin
chmod +x ~/.local/bin/deepin-image-ai-plugin

# 创建 D-Bus 服务文件
cat > ~/.local/share/dbus-1/services/com.deepin.ImageAI.service << EOF
[D-BUS Service]
Name=com.deepin.ImageAI
Exec=$HOME/.local/bin/deepin-image-ai-plugin
User=bus
EOF

# 安装 Python 依赖
echo ""
echo "正在安装 Python 依赖（首次安装需要几分钟，请耐心等待）..."
pip3 install --user "rembg[cpu]" Pillow opencv-python PyQt5 dbus-python

# 预下载模型（可选，避免首次调用时等待）
echo ""
echo "正在准备 AI 模型（约 180MB，可能需要几分钟）..."
python3 -c "from rembg import remove, new_session; session = new_session('u2net_human_seg'); remove(b'', session=session)" 2>/dev/null || true

# 刷新 D-Bus 会话
dbus-send --session --dest=org.freedesktop.DBus --type=method_call --print-reply /org/freedesktop/DBus org.freedesktop.DBus.ReloadConfig >/dev/null 2>&1

echo ""
echo "========================================="
echo "✅ 安装完成！"
echo "========================================="
echo "使用方法："
echo "  dbus-send --session --type=method_call --print-reply \\"
echo "    --dest=com.deepin.ImageAI /com/deepin/ImageAI \\"
echo "    com.deepin.ImageAI.RemoveBackground \\"
echo "    string:\"图片路径\" string:\"输出路径\""
echo "========================================="