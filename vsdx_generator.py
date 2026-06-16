#!/usr/bin/env python3
"""
Генератор VSDX файлов
Создаёт файлы Microsoft Visio из распознанных элементов схемы
"""

import json
import zipfile
import os
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree
import xml.dom.minidom as minidom

class VSDXGenerator:
    """Генерирует VSDX файлы (это ZIP архивы с XML)"""
    
    # XML Namespaces
    NAMESPACES = {
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'v': 'http://schemas.microsoft.com/office/visio/2012/main',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
    }
    
    def __init__(self, output_path):
        self.output_path = output_path
        self.shape_id = 1
        
    def generate(self, elements_json):
        """Генерирует VSDX файл из JSON данных"""
        
        # Парсим JSON
        if isinstance(elements_json, str):
            with open(elements_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = elements_json
        
        elements = data.get('elements', [])
        
        # Создаём временную директорию
        temp_dir = Path(self.output_path).parent / '.vsdx_temp'
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Создаём структуру VSDX
            self._create_document_structure(temp_dir, elements)
            
            # Упаковываем в ZIP
            self._create_zip(temp_dir)
            
            print(f"✅ VSDX файл создан: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при создании VSDX: {e}")
            return False
        finally:
            # Очищаем временные файлы
            self._cleanup(temp_dir)
    
    def _create_document_structure(self, temp_dir, elements):
        """Создаёт структуру документа VSDX"""
        
        # Структура папок
        (temp_dir / '_rels').mkdir(exist_ok=True)
        (temp_dir / 'word' / '_rels').mkdir(parents=True, exist_ok=True)
        (temp_dir / 'visio' / '_rels').mkdir(parents=True, exist_ok=True)
        
        # [Content_Types].xml
        self._create_content_types(temp_dir)
        
        # _rels/.rels
        self._create_relationships(temp_dir)
        
        # visio/document.xml с элементами схемы
        self._create_document(temp_dir, elements)
        
        # visio/document.xml.rels
        self._create_document_rels(temp_dir)
    
    def _create_content_types(self, temp_dir):
        """Создаёт [Content_Types].xml"""
        root = Element('Types')
        root.set('xmlns', 'http://schemas.openxmlformats.org/package/2006/content-types')
        
        # Defaults
        default = SubElement(root, 'Default')
        default.set('Extension', 'rels')
        default.set('ContentType', 'application/vnd.openxmlformats-package.relationships+xml')
        
        default = SubElement(root, 'Default')
        default.set('Extension', 'xml')
        default.set('ContentType', 'application/xml')
        
        # Override для document.xml
        override = SubElement(root, 'Override')
        override.set('PartName', '/visio/document.xml')
        override.set('ContentType', 'application/vnd.ms-visio.drawing.main+xml')
        
        self._save_xml(temp_dir / '[Content_Types].xml', root)
    
    def _create_relationships(self, temp_dir):
        """Создаёт _rels/.rels"""
        root = Element('Relationships')
        root.set('xmlns', 'http://schemas.openxmlformats.org/package/2006/relationships')
        
        rel = SubElement(root, 'Relationship')
        rel.set('Id', 'rId1')
        rel.set('Type', 'http://schemas.microsoft.com/office/2007/relationships/ui/extensibility')
        rel.set('Target', 'visio/document.xml')
        
        self._save_xml(temp_dir / '_rels' / '.rels', root)
    
    def _create_document(self, temp_dir, elements):
        """Создаёт visio/document.xml с элементами"""
        root = Element('VisioDocument')
        root.set('xmlns', 'http://schemas.microsoft.com/office/visio/2012/main')
        root.set('xmlns:r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
        
        # Pages
        pages = SubElement(root, 'Pages')
        page = SubElement(pages, 'Page')
        page.set('ID', '0')
        page.set('NameU', 'Page-1')
        page.set('Name', 'Page-1')
        
        # Shapes element
        shapes = SubElement(root, 'PageContents')
        
        # Добавляем элементы
        for elem in elements:
            self._add_element(shapes, elem)
        
        self._save_xml(temp_dir / 'visio' / 'document.xml', root)
    
    def _add_element(self, parent, element):
        """Добавляет элемент в документ"""
        elem_type = element.get('type')
        
        if elem_type == 'line':
            self._add_line(parent, element)
        elif elem_type == 'circle':
            self._add_circle(parent, element)
        elif elem_type == 'rectangle':
            self._add_rectangle(parent, element)
        elif elem_type == 'text':
            self._add_text(parent, element)
    
    def _add_line(self, parent, element):
        """Добавляет линию"""
        shape = SubElement(parent, 'Shape')
        shape.set('ID', str(self.shape_id))
        shape.set('Type', 'Shape')
        shape.set('Master', '0')
        self.shape_id += 1
        
        xf = SubElement(shape, 'XForm')
        pin_x = SubElement(xf, 'PinX')
        pin_x.text = '0'
        pin_y = SubElement(xf, 'PinY')
        pin_y.text = '0'
        width = SubElement(xf, 'Width')
        width.text = '1'
        height = SubElement(xf, 'Height')
        height.text = '1'
    
    def _add_circle(self, parent, element):
        """Добавляет круг"""
        shape = SubElement(parent, 'Shape')
        shape.set('ID', str(self.shape_id))
        self.shape_id += 1
        
        xf = SubElement(shape, 'XForm')
        cx, cy = element.get('center', (0, 0))
        r = element.get('radius', 10)
        
        pin_x = SubElement(xf, 'PinX')
        pin_x.text = str(cx / 100)
        pin_y = SubElement(xf, 'PinY')
        pin_y.text = str(cy / 100)
        width = SubElement(xf, 'Width')
        width.text = str(r / 50)
        height = SubElement(xf, 'Height')
        height.text = str(r / 50)
    
    def _add_rectangle(self, parent, element):
        """Добавляет прямоугольник"""
        shape = SubElement(parent, 'Shape')
        shape.set('ID', str(self.shape_id))
        self.shape_id += 1
        
        xf = SubElement(shape, 'XForm')
        x = element.get('x', 0)
        y = element.get('y', 0)
        w = element.get('width', 100)
        h = element.get('height', 100)
        
        pin_x = SubElement(xf, 'PinX')
        pin_x.text = str(x / 100)
        pin_y = SubElement(xf, 'PinY')
        pin_y.text = str(y / 100)
        width = SubElement(xf, 'Width')
        width.text = str(w / 100)
        height = SubElement(xf, 'Height')
        height.text = str(h / 100)
    
    def _add_text(self, parent, element):
        """Добавляет текст"""
        shape = SubElement(parent, 'Shape')
        shape.set('ID', str(self.shape_id))
        self.shape_id += 1
        
        text_elem = SubElement(shape, 'Text')
        text_elem.text = element.get('text', '')
    
    def _create_document_rels(self, temp_dir):
        """Создаёт visio/document.xml.rels"""
        root = Element('Relationships')
        root.set('xmlns', 'http://schemas.openxmlformats.org/package/2006/relationships')
        
        self._save_xml(temp_dir / 'visio' / 'document.xml.rels', root)
    
    def _save_xml(self, path, element):
        """Сохраняет XML с красивым форматированием"""
        xml_str = minidom.parseString(ElementTree(element).getroot()).toprettyxml(indent="  ")
        
        with open(path, 'w', encoding='utf-8') as f:
            # Удаляем XML declaration и пустые строки
            lines = xml_str.split('\n')
            f.write('\n'.join(lines[1:]))
    
    def _create_zip(self, temp_dir):
        """Упаковывает в ZIP архив"""
        with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = str(file_path.relative_to(temp_dir))
                    zf.write(file_path, arcname)
    
    def _cleanup(self, temp_dir):
        """Удаляет временные файлы"""
        try:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except:
            pass


# Использование из других модулей
def json_to_vsdx(json_path, output_vsdx):
    """Удобная функция для конвертирования JSON в VSDX"""
    generator = VSDXGenerator(output_vsdx)
    return generator.generate(json_path)


# Тестирование
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 3:
        json_file = sys.argv[1]
        vsdx_file = sys.argv[2]
        
        if json_to_vsdx(json_file, vsdx_file):
            print("✅ Успешно создан VSDX файл!")
        else:
            print("❌ Ошибка при создании VSDX файла")
    else:
        print("Использование: python3 vsdx_generator.py <input.json> <output.vsdx>")
