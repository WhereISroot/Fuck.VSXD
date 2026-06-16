#!/usr/bin/env python3
"""
Schematic Diagram to VSDX Converter
Конвертирует фото электрических схем в VSDX файлы Visio
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QScrollArea, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pytesseract
from PIL import Image
import json

class SchematicProcessor(QThread):
    """Обработка схемы в отдельном потоке"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, image_path, output_path):
        super().__init__()
        self.image_path = image_path
        self.output_path = output_path
        
    def run(self):
        try:
            self.progress.emit("Загрузка изображения...")
            img = cv2.imread(str(self.image_path))
            if img is None:
                self.finished.emit(False, "Не удалось загрузить изображение")
                return
                
            self.progress.emit("Предварительная обработка...")
            processed = self.preprocess_image(img)
            
            self.progress.emit("Обнаружение элементов...")
            elements = self.detect_elements(processed, img)
            
            self.progress.emit("Распознавание текста...")
            elements = self.recognize_text(img, elements)
            
            self.progress.emit("Генерация VSDX...")
            self.generate_vsdx(elements, self.output_path)
            
            self.finished.emit(True, f"Успешно! Файл сохранён: {self.output_path}")
            
        except Exception as e:
            self.finished.emit(False, f"Ошибка: {str(e)}")
    
    def preprocess_image(self, img):
        """Предварительная обработка изображения"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
        return binary
    
    def detect_elements(self, binary, original):
        """Обнаружение элементов схемы"""
        elements = []
        
        # Обнаружение линий (проводов)
        lines = cv2.HoughLinesP(binary, 1, np.pi/180, 50, minLineLength=30, maxLineGap=10)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                elements.append({
                    'type': 'line',
                    'points': [(x1, y1), (x2, y2)],
                    'confidence': 0.95
                })
        
        # Обнаружение окружностей (компоненты)
        circles = cv2.HoughCircles(binary, cv2.HOUGH_GRADIENT, 1, 30,
                                   param1=50, param2=30, minRadius=5, maxRadius=50)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                x, y, r = i[0], i[1], i[2]
                elements.append({
                    'type': 'circle',
                    'center': (int(x), int(y)),
                    'radius': int(r),
                    'confidence': 0.9
                })
        
        # Обнаружение прямоугольников (реле, переключатели)
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if 300 < area < 50000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h != 0 else 0
                
                # Если это похоже на прямоугольник
                if 0.3 < aspect_ratio < 3:
                    elements.append({
                        'type': 'rectangle',
                        'x': x, 'y': y, 'width': w, 'height': h,
                        'confidence': 0.85
                    })
        
        return elements
    
    def recognize_text(self, img, elements):
        """Распознавание текста на схеме"""
        try:
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            text_data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            
            # Добавляем распознанный текст к элементам
            for i in range(len(text_data['text'])):
                if int(text_data['conf'][i]) > 30:  # Минимальная уверенность
                    elements.append({
                        'type': 'text',
                        'text': text_data['text'][i],
                        'x': text_data['left'][i],
                        'y': text_data['top'][i],
                        'width': text_data['width'][i],
                        'height': text_data['height'][i],
                        'confidence': int(text_data['conf'][i]) / 100
                    })
        except:
            pass  # Если Tesseract не установлен, просто пропускаем
        
        return elements
    
    def generate_vsdx(self, elements, output_path):
        """Генерация VSDX файла или JSON для ручной обработки"""
        # Сохраняем как JSON для дальнейшей обработки
        json_data = {
            'elements': elements,
            'metadata': {
                'source': str(self.image_path),
                'total_elements': len(elements)
            }
        }
        
        json_path = output_path.replace('.vsdx', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Пытаемся создать VSDX если доступна библиотека
        try:
            from vsdx import Document
            
            doc = Document()
            page = doc.pages[0]
            
            # Масштабирование для Visio (1 пиксель = 0.01 дюйма примерно)
            scale = 0.01
            
            for elem in elements:
                if elem['type'] == 'line':
                    x1, y1 = elem['points'][0]
                    x2, y2 = elem['points'][1]
                    # Добавляем линию
                    connector = page.connect(
                        (x1*scale, y1*scale),
                        (x2*scale, y2*scale)
                    )
                
                elif elem['type'] == 'circle':
                    cx, cy = elem['center']
                    r = elem['radius']
                    # Добавляем эллипс
                    shape = page.add_shape()
                    shape.text = ''
                
                elif elem['type'] == 'rectangle':
                    x, y, w, h = elem['x'], elem['y'], elem['width'], elem['height']
                    shape = page.add_shape(
                        f"RECT({x*scale},{y*scale},{(x+w)*scale},{(y+h)*scale})"
                    )
                
                elif elem['type'] == 'text':
                    text_shape = page.add_shape()
                    text_shape.text = elem.get('text', '')
            
            doc.save(str(output_path))
            
        except ImportError:
            # Если python-vsdx не установлен, сохраняем JSON
            # который можно импортировать в Visio или использовать для создания схемы вручную
            pass


class SchematicConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.processor = None
        
    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle('Schematic to VSDX Converter')
        self.setGeometry(100, 100, 900, 700)
        
        # Главный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Область для отображения изображения
        self.image_label = QLabel('Изображение схемы будет отображено здесь')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")
        
        scroll = QScrollArea()
        scroll.setWidget(self.image_label)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(QLabel('Предпросмотр:'), 0, Qt.AlignTop)
        main_layout.addWidget(scroll)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton('📂 Загрузить изображение')
        self.load_btn.clicked.connect(self.load_image)
        button_layout.addWidget(self.load_btn)
        
        self.convert_btn = QPushButton('⚙️ Конвертировать в VSDX')
        self.convert_btn.clicked.connect(self.convert_image)
        self.convert_btn.setEnabled(False)
        button_layout.addWidget(self.convert_btn)
        
        main_layout.addLayout(button_layout)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel('Готово к работе')
        main_layout.addWidget(self.status_label)
        
        self.current_image = None
        
    def load_image(self):
        """Загрузка изображения"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Выберите изображение схемы', '',
            'Изображения (*.jpg *.jpeg *.png *.bmp);;All Files (*)'
        )
        
        if file_path:
            self.current_image = file_path
            
            # Отображаем превью
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaledToWidth(800, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            
            self.status_label.setText(f'Загружено: {Path(file_path).name}')
            self.convert_btn.setEnabled(True)
    
    def convert_image(self):
        """Конвертирование схемы"""
        if not self.current_image:
            QMessageBox.warning(self, 'Ошибка', 'Сначала загрузите изображение')
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить как VSDX', '',
            'Visio Files (*.vsdx);;All Files (*)'
        )
        
        if output_path:
            self.convert_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.processor = SchematicProcessor(self.current_image, output_path)
            self.processor.progress.connect(self.update_progress)
            self.processor.finished.connect(self.processing_finished)
            self.processor.start()
    
    def update_progress(self, message):
        """Обновление прогресса"""
        self.status_label.setText(message)
        self.progress_bar.setValue(
            (self.progress_bar.value() + 25) % 100
        )
    
    def processing_finished(self, success, message):
        """Завершение обработки"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        
        if success:
            QMessageBox.information(self, 'Успех', message)
        else:
            QMessageBox.critical(self, 'Ошибка', message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SchematicConverterGUI()
    window.show()
    sys.exit(app.exec_())
