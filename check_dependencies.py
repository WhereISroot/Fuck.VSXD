#!/usr/bin/env python3
"""
Проверка всех зависимостей перед запуском
"""

import sys
import subprocess
from pathlib import Path

class DependencyChecker:
    def __init__(self):
        self.python_modules = {
            'cv2': 'opencv-python',
            'PyQt5': 'PyQt5',
            'PIL': 'Pillow',
            'numpy': 'numpy',
            'scipy': 'scipy',
            'pytesseract': 'pytesseract',
        }
        self.system_programs = {
            'tesseract': 'Tesseract OCR (опционально)',
        }
        self.results = []
    
    def check_all(self):
        """Проверить все зависимости"""
        print("╔════════════════════════════════════════════════════════╗")
        print("║   Проверка зависимостей для Schematic Converter       ║")
        print("╚════════════════════════════════════════════════════════╝")
        print()
        
        # Проверка Python версии
        self._check_python_version()
        
        # Проверка Python модулей
        print("📦 Проверка Python модулей:")
        print("-" * 50)
        for module, package_name in self.python_modules.items():
            self._check_python_module(module, package_name)
        
        print()
        
        # Проверка системных программ
        print("🔧 Проверка системных программ:")
        print("-" * 50)
        for program, description in self.system_programs.items():
            self._check_system_program(program, description)
        
        print()
        print("=" * 50)
        self._print_summary()
    
    def _check_python_version(self):
        """Проверка версии Python"""
        print(f"🐍 Python версия: {sys.version.split()[0]}")
        
        major, minor = sys.version_info[:2]
        if major >= 3 and minor >= 7:
            print("   ✅ Поддерживаемая версия!")
        else:
            print("   ❌ Нужна Python 3.7 или выше!")
            self.results.append(False)
        
        print()
    
    def _check_python_module(self, module, package_name):
        """Проверка Python модуля"""
        try:
            __import__(module)
            # Получить версию
            mod = sys.modules[module]
            version = getattr(mod, '__version__', 'unknown')
            print(f"  ✅ {module:20} (v{version})")
            self.results.append(True)
        except ImportError:
            print(f"  ❌ {module:20} НЕ УСТАНОВЛЕН!")
            print(f"     Установите: pip install {package_name}")
            self.results.append(False)
    
    def _check_system_program(self, program, description):
        """Проверка системной программы"""
        result = subprocess.run(
            ['which', program],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✅ {program:20} ({description})")
        else:
            print(f"  ⚠️  {program:20} НЕ НАЙДЕН ({description})")
            if program == 'tesseract':
                print(f"     На Arch: sudo pacman -S tesseract")
                print(f"     На Ubuntu: sudo apt-get install tesseract-ocr")
    
    def _print_summary(self):
        """Вывести итоговый отчёт"""
        total = len(self.results)
        passed = sum(self.results)
        failed = total - passed
        
        print(f"✅ Успешно: {passed}/{total}")
        
        if failed == 0:
            print("🎉 ВСЕ ЗАВИСИМОСТИ УСТАНОВЛЕНЫ!")
            print()
            print("Для запуска программы используйте:")
            print("  python3 schematic_converter.py")
            print()
            return 0
        else:
            print(f"❌ Ошибок: {failed}/{total}")
            print()
            print("Установите отсутствующие зависимости:")
            if any(not r for r in self.results[:len(self.python_modules)]):
                print("  pip install -r requirements.txt")
            print()
            return 1


def main():
    checker = DependencyChecker()
    exit_code = checker.check_all()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
