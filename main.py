import webview
import os
import sys
import time
import threading
import urllib.request
import random

from pathlib import Path
from backend import Backend
from api_server import start_server

# Порт для API сервера
API_PORT = 8765
API_URL = f'http://127.0.0.1:{API_PORT}/api'


if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

ICON_PATH = BASE_DIR / "static" / "icons" / "dse-orger-manager.ico"

# Минимальное время показа сплэш-экрана (сек) — чтобы анимация успела сыграть
SPLASH_MIN_TIME = 1.8
# Максимальное ожидание готовности сервера (сек)
SERVER_TIMEOUT = 30


class WindowApi:
    """
    JS-API для управления окном из фронтенда.
    Методы доступны в JS как pywebview.api.<method>()
    """

    def __init__(self):
        self.window = None
        self._pos = {'x': None, 'y': None}
        self._drag = None

    def attach(self, window):
        """Привязка окна и подписка на события перемещения"""
        self.window = window
        try:
            window.events.moved += self._on_moved
        except Exception:
            pass

    def _on_moved(self, x, y):
        self._pos['x'] = x
        self._pos['y'] = y

    # --- Управление окном ---

    def minimize(self):
        if self.window:
            self.window.minimize()

    def close_app(self):
        if self.window:
            self.window.destroy()

    # --- Перетаскивание frameless-окна ---

    def _current_pos(self):
        x, y = self._pos['x'], self._pos['y']
        if x is None:
            x = getattr(self.window, 'x', None)
            y = getattr(self.window, 'y', None)
        return x, y

    def drag_start(self, sx, sy):
        x, y = self._current_pos()
        if x is not None:
            self._drag = (sx, sy, x, y)

    def drag_move(self, sx, sy):
        if self._drag and self.window:
            sx0, sy0, wx, wy = self._drag
            self.window.move(int(wx + (sx - sx0)), int(wy + (sy - sy0)))

    def drag_end(self):
        self._drag = None


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


# def main():
#     started_at = time.time()
#
#     # Создаём бэкенд
#     backend = Backend()
#
#     web_dir = get_web_dir()
#     splash_path = os.path.join(web_dir, 'splash.html')
#
#     # JS-API для кнопок окна (свернуть / закрыть / перетаскивание)
#     window_api = WindowApi()
#
#     # Окно сразу открывает сплэш — мгновенный отклик для пользователя
#     window = webview.create_window(
#         title='SQL Order Engine',
#         url=f'file:///{splash_path.replace(os.sep, "/")}',
#         width=1250,
#         height=780,
#         min_size=(900, 600),
#         text_select=True,
#         confirm_close=False,
#         frameless=True,  # кастомный тайтлбар — кнопки в settings-top-bar
#         js_api=window_api
#     )
#     window_api.attach(window)
#
#     # Сервер поднимаем ПОСЛЕ старта GUI-цикла — сплэш уже на экране
#     webview.start(
#         boot,
#         args=(window, backend, web_dir, started_at),
#         debug=True,  # True для отладки (откроет DevTools)
#         gui='edgechromium'  # edgechromium на Windows, cocoa на macOS, gtk на Linux
#     )


def main():
    started_at = time.time()

    backend = Backend()

    web_dir = get_web_dir()
    splash_path = os.path.join(web_dir, 'splash.html')
    main_path = os.path.join(web_dir, 'index.html')

    window_api = WindowApi()

    splash = webview.create_window(
        title='SQL Order Engine',
        url=str(splash_path),
        width=400,
        height=500,
        resizable=False,
        frameless=True,
        on_top=True,
        confirm_close=False
    )

    # window = webview.create_window(
    #     title='SQL Order Engine',
    #     url=f'file:///{splash_path.replace(os.sep, "/")}',
    #     width=1250,
    #     height=780,
    #     min_size=(900, 600),
    #     text_select=True,
    #     confirm_close=False
    # )
    
    # # Сервер поднимаем ПОСЛЕ старта GUI-цикла — сплэш уже на экране
    # webview.start(
    #     boot,
    #     args=(window, backend, web_dir, started_at),
    #     debug=True,  # True для отладки (откроет DevTools)
    #     gui='edgechromium'  # edgechromium на Windows, cocoa на macOS, gtk на Linux
    # )
    main_window = webview.create_window(
        title='SQL Order Engine',
        url=str(main_path),
        width=950,
        height=730,
        resizable=False,
        frameless=True,
        text_select=False,
        hidden=True,
        js_api=window_api
    )

    # window_api.attach(main_window)

    def on_loaded():
        time_sleep_main_window = random.randint(5, 7)
        time.sleep(time_sleep_main_window)
        splash.destroy()
        main_window.show()
        main_window.restore()

    main_window.events.loaded += on_loaded

    webview.start(
        boot,
        icon=str(ICON_PATH),
        args=(main_window, backend, web_dir, started_at),
        debug=True
    )

if __name__ == '__main__':
    main()
