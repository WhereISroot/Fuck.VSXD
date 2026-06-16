#!/usr/bin/env python3
"""
Simple test script for contour extraction
Простой скрипт для тестирования извлечения контуров
"""

import sys
from pathlib import Path
from contour_extractor import ContourExtractor


def test_contour_extraction(image_path):
    """Тестирует извлечение контуров"""
    
    print(f"📁 Загружаю изображение: {image_path}")
    
    # Создаем экстрактор
    extractor = ContourExtractor(image_path)
    
    # Загружаем изображение
    if not extractor.load_image():
        print("❌ Ошибка загрузки изображения")
        return False
    
    print(f"✓ Изображение загружено ({extractor.image.shape[1]}x{extractor.image.shape[0]})")
    
    # Предварительная обработка
    print("🔄 Предварительная обработка...")
    extractor.preprocess_image()
    print("✓ Готово")
    
    # Извлечение контуров
    print("🔎 Извлечение контуров...")
    contours = extractor.extract_contours(min_area=50)
    print(f"✓ Найдено контуров: {len(contours)}")
    
    if len(contours) > 0:
        print("\n📊 Статистика контуров:")
        print(f"  - Макс площадь: {max(c['area'] for c in contours):.2f}")
        print(f"  - Мин площадь: {min(c['area'] for c in contours):.2f}")
        print(f"  - Макс вершин: {max(c['vertices_count'] for c in contours)}")
        print(f"  - Мин вершин: {min(c['vertices_count'] for c in contours)}")
    
    # Разделение на части
    print("\n✂️ Разделение контуров на части...")
    parts = extractor.split_contours_into_parts()
    print(f"✓ Выделено частей: {len(parts)}")
    
    # Экспорт
    output_stem = Path(image_path).stem
    
    print("\n💾 Экспорт CSV...")
    extractor.export_to_csv(f"{output_stem}_contours.csv")
    print(f"  ✓ {output_stem}_contours.csv")
    print(f"  ✓ {output_stem}_parts.csv")
    print(f"  ✓ {output_stem}_vertices.csv")
    
    print("\n💾 Экспорт JSON...")
    extractor.export_to_json(f"{output_stem}_contours.json")
    print(f"  ✓ {output_stem}_contours.json")
    
    print("\n🎨 Генерация визуализации...")
    extractor.visualize_contours(f"{output_stem}_visualization.jpg")
    print(f"  ✓ {output_stem}_visualization.jpg")
    
    print("\n✅ Готово!")
    print(f"\nСозданные файлы:")
    print(f"  - {output_stem}_contours.csv")
    print(f"  - {output_stem}_parts.csv")
    print(f"  - {output_stem}_vertices.csv")
    print(f"  - {output_stem}_contours.json")
    print(f"  - {output_stem}_visualization.jpg")
    
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("❌ Использование: python test_contours.py <путь_к_изображению>")
        print("\nПримеры:")
        print("  python test_contours.py schema.jpg")
        print("  python test_contours.py /path/to/circuit.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"❌ Файл не найден: {image_path}")
        sys.exit(1)
    
    success = test_contour_extraction(image_path)
    sys.exit(0 if success else 1)
