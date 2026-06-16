#!/bin/bash
# Быстрый запуск приложения

set -e

echo "🚀 Schematic Converter v1.0"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    echo "Установите: sudo pacman -S python"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Проверка зависимостей
echo ""
echo "📦 Проверка зависимостей..."

# Список обязательных пакетов
REQUIRED_MODULES=("cv2" "PyQt5" "PIL" "numpy" "pytesseract")

MISSING_MODULES=()

for module in "${REQUIRED_MODULES[@]}"; do
    if ! python3 -c "import $module" 2>/dev/null; then
        MISSING_MODULES+=("$module")
    fi
done

if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
    echo "⚠️  Отсутствуют модули: ${MISSING_MODULES[*]}"
    echo ""
    echo "Установите зависимости:"
    echo "  chmod +x install_arch.sh"
    echo "  ./install_arch.sh"
    exit 1
fi

echo "✅ Все зависимости установлены!"
echo ""

# Проверка Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract OCR не найден (опционально)"
    echo "Установите: sudo pacman -S tesseract"
    echo ""
fi

# Запуск приложения
echo "🎯 Запуск Schematic Converter..."
echo ""

python3 schematic_converter.py
