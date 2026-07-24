import webview
import os
import sys
import time

from backend import Backend
from api_server import start_server

# Порт для API сервера
API_PORT = 8765

def main():
    # Создаём бэкенд
    backend = Backend()
    
    # Запускаем API сервер в фоновом потоке
    start_server(backend, port=API_PORT)
    
    # Ждём запуска сервера
    time.sleep(1)
    
    # Определяем путь к HTML
    if hasattr(sys, '_MEIPASS'):
        web_dir = os.path.join(sys._MEIPASS, 'web')
    else:
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
    
    html_path = os.path.join(web_dir, 'index.html')
    
    # Создаём окно webview
    window = webview.create_window(
        title='SQL Order Engine',
        url=f'file:///{html_path.replace(os.sep, "/")}',
        width=1250,
        height=780,
        min_size=(900, 600),
        text_select=True,
        confirm_close=False
    )
    
    # Запускаем
    webview.start(
        debug=True,  # True для отладки (откроет DevTools)
        gui='edgechromium'  # edgechromium на Windows, cocoa на macOS, gtk на Linux
    )

if __name__ == '__main__':
    main()
