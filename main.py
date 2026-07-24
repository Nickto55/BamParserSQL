import webview
import os
import sys
import time
import threading
import urllib.request

from backend import Backend
from api_server import start_server

# Порт для API сервера
API_PORT = 8765
API_URL = f'http://127.0.0.1:{API_PORT}/api'

# Минимальное время показа сплэш-экрана (сек) — чтобы анимация успела сыграть
SPLASH_MIN_TIME = 1.8
# Максимальное ожидание готовности сервера (сек)
SERVER_TIMEOUT = 30


def get_web_dir():
    """Путь к папке web (с учётом PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'web')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')


def wait_for_server(timeout=SERVER_TIMEOUT):
    """Ждём, пока API-сервер начнёт отвечать"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f'{API_URL}/status', timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def boot(window, backend, web_dir, started_at):
    """
    Фоновая загрузка: поднимаем сервер, ждём его готовности,
    затем переключаем окно со сплэша на основной интерфейс.
    """
    # Запускаем API сервер
    start_server(backend, port=API_PORT)

    # Ждём готовности сервера
    server_ok = wait_for_server()

    # Держим сплэш минимум SPLASH_MIN_TIME
    elapsed = time.time() - started_at
    if elapsed < SPLASH_MIN_TIME:
        time.sleep(SPLASH_MIN_TIME - elapsed)

    # Переключаемся на основной интерфейс
    index_path = os.path.join(web_dir, 'index.html')
    window.load_url(f'file:///{index_path.replace(os.sep, "/")}')

    if not server_ok:
        print('[SQL Order Engine] ВНИМАНИЕ: сервер не ответил вовремя')


def main():
    started_at = time.time()

    # Создаём бэкенд
    backend = Backend()

    web_dir = get_web_dir()
    splash_path = os.path.join(web_dir, 'splash.html')

    # Окно сразу открывает сплэш — мгновенный отклик для пользователя
    window = webview.create_window(
        title='SQL Order Engine',
        url=f'file:///{splash_path.replace(os.sep, "/")}',
        width=1250,
        height=780,
        min_size=(900, 600),
        text_select=True,
        confirm_close=False
    )

    # Сервер поднимаем ПОСЛЕ старта GUI-цикла — сплэш уже на экране
    webview.start(
        boot,
        args=(window, backend, web_dir, started_at),
        debug=False,  # True для отладки (откроет DevTools)
        gui='edgechromium'  # edgechromium на Windows, cocoa на macOS, gtk на Linux
    )


if __name__ == '__main__':
    main()
