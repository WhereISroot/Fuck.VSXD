#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 QUICK START GUIDE - Быстрый старт (v2.0)
Schematic Converter with CSV Contour Export
"""

import os
import sys
from pathlib import Path


class QuickStart:
    """Интерактивное руководство быстрого старта"""
    
    STEPS = {
        '1': {
            'title': '🔧 Установка',
            'description': 'Установить зависимости',
            'details': """
            Linux/macOS:
            ─────────────
            pip install -r requirements.txt
            
            Windows:
            ────────
            pip install -r requirements.txt
            
            Tesseract (для OCR):
            ──────────────────
            Linux (Arch):     sudo pacman -S tesseract
            Linux (Ubuntu):   sudo apt-get install tesseract-ocr
            macOS:            brew install tesseract
            Windows:          https://github.com/UB-Mannheim/tesseract/wiki
            """
        },
        '2': {
            'title': '📸 Подготовка изображения',
            'description': 'Подготовить схему к обработке',
            'details': """
            Требования к изображению:
            ─────────────────────────
            ✓ Формат: JPG, PNG, BMP
            ✓ Размер: минимум 500x500 пикселей
            ✓ Контрастность: хороший контраст между схемой и фоном
            ✓ Резкость: четкие линии без размытия
            ✓ Освещение: равномерное без теней
            
            Советы:
            ──────
            • Снимайте фото под прямым углом
            • Используйте хорошее освещение
            • Избегайте бликов и теней
            • Обрезайте лишние части изображения
            """
        },
        '3': {
            'title': '🖥️ Запуск программы',
            'description': 'Запустить графический интерфейс',
            'details': """
            Linux/macOS:
            ────────────
            python3 schematic_converter.py
            
            Windows:
            ────────
            python schematic_converter.py
            
            Откроется окно с интерфейсом:
            ───────────────────────────
            1. Вкладка "Конвертер" - основная работа
            2. Вкладка "Справка" - документация
            """
        },
        '4': {
            'title': '⚙️ Обработка изображения',
            'description': 'Конвертировать схему в CSV/VSDX',
            'details': """
            Шаги в интерфейсе:
            ───────────────────
            1. Нажмите "📂 Загрузить изображение"
            2. Выберите файл схемы (JPG, PNG, BMP)
            3. Выберите форматы экспорта:
               ☑ CSV (для Microsoft Drawing)
               ☑ VSDX (для Microsoft Visio)
            4. Нажмите "⚙️ Конвертировать"
            5. Выберите место и имя файла
            6. Дождитесь завершения обработки
            
            Время обработки:
            ────────────────
            • Типичное изображение: 5-15 секунд
            • Сложная схема: до 1 минуты
            """
        },
        '5': {
            'title': '📊 Использование CSV',
            'description': 'Работа с экспортированными CSV файлами',
            'details': """
            Созданные файлы:
            ────────────────
            schema_contours.csv    - Основные контуры
            schema_parts.csv       - Отдельные части
            schema_vertices.csv    - Координаты вершин
            schema_contours.json   - JSON данные
            schema_visualization.jpg - Визуализация
            
            Использование в Microsoft Drawing:
            ─────────────────────────────────
            1. Используйте schema_vertices.csv
            2. Импортируйте координаты в Drawing
            3. Нарисуйте фигуры по координатам
            
            Или используйте csv_drawer.py:
            ──────────────────────────────
            python csv_drawer.py schema_vertices.csv result.jpg
            
            Это создаст изображение с нарисованными фигурами
            """
        },
        '6': {
            'title': '🖼️ Проверка результатов',
            'description': 'Проверить качество обработки',
            'details': """
            Файл визуализации:
            ──────────────────
            schema_visualization.jpg
            
            На нем отображено:
            • Все обнаруженные контуры (разные цвета)
            • ID каждого контура
            • Центроиды отдельных частей (желтые точки)
            
            Если результаты неудовлетворительны:
            ──────────────────────────────────
            1. Улучшите качество исходного изображения
            2. Увеличьте контрастность
            3. Попробуйте другое изображение
            4. Отрегулируйте параметры в contour_extractor.py
            """
        },
        '7': {
            'title': '💻 Использование в коде',
            'description': 'Интеграция в собственные программы',
            'details': """
            Пример 1: Базовое использование
            ───────────────────────────────
            from contour_extractor import ContourExtractor
            
            extractor = ContourExtractor('schema.jpg')
            extractor.load_image()
            extractor.preprocess_image()
            contours = extractor.extract_contours()
            parts = extractor.split_contours_into_parts()
            
            extractor.export_to_csv('schema_contours.csv')
            extractor.export_to_json('schema_contours.json')
            
            Пример 2: Использование CSV Drawer
            ────────────────────────────────
            from csv_drawer import CSVShapeDrawer
            
            drawer = CSVShapeDrawer(2000, 2000)
            drawer.load_vertices_csv('schema_vertices.csv')
            drawer.draw_shapes()
            drawer.save('result.jpg')
            """
        }
    }
    
    @staticmethod
    def print_header():
        """Печатает заголовок"""
        print("""
╔════════════════════════════════════════════════════════════════╗
║          🎯 Schematic Converter v2.0 - Quick Start            ║
║                  Быстрый старт за 7 шагов                    ║
╚════════════════════════════════════════════════════════════════╝
        """)
    
    @staticmethod
    def print_menu():
        """Печатает меню выбора"""
        print("\nВыберите тему для подробного объяснения:")
        print("─" * 50)
        for key, step in QuickStart.STEPS.items():
            print(f"  {key} - {step['title']}")
        print("  0 - Выход")
        print("  m - Меню")
        print("  a - Все (вывести все шаги)")
        print("─" * 50)
    
    @staticmethod
    def print_step(step_key):
        """Печатает информацию о шаге"""
        if step_key not in QuickStart.STEPS:
            print("❌ Неверный выбор")
            return
        
        step = QuickStart.STEPS[step_key]
        print(f"\n{'═' * 60}")
        print(f"  {step['title']}")
        print(f"{'═' * 60}")
        print(step['details'])
        print()
    
    @staticmethod
    def print_all_steps():
        """Печатает все шаги"""
        for key in sorted(QuickStart.STEPS.keys()):
            QuickStart.print_step(key)
            input("Нажмите Enter для продолжения...")
            print("\n")
    
    @staticmethod
    def run():
        """Запускает интерактивное меню"""
        QuickStart.print_header()
        
        while True:
            QuickStart.print_menu()
            choice = input("\nВыбор: ").strip()
            
            if choice == '0':
                print("\n👋 До свидания!")
                break
            elif choice == 'm':
                continue
            elif choice == 'a':
                QuickStart.print_all_steps()
            elif choice in QuickStart.STEPS:
                QuickStart.print_step(choice)
                input("Нажмите Enter для возврата в меню...")
            else:
                print("❌ Неверный выбор. Попробуйте еще раз.")


# Автоматическое отображение при импорте
if __name__ == '__main__':
    QuickStart.run()
