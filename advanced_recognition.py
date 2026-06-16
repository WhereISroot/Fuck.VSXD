#!/usr/bin/env python3
"""
Продвинутое распознавание элементов электрических схем
Использует шаблоны и обучение для лучшего распознавания компонентов
"""

import cv2
import numpy as np
from scipy import ndimage
from collections import defaultdict

class ElectricalSchematicRecognizer:
    """Распознавание элементов электрических схем"""
    
    # Словарь компонентов электрических схем
    COMPONENTS = {
        'resistor': 'Резистор',
        'capacitor': 'Конденсатор',
        'inductor': 'Катушка индуктивности',
        'diode': 'Диод',
        'transistor': 'Транзистор',
        'switch': 'Переключатель',
        'relay': 'Реле',
        'led': 'Светодиод',
        'battery': 'Батарея',
        'motor': 'Двигатель',
        'transformer': 'Трансформатор',
        'ground': 'Заземление',
    }
    
    def __init__(self):
        self.binary = None
        self.original = None
        self.elements = []
        self.junctions = []
        
    def process(self, image_path):
        """Полная обработка изображения схемы"""
        self.original = cv2.imread(image_path)
        if self.original is None:
            raise ValueError(f"Не удалось загрузить: {image_path}")
        
        # Предварительная обработка
        self._preprocess()
        
        # Обнаружение элементов
        self._detect_wires()
        self._detect_components()
        self._detect_junctions()
        self._extract_text()
        
        return self.elements
    
    def _preprocess(self):
        """Предварительная обработка изображения"""
        # Конвертируем в серое изображение
        gray = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)
        
        # Эквализация гистограммы для улучшения контраста
        gray = cv2.equalizeHist(gray)
        
        # Размытие для удаления шума
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Бинаризация
        _, self.binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Морфологические операции
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        self.binary = cv2.morphologyEx(self.binary, cv2.MORPH_CLOSE, kernel)
        self.binary = cv2.morphologyEx(self.binary, cv2.MORPH_OPEN, kernel)
    
    def _detect_wires(self):
        """Обнаружение проводов (линий)"""
        # Используем HoughLines для обнаружения длинных прямых линий
        lines = cv2.HoughLinesP(
            self.binary,
            rho=1,
            theta=np.pi/180,
            threshold=50,
            minLineLength=30,
            maxLineGap=15
        )
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Фильтруем очень короткие линии
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                if length > 20:
                    self.elements.append({
                        'type': 'wire',
                        'subtype': 'straight',
                        'points': [(x1, y1), (x2, y2)],
                        'length': float(length),
                        'angle': np.degrees(np.arctan2(y2-y1, x2-x1)),
                        'confidence': 0.95
                    })
    
    def _detect_components(self):
        """Обнаружение компонентов схемы"""
        contours, _ = cv2.findContours(
            self.binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Пропускаем очень маленькие и очень большие контуры
            if area < 100 or area > 100000:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h if h != 0 else 0
            
            # Аппроксимируем контур
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            component_type, confidence = self._classify_component(
                approx, aspect_ratio, area, w, h
            )
            
            if confidence > 0.5:
                self.elements.append({
                    'type': 'component',
                    'subtype': component_type,
                    'bbox': (x, y, w, h),
                    'area': float(area),
                    'aspect_ratio': float(aspect_ratio),
                    'confidence': float(confidence)
                })
    
    def _classify_component(self, contour, aspect_ratio, area, w, h):
        """Классификация компонента по его форме"""
        vertices = len(contour)
        solidity = self._calculate_solidity(contour)
        circularity = self._calculate_circularity(contour, area)
        
        # Кольцо или круг - может быть источник питания
        if circularity > 0.8 and area < 5000:
            return ('circle', 0.85)
        
        # Прямоугольник - переключатель, реле
        if 0.2 < aspect_ratio < 5 and solidity > 0.8 and vertices < 10:
            if aspect_ratio > 2 or aspect_ratio < 0.5:
                return ('rectangle_elongated', 0.75)
            else:
                return ('rectangle_square', 0.8)
        
        # Треугольник - может быть диод
        if vertices == 3:
            return ('triangle', 0.7)
        
        # Волнистая форма - резистор
        if vertices > 6 and solidity < 0.7:
            return ('resistor', 0.65)
        
        # По умолчанию
        return ('unknown', 0.4)
    
    def _calculate_solidity(self, contour):
        """Вычисление плотности контура"""
        area = cv2.contourArea(contour)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        return float(area) / hull_area if hull_area > 0 else 0
    
    def _calculate_circularity(self, contour, area):
        """Вычисление циркулярности контура"""
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return 0
        circularity = 4 * np.pi * area / (perimeter ** 2)
        return min(circularity, 1.0)
    
    def _detect_junctions(self):
        """Обнаружение узлов (точек соединения проводов)"""
        # Используем морфологические операции для поиска узлов
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(self.binary, kernel, iterations=2)
        
        # Находим области пересечения
        intersections = cv2.HoughCircles(
            dilated,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=30,
            minRadius=2,
            maxRadius=15
        )
        
        if intersections is not None:
            for i in intersections[0]:
                x, y, r = int(i[0]), int(i[1]), int(i[2])
                self.junctions.append({
                    'position': (x, y),
                    'radius': r
                })
    
    def _extract_text(self):
        """Извлечение текста из изображения"""
        try:
            import pytesseract
            from PIL import Image
            
            # Используем только верхнюю половину изображения для меньшего шума
            h = self.original.shape[0]
            
            # Распознаём текст
            pil_img = Image.fromarray(cv2.cvtColor(self.original, cv2.COLOR_BGR2RGB))
            text_data = pytesseract.image_to_data(
                pil_img, output_type=pytesseract.Output.DICT
            )
            
            # Добавляем распознанный текст
            for i in range(len(text_data['text'])):
                confidence = int(text_data['conf'][i]) / 100
                
                if confidence > 0.3 and text_data['text'][i].strip():
                    self.elements.append({
                        'type': 'text',
                        'content': text_data['text'][i],
                        'bbox': (
                            text_data['left'][i],
                            text_data['top'][i],
                            text_data['width'][i],
                            text_data['height'][i]
                        ),
                        'confidence': float(confidence)
                    })
        except ImportError:
            # Tesseract не установлен
            pass
    
    def get_statistics(self):
        """Получение статистики распознавания"""
        stats = {
            'total_elements': len(self.elements),
            'wires': len([e for e in self.elements if e['type'] == 'wire']),
            'components': len([e for e in self.elements if e['type'] == 'component']),
            'text': len([e for e in self.elements if e['type'] == 'text']),
            'junctions': len(self.junctions),
            'confidence': np.mean([e.get('confidence', 0) for e in self.elements])
        }
        return stats


# Тестирование
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        recognizer = ElectricalSchematicRecognizer()
        elements = recognizer.process(sys.argv[1])
        stats = recognizer.get_statistics()
        
        print("\n📊 Статистика распознавания:")
        print(f"  Всего элементов: {stats['total_elements']}")
        print(f"  Проводов: {stats['wires']}")
        print(f"  Компонентов: {stats['components']}")
        print(f"  Текста: {stats['text']}")
        print(f"  Узлов: {stats['junctions']}")
        print(f"  Среднее качество: {stats['confidence']:.1%}")
    else:
        print("Использование: python3 advanced_recognition.py <image_path>")
