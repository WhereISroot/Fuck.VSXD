#!/usr/bin/env python3

"""
Schematic Diagram to VSDX Converter + CSV Contour Export
Конвертирует фото электрических схем в VSDX файлы Visio и экспортирует контуры в CSV
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QScrollArea, QProgressBar, QMessageBox,
    QCheckBox, QTabWidget
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pytesseract
from PIL import Image
import json

from contour_extractor import ContourExtractor


class SchematicProcessor(QThread):
    """Обработка схемы в отдельном потоке"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, image_path, output_path, export_csv=True, export_vsdx=True):
        super().__init__()
        self.image_path = image_path
        self.output_path = output_path
        self.export_csv = export_csv
        self.export_vsdx = export_vsdx
        
    def run(self):
        try:
            self.progress.emit("Загрузка изображения...")
            img = cv2.imread(str(self.image_path))
            if img is None:
                self.finished.emit(False, "Не удалось загрузить изображение")
                return
            
            # Извлечение контуров и экспорт в CSV
            if self.export_csv:
                self.progress.emit("Извлечение контуров из изображения...")
                success = self.export_contours_to_csv(self.image_path)
                if not success:
                    self.finished.emit(False, "Ошибка при извлечении контуров")
                    return
            
            # Обработка схемы для VSDX
            if self.export_vsdx:
                self.progress.emit("Предварительная обработка...")
                processed = self.preprocess_image(img)
                
                self.progress.emit("Обнаружение элементов...")
                elements = self.detect_elements(processed, img)
                
                self.progress.emit("Распознавание текста...")
                elements = self.recognize_text(img, elements)
                
                self.progress.emit("Генерация VSDX...")
                self.generate_vsdx(elements, self.output_path)
            
            success_msg = "Успешно!"
            if self.export_csv and self.export_vsdx:
                success_msg += " Созданы файлы CSV, JSON и VSDX"
            elif self.export_csv:
                success_msg += " Созданы файлы CSV и JSON"
            else:
                success_msg += " Файл VSDX создан"
            
            self.finished.emit(True, success_msg)
            
        except Exception as e:
            self.finished.emit(False, f"Ошибка: {str(e)}")
    
    def export_contours_to_csv(self, image_path):
        """Экспортирует контуры в CSV формат"""
        try:
            extractor = ContourExtractor(image_path)
            
            if not extractor.load_image():
                return False
            
            # Обработка изображения
            extractor.preprocess_image()
            
            # Извлечение контуров
            contours = extractor.extract_contours(min_area=50)
            
            if len(contours) == 0:
                self.progress.emit("Предупреждение: контуры не найдены")
            
            # Разделение на части
            parts = extractor.split_contours_into_parts()
            
            # Экспорт
            output_stem = Path(image_path).stem
            extractor.export_to_csv(f"{output_stem}_contours.csv")
            extractor.export_to_json(f"{output_stem}_contours.json")
            
            # Визуализация
            extractor.visualize_contours(f"{output_stem}_visualization.jpg")
            
            self.progress.emit(f"Контуры: {len(contours)}, Частей: {len(parts)}")
            return True
        
        except Exception as e:
            print(f"Ошибка экспорта контуров: {e}")
            return False
    
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
                if int(text_data['conf'][i]) > 30:
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
            pass
        
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
            
            # Масштабирование для Visio
            scale = 0.01
            
            for elem in elements:
                if elem['type'] == 'line':
                    x1, y1 = elem['points'][0]
                    x2, y2 = elem['points'][1]
                    connector = page.connect(
                        (x1*scale, y1*scale),
                        (x2*scale, y2*scale)
                    )
                
                elif elem['type'] == 'circle':
                    cx, cy = elem['center']
                    r = elem['radius']
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
            pass


class SchematicConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.processor = None
        
    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle('Schematic Converter - VSDX + CSV Export')
        self.setGeometry(100, 100, 1000, 750)
        
        # Главный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Вкладки
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Вкладка 1: Основная обработка
        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        
        # Область для отображения изображения
        self.image_label = QLabel('Изображение схемы будет отображено здесь')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")
        
        scroll = QScrollArea()
        scroll.setWidget(self.image_label)
        scroll.setWidgetResizable(True)
        tab1_layout.addWidget(QLabel('📸 Предпросмотр:'), 0, Qt.AlignTop)
        tab1_layout.addWidget(scroll)
        
        # Опции экспорта
        options_layout = QHBoxLayout()
        self.export_csv_cb = QCheckBox('Экспортировать в CSV (контуры)')
        self.export_csv_cb.setChecked(True)
        self.export_vsdx_cb = QCheckBox('Экспортировать в VSDX')
        self.export_vsdx_cb.setChecked(True)
        options_layout.addWidget(self.export_csv_cb)
        options_layout.addWidget(self.export_vsdx_cb)
        options_layout.addStretch()
        tab1_layout.addLayout(options_layout)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton('📂 Загрузить изображение')
        self.load_btn.clicked.connect(self.load_image)
        button_layout.addWidget(self.load_btn)
        
        self.convert_btn = QPushButton('⚙️ Конвертировать')
        self.convert_btn.clicked.connect(self.convert_image)
        self.convert_btn.setEnabled(False)
        button_layout.addWidget(self.convert_btn)
        
        tab1_layout.addLayout(button_layout)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        tab1_layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel('Готово к работе')
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        tab1_layout.addWidget(self.status_label)
        
        # Вкладка 2: Справка
        tab2_widget = QWidget()
        tab2_layout = QVBoxLayout(tab2_widget)
        
        help_text = QLabel(
            """
            <h3>📚 Справка</h3>
            
            <h4>Что делает эта программа:</h4>
            <ul>
                <li><b>CSV Экспорт:</b> Извлекает контуры из изображения и экспортирует их в CSV формат для Microsoft Drawing</li>
                <li><b>VSDX Экспорт:</b> Создает файлы для Microsoft Visio</li>
                <li><b>Визуализация:</b> Генерирует файл визуализации для проверки обнаруженных контуров</li>
                <li><b>JSON:</b> Экспортирует структурированные данные для ручной обработки</li>
            </ul>
            
            <h4>Выходные файлы:</h4>
            <ul>
                <li><code>*_contours.csv</code> - Основные контуры</li>
                <li><code>*_parts.csv</code> - Отдельные части контуров</li>
                <li><code>*_vertices.csv</code> - Координаты вершин (для Drawing)</li>
                <li><code>*_contours.json</code> - JSON данные</li>
                <li><code>*_visualization.jpg</code> - Визуализация контуров</li>
                <li><code>*.vsdx</code> - Microsoft Visio файл</li>
            </ul>
            
            <h4>Как использовать:</h4>
            <ol>
                <li>Загрузите изображение схемы (JPG, PNG, BMP)</li>
                <li>Выберите форматы экспорта (CSV и/или VSDX)</li>
                <li>Нажмите "Конвертировать"</li>
                <li>Дождитесь завершения обработки</li>
                <li>Используйте созданные файлы в ваших приложениях</li>
            </ol>
            
            <h4>💡 Совет:</h4>
            <p>Для лучших результатов используйте чёткие изображения схем с хорошим контрастом между линиями и фоном.</p>
            """
        )
        help_text.setWordWrap(True)
        scroll2 = QScrollArea()
        scroll2.setWidget(help_text)
        scroll2.setWidgetResizable(True)
        tab2_layout.addWidget(scroll2)
        
        tabs.addTab(tab1_widget, "Конвертер")
        tabs.addTab(tab2_widget, "Справка")
        
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
            
            self.status_label.setText(f'✓ Загружено: {Path(file_path).name}')
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
            self.load_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            export_csv = self.export_csv_cb.isChecked()
            export_vsdx = self.export_vsdx_cb.isChecked()
            
            if not export_csv and not export_vsdx:
                QMessageBox.warning(self, 'Ошибка', 'Выберите хотя бы один формат экспорта')
                self.convert_btn.setEnabled(True)
                self.load_btn.setEnabled(True)
                return
            
            self.processor = SchematicProcessor(
                self.current_image, output_path, export_csv, export_vsdx
            )
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
        self.load_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(f"✓ {message}")
            QMessageBox.information(self, 'Успех', message)
        else:
            self.status_label.setText(f"✗ {message}")
            QMessageBox.critical(self, 'Ошибка', message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SchematicConverterGUI()
    window.show()
    sys.exit(app.exec_())
