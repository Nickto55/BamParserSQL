import os
import sys
import base64
import threading
import time
import subprocess
import pandas as pd
import plyer
import tkinter as tk
from tkinter import filedialog
import queue
import uuid

from dataclasses import fields
from script.env_assets import HandlerEnv
from sql_order_engine import EngineLogic
from bam_parcer_sql import SqlParserLogic
from dse_order_manager import DseOrderLogic
from script.excel_return import TableTransformation
from handlings.handling_config import ConfigMainProgram


_tk_request_queue = queue.Queue()
_tk_response_dict = {}


def _tkinter_worker():
    """
    Фоновый поток, который единолично управляет Tkinter.
    Он постоянно опрашивает очередь и обновляет интерфейс.
    """
    root = tk.Tk()
    root.withdraw()

    while True:
        try:
            if not _tk_request_queue.empty():
                req = _tk_request_queue.get_nowait()
                req_id = req['id']

                if req['action'] == 'select_files':
                    filepaths = filedialog.askopenfilenames(
                        title=f"Выберите Excel файлы для {req['name']}",
                        filetypes=(("Excel files", "*.xlsx *.xls *.xlsm"), ("All files", "*.*"))
                    )
                    _tk_response_dict[req_id] = list(filepaths) if filepaths else []

                _tk_request_queue.task_done()

            root.update()
            time.sleep(0.05)

        except tk.TclError:
            break
        except Exception as e:
            print(f"Ошибка в потоке Tkinter: {e}")
            break


_tk_thread = threading.Thread(target=_tkinter_worker, daemon=True)
_tk_thread.start()


class Backend:
    def __init__(self):
        self.stop_event = threading.Event()
        self.config_program = ConfigMainProgram()
        self.path_outfile = None
        self.current_thread = None
        self.table_data = []
        self.table_headers = [
            "Дсе", "ТП не в архиве", "ДСЕ без маршрутов",
            "ДСЕ без основного материала", "Дсе без трудоемкости",
            "Всего нет УП", "Наименование изделия (ИС)"
        ]
        self.log_messages = []
        self._table_window_open = False

    def get_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def get_logo(self):
        """Логотип в base64 data URI — надёжно грузится в webview из любого контекста"""
        try:
            logo_path = self.get_resource_path('static/png/bam-parcer-sql.png')
            with open(logo_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('ascii')
            return {'success': True, 'data_uri': f'data:image/png;base64,{encoded}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_dependencies(self):
        env = HandlerEnv()
        value = []
        for i, field in enumerate(fields(env.config)):
            value.append(getattr(env.config, field.name))

        CONFIG_DIR = os.path.join(os.path.expanduser("~"), "configs", ".BamParserSQL")
        file_path = os.path.join(CONFIG_DIR, ".env")

        if None in value or '' in value:
            return {
                'success': False,
                'message': '.env файл пуст.',
                'path': file_path,
                'color': 'red'
            }
        return {'success': True}

    def select_files(self, name):
        """
        Безопасный вызов диалога выбора файлов из потока FastAPI.
        Отправляет запрос в очередь Tkinter и ждет ответа.
        """
        req_id = str(uuid.uuid4())
        _tk_request_queue.put({'id': req_id, 'action': 'select_files', 'name': name})
        timeout = 120
        start_time = time.time()
        while req_id not in _tk_response_dict:
            if time.time() - start_time > timeout:
                return {'success': False, 'error': 'Превышено время ожидания выбора файла'}
            time.sleep(0.1)

        filepaths = _tk_response_dict.pop(req_id)
        if not filepaths:
            return {'success': False, 'paths': []}

        return {
            'success': True,
            'paths': filepaths,
            'name': os.path.basename(filepaths[0]) if filepaths else '',
            'str_paths': ', '.join(filepaths)
        }

    def test_db_connection(self):
        try:
            from script.scr_cmd_run import ScriptCmd
            test_bd_connect = ScriptCmd(log_callback=self._log_callback)
            result = test_bd_connect.test_connection()
            return {'success': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _log_callback(self, message, color_log=None, **kwargs):
        entry = {'message': message, 'color': color_log, 'timestamp': time.time()}
        self.log_messages.append(entry)

    def _table_callback(self, row_data):
        self.table_data.append(row_data)

    @staticmethod
    def _normalize_paths(file_paths):
        """Приводит вход к списку путей: принимает list, tuple или строку с разделителями"""
        if isinstance(file_paths, (list, tuple)):
            return [str(p).strip() for p in file_paths if str(p).strip()]
        if isinstance(file_paths, str):
            return [p.strip() for p in file_paths.replace(';', ',').split(',') if p.strip()]
        return []

    def start_processing(self, file_paths, options):
        self.stop_event.clear()
        self.log_messages = []
        self.table_data = []
        self.path_outfile = None

        paths = self._normalize_paths(file_paths)[0]

        if not paths:
            self._log_callback("Ошибка: не указаны файлы для обработки", "red")
            return {'success': False, 'error': 'Пустой список файлов'}

        def run_logic():
            # try:
            self._log_callback("Начало работы...")

            var_split = options.get('query_split', 1)
            var_error_handler = options.get('error_handler', True)

            checkbox_dse = options.get('dse_order', True)
            checkbox_bam = options.get('bam_parser', True)
            checkbox_result = options.get('generate_table', True)

            if checkbox_dse and checkbox_bam:
                manager = EngineLogic(
                    log_callback=self._log_callback,
                    table_callback=self._table_callback,
                    stop_event=self.stop_event,
                    var_radiobutton_value_query_split=var_split,
                    var_bool_error_handler_inside_request_for_swith=var_error_handler
                )
                manager.main(paths)
            elif checkbox_dse and not checkbox_bam:
                manager = DseOrderLogic()
                manager.main(paths)
            elif not checkbox_dse and checkbox_bam:
                manager = SqlParserLogic(
                    log_callback=self._log_callback,
                    table_callback=self._table_callback,
                    stop_event=self.stop_event,
                )
                manager.main(paths, var_split, var_error_handler)
            else:
                self._log_callback('Ошибка: не выбран ни один модуль обработки', 'red')
                return

            if checkbox_result:
                result = TableTransformation(paths)
                result.main()

            self.path_outfile = paths

            if self.stop_event.is_set():
                self._log_callback("Процесс остановлен пользователем. Результат сохранён.", "orange")
            else:
                self._log_callback("Процесс успешно завершен.", "green")
                self._send_notification(
                    "Программа завершена",
                    "Программа завершена, проверьте файл",
                    16
                )

            # except Exception as e:
            #     self._log_callback(f"\nERROR: {str(e)}", "red")

        self.current_thread = threading.Thread(target=run_logic, daemon=True)
        self.current_thread.start()
        return {'success': True}

    def stop_processing(self):
        self.stop_event.set()
        self._log_callback("Отправлен сигнал остановки...", "orange")
        return {'success': True}

    @staticmethod
    def _open_path(path):
        """Кроссплатформенное открытие файла/папки"""
        if sys.platform.startswith('win'):
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])

    def open_result_file(self):
        path = self.path_outfile
        if not path:
            return {'success': False, 'error': 'Путь к файлу не указан'}
        try:
            target = path

            self._open_path(os.path.abspath(target))

            self._log_callback("-Файл открыт", "#788084")
            return {'success': True}
        except Exception as e:
            self._log_callback(f"Ошибка при открытии файла: {e}", "red")
            return {'success': False, 'error': str(e)}

    def open_work_table(self):
        self._table_window_open = not self._table_window_open
        return {
            'success': True,
            'is_open': self._table_window_open,
            'data': self.table_data,
            'headers': self.table_headers
        }

    def get_table_data(self):
        return {
            'headers': self.table_headers,
            'data': self.table_data
        }

    def get_help_text(self):
        try:
            from static.help_text import help_text as help_text_str
            return {'success': True, 'text': help_text_str}
        except Exception as e:
            return {'success': False, 'error': str(e), 'text': f"Ошибка загрузки справки:\n{str(e)}"}

    def _send_notification(self, title, message, timeout=15):
        try:
            ico_path = self.get_resource_path('static/ico/bam-parcer-sql.ico')
            plyer.notification.notify(
                title=title,
                message=message,
                app_name='SQL Order Engine',
                timeout=timeout,
                app_icon=ico_path
            )
        except Exception:
            pass
