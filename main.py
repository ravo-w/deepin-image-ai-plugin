#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Plugin for Deepin Image Viewer
提供抠图、换背景、增强、风格转换等功能，通过 D-Bus 服务暴露接口
"""

import os
import sys
import tempfile
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from rembg import remove, new_session
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

# ---------- 图像处理核心类 ----------
class ImageProcessor:
    @staticmethod
    def remove_background(input_path, output_path):
        """移除背景，使用人像专用模型 + alpha matting 提高质量"""
        try:
            session = new_session("u2net_human_seg")
            with open(input_path, 'rb') as f:
                input_data = f.read()
            output_data = remove(
                input_data,
                session=session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10,
                alpha_matting_erode_size=10
            )
            with open(output_path, 'wb') as f:
                f.write(output_data)
            return True
        except Exception as e:
            print(f"抠图失败: {e}")
            return False

    @staticmethod
    def change_background(input_path, new_bg_path, output_path):
        """更换背景：先抠图，再合成新背景"""
        temp_fg = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_fg.close()
        if not ImageProcessor.remove_background(input_path, temp_fg.name):
            return False
        foreground = Image.open(temp_fg.name).convert('RGBA')
        background = Image.open(new_bg_path).convert('RGBA').resize(foreground.size)
        background.paste(foreground, (0, 0), foreground)
        background.save(output_path, 'PNG')
        os.unlink(temp_fg.name)
        return True

    @staticmethod
    def enhance_brightness(input_path, output_path, factor):
        img = Image.open(input_path)
        enhancer = ImageEnhance.Brightness(img)
        result = enhancer.enhance(factor)
        result.save(output_path)
        return True

    @staticmethod
    def enhance_contrast(input_path, output_path, factor):
        img = Image.open(input_path)
        enhancer = ImageEnhance.Contrast(img)
        result = enhancer.enhance(factor)
        result.save(output_path)
        return True

    @staticmethod
    def sharpen(input_path, output_path):
        img = Image.open(input_path)
        result = img.filter(ImageFilter.SHARPEN)
        result.save(output_path)
        return True

    @staticmethod
    def apply_sketch(input_path, output_path):
        img = cv2.imread(input_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inverted = 255 - gray
        blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
        inverted_blurred = 255 - blurred
        sketch = cv2.divide(gray, inverted_blurred, scale=256.0)
        cv2.imwrite(output_path, sketch)
        return True

    @staticmethod
    def apply_cartoon(input_path, output_path):
        img = cv2.imread(input_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img, 9, 250, 250)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        cv2.imwrite(output_path, cartoon)
        return True

# ---------- D-Bus 服务 ----------
SERVICE_NAME = "com.deepin.ImageAI"
OBJECT_PATH = "/com/deepin/ImageAI"

class ImageAIService(dbus.service.Object):
    def __init__(self, bus_name):
        dbus.service.Object.__init__(self, bus_name, OBJECT_PATH)
        self.processor = ImageProcessor()

    @dbus.service.method(SERVICE_NAME, in_signature='ss', out_signature='s')
    def RemoveBackground(self, input_path, output_path):
        success = self.processor.remove_background(input_path, output_path)
        return output_path if success else ""

    @dbus.service.method(SERVICE_NAME, in_signature='sss', out_signature='s')
    def ChangeBackground(self, input_path, new_bg_path, output_path):
        success = self.processor.change_background(input_path, new_bg_path, output_path)
        return output_path if success else ""

    @dbus.service.method(SERVICE_NAME, in_signature='ssd', out_signature='s')
    def EnhanceBrightness(self, input_path, output_path, factor):
        success = self.processor.enhance_brightness(input_path, output_path, factor)
        return output_path if success else ""

    @dbus.service.method(SERVICE_NAME, in_signature='ssd', out_signature='s')
    def EnhanceContrast(self, input_path, output_path, factor):
        success = self.processor.enhance_contrast(input_path, output_path, factor)
        return output_path if success else ""

    @dbus.service.method(SERVICE_NAME, in_signature='ss', out_signature='s')
    def Sharpen(self, input_path, output_path):
        success = self.processor.sharpen(input_path, output_path)
        return output_path if success else ""

    @dbus.service.method(SERVICE_NAME, in_signature='ss', out_signature='s')
    def ApplySketch(self, input_path, output_path):
        success = self.processor.apply_sketch(input_path, output_path)
        return output_path if success else ""

    @dbus.service.method(SERVICE_NAME, in_signature='ss', out_signature='s')
    def ApplyCartoon(self, input_path, output_path):
        success = self.processor.apply_cartoon(input_path, output_path)
        return output_path if success else ""

# ---------- 主程序 ----------
def main():
    DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    bus_name = dbus.service.BusName(SERVICE_NAME, bus=session_bus)
    service = ImageAIService(bus_name)
    print("AI Plugin for Deepin Image Viewer started")
    print("D-Bus service registered at:", SERVICE_NAME)
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\nPlugin stopped.")

if __name__ == "__main__":
    main()
