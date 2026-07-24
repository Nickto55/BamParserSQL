import eel
import os
import sys

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import Backend
eel.init('web')

backend = Backend()


@eel.expose
def check_dependencies():
    """Проверка зависимостей (.env файл)"""
    return backend.check_dependencies()

@eel.expose
def select_files(name):
    """Открыть диалог выбора файлов"""
    return backend.select_files(name)

@eel.expose
def start_processing(file_paths, options):
    """Запуск обработки в фоновом потоке"""
    return backend.start_processing(file_paths, options)

@eel.expose
def stop_processing():
    """Остановка обработки"""
    return backend.stop_processing()

@eel.expose
def open_result_file():
    """Открыть файл результата"""
    return backend.open_result_file()

@eel.expose
def open_work_table():
    """Открыть/закрыть таблицу обработанных ДСЕ"""
    return backend.open_work_table()

@eel.expose
def get_table_data():
    """Получить данные таблицы"""
    return backend.get_table_data()

@eel.expose
def get_help_text():
    """Получить текст справки"""
    return backend.get_help_text()

@eel.expose
def get_resource_path(relative_path):
    """Получить абсолютный путь к ресурсу"""
    return backend.get_resource_path(relative_path)

@eel.expose
def test_db_connection():
    """Проверка подключения к БД"""
    return backend.test_db_connection()

# Запуск приложения
if __name__ == '__main__':
    eel.start(
        'index.html',
        size=(1200, 750),

        # title='SQL Order Engine',
        # icon_path=backend.get_resource_path('static/ico/bam-parcer-sql.ico'),
        mode='chrome-app',  # chrome-app для нативного вида
        cmdline_args=['--disable-features=TranslateUI']
    )
