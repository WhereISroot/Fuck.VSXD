#!/usr/bin/env python3
"""
Example: Draw shapes from CSV output
Пример: Рисование фигур из CSV выходных файлов
"""

import csv
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


class CSVShapeDrawer:
    """Класс для рисования фигур на основе CSV данных контуров"""
    
    def __init__(self, width: int = 2000, height: int = 2000, bg_color=(255, 255, 255)):
        """
        Инициализация
        
        Args:
            width: ширина изображения
            height: высота изображения
            bg_color: цвет фона (BGR)
        """
        self.image = np.full((height, width, 3), bg_color, dtype=np.uint8)
        self.shapes = {}
        self.contour_info = {}
        
    def load_vertices_csv(self, csv_path: str) -> bool:
        """
        Загружает координаты вершин из CSV
        
        Args:
            csv_path: путь к файлу vertices CSV
        """
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    part_id = int(row['part_id'])
                    vertex_index = int(row['vertex_index'])
                    x = float(row['x'])
                    y = float(row['y'])
                    
                    if part_id not in self.shapes:
                        self.shapes[part_id] = {}
                    
                    self.shapes[part_id][vertex_index] = (int(x), int(y))
            
            return True
        except Exception as e:
            print(f"Ошибка загрузки CSV: {e}")
            return False
    
    def load_contours_csv(self, csv_path: str) -> bool:
        """
        Загружает информацию о контурах из CSV
        
        Args:
            csv_path: путь к файлу contours CSV
        """
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    contour_id = int(row['contour_id'])
                    self.contour_info[contour_id] = {
                        'area': float(row['area']),
                        'perimeter': float(row['perimeter']),
                        'center': (int(row['center_x']), int(row['center_y'])),
                        'is_convex': int(row['is_convex']),
                        'vertices_count': int(row['vertices_count'])
                    }
            return True
        except Exception as e:
            print(f"Ошибка загрузки contours CSV: {e}")
            return False
    
    def draw_shapes(self, 
                   line_color=(0, 0, 255), 
                   line_thickness=2,
                   fill_color=None,
                   draw_vertices=True,
                   vertex_color=(0, 255, 0),
                   vertex_radius=3) -> bool:
        """
        Рисует все загруженные фигуры
        
        Args:
            line_color: цвет линий (BGR)
            line_thickness: толщина линий
            fill_color: цвет заполнения (None = без заполнения)
            draw_vertices: рисовать ли вершины
            vertex_color: цвет вершин
            vertex_radius: радиус вершин
        """
        try:
            for part_id in sorted(self.shapes.keys()):
                vertices = self.shapes[part_id]
                
                if not vertices:
                    continue
                
                # Сортируем вершины по индексу и преобразуем в список точек
                sorted_vertices = [vertices[i] for i in sorted(vertices.keys())]
                points = np.array(sorted_vertices, dtype=np.int32)
                
                # Рисуем полигон
                if fill_color:
                    cv2.fillPoly(self.image, [points], fill_color)
                else:
                    cv2.polylines(self.image, [points], True, line_color, line_thickness)
                
                # Рисуем вершины
                if draw_vertices:
                    for point in sorted_vertices:
                        cv2.circle(self.image, tuple(point), vertex_radius, 
                                 vertex_color, -1)
                
                # Добавляем ID части
                if len(sorted_vertices) > 0:
                    center = np.mean(sorted_vertices, axis=0).astype(int)
                    cv2.putText(self.image, f"P{part_id}", tuple(center),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
            
            return True
        except Exception as e:
            print(f"Ошибка при рисовании: {e}")
            return False
    
    def draw_contour_info(self, contour_id: int, pos: Tuple[int, int]):
        """
        Добавляет информацию о контуре на изображение
        
        Args:
            contour_id: ID контура
            pos: позиция текста (x, y)
        """
        if contour_id not in self.contour_info:
            return
        
        info = self.contour_info[contour_id]
        x, y = pos
        
        text = f"ID:{contour_id} Area:{info['area']:.0f}"
        cv2.putText(self.image, text, (x, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    def add_grid(self, spacing: int = 100, color=(200, 200, 200), thickness=1):
        """
        Добавляет сетку на изображение для справки
        
        Args:
            spacing: расстояние между линиями сетки
            color: цвет сетки (BGR)
            thickness: толщина линий сетки
        """
        height, width = self.image.shape[:2]
        
        # Вертикальные линии
        for x in range(0, width, spacing):
            cv2.line(self.image, (x, 0), (x, height), color, thickness)
        
        # Горизонтальные линии
        for y in range(0, height, spacing):
            cv2.line(self.image, (0, y), (width, y), color, thickness)
    
    def save(self, output_path: str) -> bool:
        """
        Сохраняет результат в файл
        
        Args:
            output_path: путь для сохранения
        """
        try:
            cv2.imwrite(output_path, self.image)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False
    
    def show(self, window_name="Drawing"):
        """Показывает изображение"""
        cv2.imshow(window_name, self.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def example_usage():
    """Пример использования"""
    print("""
    📚 Примеры использования CSVShapeDrawer:
    
    # Пример 1: Рисование из CSV
    drawer = CSVShapeDrawer(2000, 2000)
    drawer.load_vertices_csv('schema_vertices.csv')
    drawer.load_contours_csv('schema_contours.csv')
    drawer.add_grid(spacing=100)
    drawer.draw_shapes(line_color=(0, 0, 255), line_thickness=2)
    drawer.save('result.jpg')
    
    # Пример 2: С заполнением цветом
    drawer = CSVShapeDrawer(2000, 2000)
    drawer.load_vertices_csv('schema_vertices.csv')
    drawer.draw_shapes(
        fill_color=(200, 200, 255),
        line_color=(0, 0, 255),
        line_thickness=1
    )
    drawer.save('result_filled.jpg')
    
    # Пример 3: Без вершин
    drawer = CSVShapeDrawer(2000, 2000)
    drawer.load_vertices_csv('schema_vertices.csv')
    drawer.draw_shapes(draw_vertices=False)
    drawer.save('result_simple.jpg')
    """)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        example_usage()
        print("\nУспользование:")
        print("python csv_drawer.py <vertices.csv> <output.jpg>")
        sys.exit(0)
    
    vertices_csv = sys.argv[1]
    output_image = sys.argv[2]
    
    # Проверяем файлы
    if not Path(vertices_csv).exists():
        print(f"❌ Файл не найден: {vertices_csv}")
        sys.exit(1)
    
    print(f"📂 Загружаю CSV: {vertices_csv}")
    
    # Создаем drawer
    drawer = CSVShapeDrawer(2000, 2000)
    
    # Загружаем данные
    if not drawer.load_vertices_csv(vertices_csv):
        print("❌ Ошибка загрузки CSV")
        sys.exit(1)
    
    print(f"✓ Загружено фигур: {len(drawer.shapes)}")
    
    # Рисуем
    print("🎨 Рисование...")
    drawer.add_grid(spacing=100)
    drawer.draw_shapes(
        line_color=(0, 0, 255),
        line_thickness=2,
        draw_vertices=True,
        vertex_color=(0, 255, 0)
    )
    
    # Сохраняем
    print(f"💾 Сохранение в {output_image}...")
    if drawer.save(output_image):
        print(f"✅ Готово! Результат: {output_image}")
    else:
        print("❌ Ошибка сохранения")
        sys.exit(1)
