#!/bin/bash
# Установка зависимостей на Arch Linux

echo "╔════════════════════════════════════════════════════════╗"
echo "║   Schematic Converter - Arch Linux Setup               ║"
echo "╚════════════════════════════════════════════════════════╝"

echo ""
echo "🔧 Обновление пакетов..."
sudo pacman -Syu --noconfirm

echo ""
echo "📦 Установка системных зависимостей..."
sudo pacman -S --noconfirm \
    python \
    python-pip \
    python-pyqt5 \
    opencv \
    tesseract \
    pillow

echo ""
echo "🐍 Установка Python пакетов..."
pip install --upgrade pip
pip install \
    opencv-python \
    pytesseract \
    pillow \
    numpy \
    scipy

# Опционально: для полной поддержки VSDX
echo ""
echo "⚙️ Установка опциональных пакетов для VSDX поддержки..."
pip install python-vsdx lxml

echo ""
echo "✅ Установка завершена!"
echo ""
echo "Для запуска программы используйте:"
echo "  python3 schematic_converter.py"
