import sys
import time
import random
from pathlib import Path

import webview

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

WEB_DIR = BASE_DIR / "web"

from backend import Backend


class Api:
    """
    JS-API: доступен в JS как pywebview.api.<method>()
    Проксирует вызовы в Backend + управляет окном.
    """

    def __init__(self):
        self._window = None
        self.backend = Backend()
        self._pos = {'x': None, 'y': None}
        self._drag = None

    def set_window(self, window):
        """Устанавливаем ссылку на окно после создания"""
        self._window = window
        try:
            window.events.moved += self._on_moved
        except Exception:
            pass

    def _on_moved(self, x, y):
        self._pos['x'] = x
        self._pos['y'] = y


    def minimize_window(self):
        """Свернуть окно"""
        if self._window:
            self._window.minimize()
        return True

    def close_window(self):
        """Закрыть окно и завершить приложение"""
        for w in list(webview.windows):
            try:
                w.destroy()
            except Exception:
                pass
        return True

    def drag_start(self, sx, sy):
        x, y = self._pos['x'], self._pos['y']
        if x is None:
            x = getattr(self._window, 'x', None)
            y = getattr(self._window, 'y', None)
        if x is not None:
            self._drag = (sx, sy, x, y)

    def drag_move(self, sx, sy):
        if self._drag and self._window:
            sx0, sy0, wx, wy = self._drag
            self._window.move(int(wx + (sx - sx0)), int(wy + (sy - sy0)))

    def drag_end(self):
        self._drag = None

    def check_dependencies(self):
        return self.backend.check_dependencies()

    def test_db_connection(self):
        return self.backend.test_db_connection()

    def get_logo(self):
        return self.backend.get_logo()

    def select_files(self, name):
        return self.backend.select_files(name)

    def start_processing(self, file_paths, options):
        return self.backend.start_processing(file_paths, options)

    def stop_processing(self):
        return self.backend.stop_processing()

    def open_result_file(self):
        return self.backend.open_result_file()

    def get_table_data(self):
        return self.backend.get_table_data()

    def get_help_text(self):
        return self.backend.get_help_text()

    def get_logs(self):
        return self.backend.log_messages

    def get_status(self):
        return {
            'is_processing': self.backend.current_thread is not None
                             and self.backend.current_thread.is_alive(),
            'path_outfile': self.backend.path_outfile,
            'table_open': self.backend._table_window_open
        }


def main():
    api = Api()

    splash_path = WEB_DIR / "splash.html"
    main_path = WEB_DIR / "index.html"

    splash = webview.create_window(
        title='SQL Order Engine',
        url=str(splash_path),
        width=400,
        height=500,
        resizable=False,
        frameless=True,
        on_top=True,
        confirm_close=False,
        js_api=api
    )

    main_window = webview.create_window(
        title='SQL Order Engine',
        url=str(main_path),
        width=950,
        height=730,
        resizable=False,
        frameless=True,
        js_api=api,
        text_select=False,
        hidden=True
    )

    api.set_window(main_window)

    def on_loaded():
        time_sleep_main_window = random.randint(2, 3)
        time.sleep(time_sleep_main_window)
        splash.destroy()
        main_window.show()
        main_window.restore()

    main_window.events.loaded += on_loaded

    webview.start(
        debug=False,
        gui='edgechromium'
    )


if __name__ == '__main__':
    main()
