"""
СКАЧИВАНИЕ ФАЙЛОВ С GOOGLE DRIVE
=================================

Работает БЕЗ Google Drive API, используя прямые ссылки на скачивание.

Логика:
1. Получает ID файлов или прямые ссылки из config.py
2. Использует библиотеку gdown для скачивания
3. Сохраняет файлы во временную папку с префиксом "temp_"
4. Возвращает список путей к скачанным файлам

Функции:
- download_target_files() - главная функция, скачивает все файлы
- download_file_by_id() - скачивание по ID файла
- download_file_by_link() - скачивание по прямой ссылке
- extract_file_id_from_url() - извлечение ID из URL
"""

import os
import warnings
import requests
import gdown
from bs4 import XMLParsedAsHTMLWarning
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FILE_IDS, DOWNLOAD_LINKS, TARGET_FILES, GOOGLE_DRIVE_FOLDER_ID

# Подавляем предупреждение о парсинге XML как HTML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def extract_file_id_from_url(url):
    """
    Извлечение ID файла из URL Google Drive
    
    Поддерживает форматы:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/uc?export=download&id=FILE_ID
    - https://drive.google.com/open?id=FILE_ID
    - Просто ID (без URL)
    """
    # Различные форматы URL Google Drive
    if '/file/d/' in url:
        # Формат: https://drive.google.com/file/d/FILE_ID/view
        file_id = url.split('/file/d/')[1].split('/')[0]
    elif 'id=' in url:
        # Формат: https://drive.google.com/uc?export=download&id=FILE_ID
        file_id = url.split('id=')[1].split('&')[0]
    elif '/open?id=' in url:
        # Формат: https://drive.google.com/open?id=FILE_ID
        file_id = url.split('id=')[1].split('&')[0]
    else:
        # Если это уже ID
        file_id = url.strip()
    
    return file_id


def download_file_by_id(file_id, file_name, download_dir=None):
    """
    Скачивание файла по ID через gdown
    
    Логика:
    1. Определяет тип файла (Google Sheets или Google Drive файл)
    2. Формирует правильную ссылку на скачивание
    3. Использует gdown для скачивания
    4. Сохраняет в downloaded_files/<имя_файла>
    5. Проверяет, что файл скачан и не пустой
    """
    if download_dir is None:
        # Путь относительно корня проекта
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        download_dir = os.path.join(base_dir, "data", "downloaded_files")
    try:
        # Создаем папку для скачанных файлов
        os.makedirs(download_dir, exist_ok=True)
        
        local_path = os.path.join(download_dir, file_name)
        
        print(f"  Скачивание: {file_name}...")
        
        # Пробуем сначала как Google Sheets (экспорт в Excel)
        # Формат: https://docs.google.com/spreadsheets/d/{ID}/export?format=xlsx
        sheets_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        
        try:
            # Пытаемся скачать как Google Sheets
            response = requests.get(sheets_url, allow_redirects=True, timeout=30)
            
            if response.status_code == 200 and len(response.content) > 1000:  # Минимум 1KB
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                file_size = os.path.getsize(local_path) / 1024
                print(f"  ✓ Скачан (Google Sheets): {file_name} ({file_size:.1f} KB)")
                return local_path
        except Exception as sheets_error:
            # Если не получилось как Google Sheets, пробуем как обычный файл Drive
            pass
        
        # Пробуем как обычный файл Google Drive
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        try:
            gdown.download(download_url, local_path, quiet=True, fuzzy=True)
        except Exception as gdown_error:
            return None
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            file_size = os.path.getsize(local_path) / 1024  # размер в KB
            print(f"  ✓ Скачан: {file_name} ({file_size:.1f} KB)")
            return local_path
        else:
            return None
            
    except Exception as e:
        return None


def download_file_by_link(download_link, file_name, download_dir=None):
    """
    Скачивание файла по прямой ссылке
    
    Аналогично download_file_by_id, но использует готовую ссылку
    """
    if download_dir is None:
        # Путь относительно корня проекта
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        download_dir = os.path.join(base_dir, "data", "downloaded_files")
    try:
        # Создаем папку для скачанных файлов
        os.makedirs(download_dir, exist_ok=True)
        
        local_path = os.path.join(download_dir, file_name)
        
        print(f"  Скачивание: {file_name}...")
        
        # Используем gdown (quiet=True для уменьшения вывода)
        try:
            gdown.download(download_link, local_path, quiet=True, fuzzy=True)
        except Exception as gdown_error:
            return None
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            file_size = os.path.getsize(local_path) / 1024
            print(f"  ✓ Скачан: {file_name} ({file_size:.1f} KB)")
            return local_path
        else:
            return None
            
    except Exception as e:
        error_str = str(e)
        if "Failed to retrieve" in error_str or "Cannot retrieve" in error_str:
            print(f"  ✗ Не удалось скачать {file_name} (проверьте права доступа)")
        else:
            print(f"  ✗ Ошибка: {file_name}")
        return None


def download_target_files(download_dir=None):
    """
    Скачивание всех целевых файлов
    
    Логика работы:
    1. Удаляет старые файлы из папки downloaded_files
    2. Проверяет DOWNLOAD_LINKS (приоритет 1)
    3. Если нет, проверяет FILE_IDS (приоритет 2)
    4. Возвращает список путей к скачанным файлам
    
    Требования:
    - В config.py должны быть указаны DOWNLOAD_LINKS или FILE_IDS
    - Файлы должны быть доступны по ссылке на Google Drive
    """
    if download_dir is None:
        # Путь относительно корня проекта
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        download_dir = os.path.join(base_dir, "data", "downloaded_files")
    # Создаем папку для скачанных файлов
    os.makedirs(download_dir, exist_ok=True)
    
    # Удаляем старые файлы из папки
    try:
        for old_file in os.listdir(download_dir):
            old_path = os.path.join(download_dir, old_file)
            if os.path.isfile(old_path):
                os.remove(old_path)
                print(f"  Удален старый файл: {old_file}")
    except Exception as e:
        pass
    
    downloaded_files = []
    
    # Вариант 1: Используем прямые ссылки на скачивание
    if DOWNLOAD_LINKS and any(DOWNLOAD_LINKS):
        for i, link in enumerate(DOWNLOAD_LINKS):
            if link and link.strip():
                if i < len(TARGET_FILES):
                    file_name = TARGET_FILES[i]
                    file_path = download_file_by_link(link.strip(), file_name, download_dir)
                    if file_path:
                        downloaded_files.append(file_path)
    
    # Вариант 2: Используем ID файлов
    elif FILE_IDS and any(FILE_IDS):
        for i, file_id in enumerate(FILE_IDS):
            if file_id and file_id.strip():
                if i < len(TARGET_FILES):
                    file_name = TARGET_FILES[i]
                    # Извлекаем ID из URL, если это ссылка
                    clean_id = extract_file_id_from_url(file_id.strip())
                    file_path = download_file_by_id(clean_id, file_name, download_dir)
                    if file_path:
                        downloaded_files.append(file_path)
    
    return downloaded_files

