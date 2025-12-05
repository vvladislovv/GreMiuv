"""Конфигурация приложения"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google Drive настройки (прямые ссылки на скачивание)
# Если у вас есть прямые ссылки на файлы, укажите их здесь
# Формат ссылки: https://drive.google.com/uc?export=download&id=FILE_ID
# Или просто ID файла (gdown автоматически сформирует ссылку)

# Вариант 1: Указать ID файлов (из URL Google Drive)
# Чтобы получить ID: откройте файл на Google Drive, скопируйте ID из URL
# Например: https://drive.google.com/file/d/FILE_ID_HERE/view
# ID Google Sheets (из ссылок docs.google.com/spreadsheets)
FILE_IDS = [
    '1wBc0Nzfj7KxgjeWgBC98upRox6NOYCfvSRlGo4tqFmg',  # Испп 23-09.1
    '1z_Vj1egQPix6eJ3x9dRw8pn9405pnpMOFwDRW4VfU_8',  # Испп 24-11
    '1lMV7gbDZ4rhDaPKCpsum90uRbviAUd7JCq2NrnGwIT4',  # Испп 23-09.2
]

# Вариант 2: Прямые ссылки на экспорт Google Sheets в Excel
DOWNLOAD_LINKS = [
    # Формат для Google Sheets: https://docs.google.com/spreadsheets/d/{ID}/export?format=xlsx
    # "https://docs.google.com/spreadsheets/d/1wBc0Nzfj7KxgjeWgBC98upRox6NOYCfvSRlGo4tqFmg/export?format=xlsx",
    # "https://docs.google.com/spreadsheets/d/1z_Vj1egQPix6eJ3x9dRw8pn9405pnpMOFwDRW4VfU_8/export?format=xlsx",
    # "https://docs.google.com/spreadsheets/d/1lMV7gbDZ4rhDaPKCpsum90uRbviAUd7JCq2NrnGwIT4/export?format=xlsx",
]

# Имена файлов (соответствуют порядку в FILE_IDS или DOWNLOAD_LINKS)
TARGET_FILES = [
    "Испп 23-09.1.xlsx",
    "Испп 24-11.xlsx",
    "Испп 23-09.2.xlsx"
]

# ID папки Google Drive (для автоматического поиска файлов, если есть доступ)
GOOGLE_DRIVE_FOLDER_ID = "1Vte1-RAsucB6WLRiQRAUN1Yq37k7GpQb"

# Настройки парсинга
SKIP_FIRST_SHEETS = 3  # Пропускаем первые 3 вкладки
STOP_SHEET_NAME = "УП технической разработки"  # Останавливаемся на этой вкладке

# База данных
# Путь относительно корня проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "students.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# Расписание
PARSE_INTERVAL_MINUTES = 15

