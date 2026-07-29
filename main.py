import webview
import os
import sys
import time
import threading
import urllib.request

from pathlib import Path
from backend import Backend
from api_server import start_server

# Порт для API сервера
API_PORT = 8765
API_URL = f'http://127.0.0.1:{API_PORT}/api'

# Минимальное время показа сплэш-экрана (сек)
SPLASH_MIN_TIME = 3.0
# Максимальное ожидание готовности сервера (сек)
SERVER_TIMEOUT = 30

# Размеры окон
SPLASH_SIZE = (400, 500)
MAIN_SIZE = (950, 730)


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

    def minimize(self):
        if self.window:
            self.window.minimize()

    def close_app(self):
        """Закрыть приложение целиком (все окна)"""
        for w in list(webview.windows):
            try:
                w.destroy()
            except Exception:
                pass

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


def get_screen_size():
    """Размер экрана (Windows -> ctypes, иначе запасной вариант)"""
    try:
        import ctypes
        return (ctypes.windll.user32.GetSystemMetrics(0),
                ctypes.windll.user32.GetSystemMetrics(1))
    except Exception:
        return 1920, 1080


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
    затем ЭТО ЖЕ окно расширяем до основного размера и грузим интерфейс.
    """
    start_server(backend, port=API_PORT)

    server_ok = wait_for_server()

    # Держим сплэш минимум SPLASH_MIN_TIME
    elapsed = time.time() - started_at
    if elapsed < SPLASH_MIN_TIME:
        time.sleep(SPLASH_MIN_TIME - elapsed)

    # Расширяем окно до основного размера и центрируем
    try:
        w, h = MAIN_SIZE
        sw, sh = get_screen_size()
        window.resize(w, h)
        window.move((sw - w) // 2, (sh - h) // 2)
    except Exception as e:
        print(f'[SQL Order Engine] Не удалось изменить размер окна: {e}')

    # Грузим основной интерфейс в то же окно.
    # ВАЖНО: не создаём второе окно из этого потока — на WinForms/edgechromium
    # это приводит к дедлоку (exit code -805306369) и ошибке рекурсии
    # AccessibilityObject.Bounds в мосте JS-API.
    index_path = os.path.join(web_dir, 'index.html')
    window.load_url(f'file:///{index_path.replace(os.sep, "/")}')

    if not server_ok:
        print('[SQL Order Engine] ВНИМАНИЕ: сервер не ответил вовремя')


def main():
    started_at = time.time()

    backend = Backend()

    web_dir = get_web_dir()
    splash_path = os.path.join(web_dir, 'splash.html')

    # JS-API для кнопок окна (свернуть / закрыть / перетаскивание)
    window_api = WindowApi()

    # ЕДИНСТВЕННОЕ окно: стартует как сплэш, затем трансформируется в главное
    window = webview.create_window(
        title='SQL Order Engine',
        url=str(splash_path),
        width=SPLASH_SIZE[0],
        height=SPLASH_SIZE[1],
        resizable=False,
        frameless=True,
        text_select=False,
        confirm_close=False,
        js_api=window_api
    )
    window_api.attach(window)

    # Сервер и переключение интерфейса — ПОСЛЕ старта GUI-цикла
    webview.start(
        boot,
        args=(window, backend, web_dir, started_at),
        debug=True,  # True для отладки (откроет DevTools)
        gui='edgechromium'  # edgechromium на Windows, cocoa на macOS, gtk на Linux
    )


if __name__ == '__main__':
    main()
