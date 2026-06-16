# Fuck VSDX - Updated Version (с CSV Экспортом)

## 🎯 Основное назначение

Преобразование фотографий электрических схем в:
- **CSV файлы** с обнаруженными контурами и отдельными частями (совместимо с Microsoft Drawing)
- **VSDX файлы** для Microsoft Visio
- **JSON данные** для ручной обработки
- **Визуализацию** для проверки качества обработки

## ✨ Новые возможности (v2.0)

### CSV Экспорт Контуров
Программа теперь автоматически:

1. **Детектирует контуры** на изображении
2. **Разделяет их на отдельные части** (для сложных фигур)
3. **Экспортирует в три CSV файла**:
   - `*_contours.csv` - основные контуры с параметрами
   - `*_parts.csv` - отдельные части контуров
   - `*_vertices.csv` - координаты всех вершин

4. **Экспортирует в JSON** для структурированного доступа к данным
5. **Генерирует визуализацию** контуров для проверки

## 📋 Быстрый старт

### Для Arch Linux

```bash
# 1. Делаем скрипт исполняемым
chmod +x install_arch.sh

# 2. Запускаем установку
./install_arch.sh

# 3. Запускаем программу
python3 schematic_converter.py
```

### Для Windows

```batch
# Установка зависимостей
pip install -r requirements.txt

# Запуск программы
python schematic_converter.py
```

### Для macOS

```bash
# Установка Tesseract (если еще не установлен)
brew install tesseract

# Установка зависимостей
pip install -r requirements.txt

# Запуск программы
python3 schematic_converter.py
```

## 🖥️ Как использовать интерфейс

1. **Запустите программу**
   ```bash
   python3 schematic_converter.py
   ```

2. **Откроется окно с двумя вкладками:**
   - "Конвертер" - основная работа
   - "Справка" - документация

3. **На вкладке "Конвертер":**
   - Нажмите "📂 Загрузить изображение"
   - Выберите изображение схемы (JPG, PNG, BMP)
   - Выберите форматы экспорта (CSV и/или VSDX)
   - Нажмите "⚙️ Конвертировать"
   - Выберите место сохранения файла
   - Дождитесь завершения обработки

## 📁 Выходные файлы

После обработки будут созданы:

### CSV файлы (для Microsoft Drawing)

**`*_contours.csv`** - Основные контуры
```
contour_id,area,perimeter,center_x,center_y,is_convex,vertices_count,bound_x,bound_y,bound_width,bound_height
0,1234.56,156.78,245,189,1,8,200,150,90,78
```

**`*_parts.csv`** - Отдельные части контуров
```
part_id,parent_contour_id,segment_index,vertex_count,centroid_x,centroid_y,min_x,min_y,max_x,max_y
0,0,0,8,245.50,189.25,200,150,290,228
```

**`*_vertices.csv`** - Координаты вершин (для точной реконструкции)
```
part_id,vertex_index,x,y
0,0,200,150
0,1,210,155
0,2,220,160
...
```

### JSON файл

**`*_contours.json`** - Полные данные в структурированном формате
```json
{
  "contours": [
    {
      "id": 0,
      "area": 1234.56,
      "perimeter": 156.78,
      "center": [245, 189],
      "is_convex": true,
      "vertices_count": 8,
      "contour": [...],
      "approximation": [...],
      "bounding_rect": {...}
    }
  ],
  "contour_parts": [...],
  "metadata": {...}
}
```

### Визуализация

**`*_visualization.jpg`** - Изображение с нарисованными контурами
- Разные контуры отмечены разными цветами
- Каждый контур подписан его ID
- Центроиды частей показаны жёлтыми точками

### VSDX файл

**`*.vsdx`** - Файл Microsoft Visio (если выбран экспорт)

## 🔧 Использование CSV в Microsoft Drawing

### Способ 1: Импорт координат вершин

1. Откройте Microsoft Drawing
2. Используйте `*_vertices.csv` для восстановления фигур
3. Скрипт ниже поможет конвертировать CSV в Drawing:

```python
import csv
from pathlib import Path

def csv_to_drawing(csv_path):
    """Конвертирует CSV в координаты для Drawing"""
    shapes = {}
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            part_id = int(row['part_id'])
            x = float(row['x'])
            y = float(row['y'])
            
            if part_id not in shapes:
                shapes[part_id] = []
            shapes[part_id].append((x, y))
    
    return shapes
```

### Способ 2: Использование Python для рисования

```python
from PIL import Image, ImageDraw
import csv

def draw_from_csv(csv_path, output_image):
    """Рисует фигуры из CSV в изображение"""
    img = Image.new('RGB', (2000, 2000), 'white')
    draw = ImageDraw.Draw(img)
    
    shapes = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            part_id = int(row['part_id'])
            x, y = int(row['x']), int(row['y'])
            if part_id not in shapes:
                shapes[part_id] = []
            shapes[part_id].append((x, y))
    
    for points in shapes.values():
        if len(points) > 1:
            draw.polygon(points, outline='black', fill=None)
    
    img.save(output_image)
```

## 🎓 Примеры использования

### Пример 1: Базовое использование

```python
from contour_extractor import ContourExtractor

# Загружаем изображение
extractor = ContourExtractor('schema.jpg')
extractor.load_image()

# Обрабатываем
extractor.preprocess_image()
contours = extractor.extract_contours()
parts = extractor.split_contours_into_parts()

# Экспортируем
extractor.export_to_csv('schema_contours.csv')
extractor.export_to_json('schema_contours.json')
extractor.visualize_contours('schema_viz.jpg')
```

### Пример 2: Использование из командной строки

```bash
python contour_extractor.py /path/to/schema.jpg
```

Создаст:
- `schema_contours.csv`
- `schema_parts.csv`
- `schema_vertices.csv`
- `schema_contours.json`
- `schema_visualization.jpg`

## 🔍 Параметры настройки

### В файле `contour_extractor.py`:

```python
# Минимальная площадь контура (пиксели²)
extractor.extract_contours(min_area=50)

# Максимальный разрыв для разделения (пиксели)
extractor._segment_contour(contour, gap_threshold=50)

# Фильтрация контуров по размеру
extractor.extract_contours(min_area=50, max_area=50000)
```

## 📊 Структура контуров

Каждый контур содержит:

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | int | Уникальный идентификатор контура |
| `area` | float | Площадь контура (пиксели²) |
| `perimeter` | float | Периметр контура (пиксели) |
| `center` | tuple | Координаты центра (x, y) |
| `is_convex` | bool | Является ли контур выпуклым |
| `vertices_count` | int | Количество вершин |
| `bounding_rect` | dict | Ограничивающий прямоугольник |

## ⚠️ Требования к изображениям

Для лучших результатов:

1. **Контрастность**: Хороший контраст между схемой и фоном
2. **Разрешение**: Минимум 500x500 пикселей
3. **Резкость**: Четкие, нечёткие изображения дают плохие результаты
4. **Освещение**: Равномерное освещение без теней
5. **Формат**: JPG, PNG, BMP

## 🐛 Решение проблем

### "Ошибка: Tesseract не установлен"

```bash
# Arch Linux
sudo pacman -S tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Скачайте установщик с https://github.com/UB-Mannheim/tesseract/wiki
```

### "Контуры не найдены"

- Проверьте контрастность изображения
- Попробуйте другое изображение с лучшим контрастом
- Используйте визуализацию для проверки обработки

### "VSDX экспорт не работает"

- Убедитесь, что установлена библиотека: `pip install python-vsdx`
- CSV экспорт будет работать даже без VSDX

## 📝 Лицензия

MIT License - используйте свободно!

## 👨‍💻 Версия

**v2.0** - с полноценным CSV экспортом и разделением контуров на части

## 🤝 Контрибьютинг

Если найдете баги или есть идеи - добро пожаловать в issue!

---

**Made with ❤️ for schematic diagram processing**
