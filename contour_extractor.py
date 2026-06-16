#!/usr/bin/env python3
"""
Contour Extractor - Извлечение контуров из изображений
Экспортирует контуры с разделяемыми частями в CSV формат
"""

import cv2
import numpy as np
import csv
from pathlib import Path
from typing import List, Dict, Tuple
import json

def json_converter(obj):
    import numpy as np
    if isinstance(obj, np.integer): return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    return str(obj)


class ContourExtractor:
    """Класс для извлечения и анализа контуров из изображений"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image = None
        self.binary_image = None
        self.contours = []
        self.contour_parts = []
        
    def load_image(self) -> bool:
        """Загружает изображение"""
        try:
            self.image = cv2.imread(str(self.image_path))
            if self.image is None:
                return False
            return True
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            return False
    
    def preprocess_image(self, blur_kernel: int = 5, threshold_value: int = 150) -> np.ndarray:
        """Предварительная обработка изображения для выделения контуров"""
        # Конвертируем в оттенки серого
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # Применяем размытие Гаусса для удаления шума
        blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
        
        # Применяем адаптивную пороговую обработку для лучшего выделения деталей
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Закрытие (заполнение мелких дыр)
        kernel = cv2.getStructuringElement(cv2.MORPH_CLOSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Открытие (удаление мелкого шума)
        kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        
        self.binary_image = binary
        return binary
    
    def extract_contours(self, min_area: float = 50, max_area: float = None) -> List[Dict]:
        """Извлекает контуры из обработанного изображения"""
        if self.binary_image is None:
            raise ValueError("Сначала нужно обработать изображение (preprocess_image)")
        
        if max_area is None:
            max_area = self.binary_image.size
        
        contours, _ = cv2.findContours(
            self.binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        
        self.contours = []
        contour_id = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Фильтруем по площади
            if min_area <= area <= max_area:
                # Аппроксимируем контур
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Вычисляем характеристики контура
                perimeter = cv2.arcLength(contour, True)
                
                # Контур выпукл или нет
                hull = cv2.convexHull(contour)
                is_convex = cv2.isContourConvex(contour)
                
                # Момент для центра масс
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = 0, 0
                
                contour_dict = {
                    'id': contour_id,
                    'area': float(area),
                    'perimeter': float(perimeter),
                    'center': (int(cx), int(cy)),
                    'is_convex': bool(is_convex),
                    'vertices_count': len(approx),
                    'contour': contour.tolist(),
                    'approximation': approx.tolist(),
                    'hull': hull.tolist(),
                    'bounding_rect': None
                }
                
                # Добавляем bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                contour_dict['bounding_rect'] = {
                    'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)
                }
                
                self.contours.append(contour_dict)
                contour_id += 1
        
        return self.contours
    
    def split_contours_into_parts(self) -> List[Dict]:
        """Разделяет контуры на части (для сложных фигур)"""
        self.contour_parts = []
        part_id = 0
        
        for contour_data in self.contours:
            contour_id = contour_data['id']
            contour = np.array(contour_data['contour'], dtype=np.int32)
            
            # Проверяем, нужно ли разделять контур на части
            # Разделяем на основе разрывов в координатах
            segments = self._segment_contour(contour)
            
            if len(segments) > 1:
                # Контур состоит из нескольких отдельных частей
                for seg_idx, segment in enumerate(segments):
                    part_dict = {
                        'part_id': part_id,
                        'parent_contour_id': contour_id,
                        'segment_index': seg_idx,
                        'vertices': segment.tolist(),
                        'vertex_count': len(segment),
                        'centroid': self._calculate_centroid(segment),
                        'bounds': self._get_segment_bounds(segment)
                    }
                    self.contour_parts.append(part_dict)
                    part_id += 1
            else:
                # Контур - это одна часть
                part_dict = {
                    'part_id': part_id,
                    'parent_contour_id': contour_id,
                    'segment_index': 0,
                    'vertices': contour.tolist(),
                    'vertex_count': len(contour),
                    'centroid': self._calculate_centroid(contour),
                    'bounds': self._get_segment_bounds(contour)
                }
                self.contour_parts.append(part_dict)
                part_id += 1
        
        return self.contour_parts
    
    def _segment_contour(self, contour: np.ndarray, gap_threshold: int = 50) -> List[np.ndarray]:
        """Разделяет контур на части на основе разрывов"""
        if len(contour) < 2:
            return [contour]
        
        segments = []
        current_segment = [contour[0]]
        
        for i in range(1, len(contour)):
            point = contour[i]
            prev_point = contour[i - 1]
            
            # Вычисляем расстояние между точками
            distance = np.sqrt(
                (point[0][0] - prev_point[0][0])**2 + 
                (point[0][1] - prev_point[0][1])**2
            )
            
            if distance > gap_threshold:
                # Разрыв обнаружен
                if len(current_segment) > 1:
                    segments.append(np.array(current_segment))
                current_segment = [point]
            else:
                current_segment.append(point)
        
        # Добавляем последний сегмент
        if len(current_segment) > 1:
            segments.append(np.array(current_segment))
        
        return segments if segments else [contour]
    
    def _calculate_centroid(self, points: np.ndarray) -> Tuple[float, float]:
        """Вычисляет центроид набора точек"""
        if len(points) == 0:
            return (0, 0)
        
        points = np.array(points)
        if len(points.shape) == 3:  # если это контур OpenCV
            points = points.reshape(-1, 2)
        elif len(points.shape) == 2 and points.shape[1] == 1:
            points = points.reshape(-1, 2)
        
        centroid = np.mean(points, axis=0)
        return (float(centroid[0]), float(centroid[1]))
    
    def _get_segment_bounds(self, points: np.ndarray) -> Dict:
        """Получает границы для набора точек"""
        if len(points) == 0:
            return {'min_x': 0, 'min_y': 0, 'max_x': 0, 'max_y': 0}
        
        points = np.array(points)
        if len(points.shape) == 3:
            points = points.reshape(-1, 2)
        elif len(points.shape) == 2 and points.shape[1] == 1:
            points = points.reshape(-1, 2)
        
        return {
            'min_x': int(np.min(points[:, 0])),
            'min_y': int(np.min(points[:, 1])),
            'max_x': int(np.max(points[:, 0])),
            'max_y': int(np.max(points[:, 1]))
        }
    
    def export_to_csv(self, output_path: str, include_vertices: bool = True) -> bool:
        """Экспортирует контуры и их части в CSV формат"""
        try:
            output_path = Path(output_path)
            
            # Основной CSV с контурами
            contours_csv = output_path.parent / f"{output_path.stem}_contours.csv"
            # CSV с частями контуров
            parts_csv = output_path.parent / f"{output_path.stem}_parts.csv"
            # CSV с координатами вершин
            vertices_csv = output_path.parent / f"{output_path.stem}_vertices.csv"
            
            # Сохраняем основные контуры
            with open(contours_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f, fieldnames=[
                        'contour_id', 'area', 'perimeter', 'center_x', 'center_y',
                        'is_convex', 'vertices_count', 'bound_x', 'bound_y', 
                        'bound_width', 'bound_height'
                    ]
                )
                writer.writeheader()
                
                for contour in self.contours:
                    row = {
                        'contour_id': contour['id'],
                        'area': f"{contour['area']:.2f}",
                        'perimeter': f"{contour['perimeter']:.2f}",
                        'center_x': contour['center'][0],
                        'center_y': contour['center'][1],
                        'is_convex': 1 if contour['is_convex'] else 0,
                        'vertices_count': contour['vertices_count'],
                        'bound_x': contour['bounding_rect']['x'],
                        'bound_y': contour['bounding_rect']['y'],
                        'bound_width': contour['bounding_rect']['width'],
                        'bound_height': contour['bounding_rect']['height']
                    }
                    writer.writerow(row)
            
            # Сохраняем части контуров
            with open(parts_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f, fieldnames=[
                        'part_id', 'parent_contour_id', 'segment_index',
                        'vertex_count', 'centroid_x', 'centroid_y',
                        'min_x', 'min_y', 'max_x', 'max_y'
                    ]
                )
                writer.writeheader()
                
                for part in self.contour_parts:
                    row = {
                        'part_id': part['part_id'],
                        'parent_contour_id': part['parent_contour_id'],
                        'segment_index': part['segment_index'],
                        'vertex_count': part['vertex_count'],
                        'centroid_x': f"{part['centroid'][0]:.2f}",
                        'centroid_y': f"{part['centroid'][1]:.2f}",
                        'min_x': part['bounds']['min_x'],
                        'min_y': part['bounds']['min_y'],
                        'max_x': part['bounds']['max_x'],
                        'max_y': part['bounds']['max_y']
                    }
                    writer.writerow(row)
            
            # Сохраняем вершины (если требуется)
            if include_vertices:
                with open(vertices_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(
                        f, fieldnames=['part_id', 'vertex_index', 'x', 'y']
                    )
                    writer.writeheader()
                    
                    for part in self.contour_parts:
                        vertices = part['vertices']
                        for idx, vertex in enumerate(vertices):
                            if isinstance(vertex, list) and len(vertex) > 0:
                                x, y = vertex[0] if isinstance(vertex[0], list) else (vertex[0], vertex[1] if len(vertex) > 1 else 0)
                            else:
                                x, y = vertex, 0
                            
                            row = {
                                'part_id': part['part_id'],
                                'vertex_index': idx,
                                'x': x,
                                'y': y
                            }
                            writer.writerow(row)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при экспорте CSV: {e}")
            return False
    
    def export_to_json(self, output_path: str) -> bool:
        """Экспортирует контуры в JSON для ручной обработки"""
        try:
            output_path = Path(output_path)
            
            data = {
                'contours': self.contours,
                'contour_parts': self.contour_parts,
                'metadata': {
                    'total_contours': len(self.contours),
                    'total_parts': len(self.contour_parts),
                    'image_source': str(self.image_path),
                    'image_shape': self.image.shape if self.image is not None else None
                }
            }
            
            json_path = output_path.parent / f"{output_path.stem}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=json_converter)
            
            return True
        
        except Exception as e:
            print(f"Ошибка при экспорте JSON: {e}")
            return False
    
    def visualize_contours(self, output_path: str) -> bool:
        """Создает визуализацию контуров для проверки"""
        try:
            if self.image is None:
                return False
            
            visualization = self.image.copy()
            
            # Рисуем контуры разными цветами
            for i, contour_data in enumerate(self.contours):
                contour = np.array(contour_data['contour'], dtype=np.int32)
                # Генерируем цвет на основе ID
                color = (
                    (i * 73) % 256,
                    (i * 137) % 256,
                    (i * 195) % 256
                )
                cv2.drawContours(visualization, [contour], 0, color, 2)
                
                # Добавляем ID контура
                cx, cy = contour_data['center']
                cv2.putText(
                    visualization, str(contour_data['id']),
                    (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
                )
            
            # Рисуем части контуров точками
            for part in self.contour_parts:
                centroid = part['centroid']
                cv2.circle(
                    visualization, 
                    (int(centroid[0]), int(centroid[1])),
                    3, (0, 255, 255), -1
                )
            
            cv2.imwrite(str(output_path), visualization)
            return True
        
        except Exception as e:
            print(f"Ошибка при визуализации: {e}")
            return False


if __name__ == '__main__':
    # Пример использования
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python contour_extractor.py <путь_к_изображению>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    extractor = ContourExtractor(image_path)
    
    if not extractor.load_image():
        print(f"Ошибка: не удалось загрузить изображение {image_path}")
        sys.exit(1)
    
    print("Обработка изображения...")
    extractor.preprocess_image()
    
    print("Извлечение контуров...")
    contours = extractor.extract_contours()
    print(f"Найдено контуров: {len(contours)}")
    
    print("Разделение контуров на части...")
    parts = extractor.split_contours_into_parts()
    print(f"Найдено частей: {len(parts)}")
    
    output_stem = Path(image_path).stem
    
    print(f"Экспорт в CSV...")
    extractor.export_to_csv(f"{output_stem}_contours.csv")
    
    print(f"Экспорт в JSON...")
    extractor.export_to_json(f"{output_stem}_contours.json")
    
    print(f"Визуализация контуров...")
    extractor.visualize_contours(f"{output_stem}_visualization.jpg")
    
    print("✓ Готово!")
