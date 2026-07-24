import os
import sys
import threading
import queue
import time
import pandas as pd
import plyer
from tkinter import filedialog
import tkinter as tk

# Скрытое окно tkinter для диалогов
_root = tk.Tk()
_root.withdraw()

from dataclasses import fields
from script.env_assets import HandlerEnv
from sql_order_engine import EngineLogic
from bam_parcer_sql import SqlParserLogic
from dse_order_manager import DseOrderLogic
from script.excel_return import TableTransformation
from handlings.handling_config import ConfigMainProgram


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
        """Возвращает абсолютный путь к ресурсу"""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def check_dependencies(self):
        """Проверка .env файла"""
        env = HandlerEnv()
        value = []
        for i, field in enumerate(fields(env.config)):
            value.append(getattr(env.config, field.name))

        CONFIG_DIR = os.path.join(
            os.path.expanduser("~"),
            "configs",
            ".BamParserSQL"
        )
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
        """Диалог выбора файлов"""
        filepaths = filedialog.askopenfilenames(
            title=f"Выберите Excel файлы для {name}",
            filetypes=(("Excel files", "*.xlsx *.xls *.xlsm"), ("All files", "*.*"))
        )
        if not filepaths:
            return {'success': False, 'paths': []}

        paths = list(filepaths)
        return {
            'success': True,
            'paths': paths,
            'name': os.path.basename(paths[0]) if paths else '',
            'str_paths': ', '.join(paths)
        }

    def test_db_connection(self):
        """Проверка подключения к БД"""
        try:
            from script.scr_cmd_run import ScriptCmd
            test_bd_connect = ScriptCmd(log_callback=self._log_callback)
            result = test_bd_connect.test_connection()
            return {'success': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _log_callback(self, message, color_log=None):
        """Внутренний колбэк для логов"""
        self.log_messages.append({'message': message, 'color': color_log})
        # Отправляем лог на фронтенд
        try:
            import eel
            eel.receiveLog(message, color_log)
        except:
            pass

    def _table_callback(self, row_data):
        """Колбэк для данных таблицы"""
        self.table_data.append(row_data)
        try:
            import eel
            eel.receiveTableRow(row_data)
        except:
            pass

    def start_processing(self, file_paths, options):
        """Запуск обработки"""
        self.stop_event.clear()
        self.log_messages = []
        self.table_data = []
        self.path_outfile = None

        def run_logic():
            try:
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
                    manager.main(file_paths)
                elif checkbox_dse and not checkbox_bam:
                    manager = DseOrderLogic()
                    manager.main(file_paths)
                elif not checkbox_dse and checkbox_bam:
                    manager = SqlParserLogic(
                        log_callback=self._log_callback,
                        table_callback=self._table_callback,
                        stop_event=self.stop_event
                    )
                    manager.main(file_paths, var_split, var_error_handler)
                else:
                    self._log_callback(f'Произошла ошибка: {checkbox_dse} {checkbox_bam}', 'red')
                    return

                if checkbox_result:
                    result = TableTransformation(file_paths)
                    result.main()

                self.path_outfile = file_paths

                if self.stop_event.is_set():
                    self._log_callback("Процесс остановлен пользователем. Результат сохранён.", "orange")
                else:
                    self._log_callback("Процесс успешно завершен.", "green")
                    self._send_notification(
                        "Программа завершена",
                        "Программа завершена, проверьте файл",
                        16
                    )

                try:
                    import eel
                    eel.processingFinished(self.path_outfile, self.stop_event.is_set())
                except:
                    pass

            except Exception as e:
                self._log_callback(f"\nERROR: dsf {str(e)}", "red")
                try:
                    import eel
                    eel.processingFinished(None, True)
                except:
                    pass

        self.current_thread = threading.Thread(target=run_logic, daemon=True)
        self.current_thread.start()
        return {'success': True}

    def stop_processing(self):
        """Остановка обработки"""
        self.stop_event.set()
        self._log_callback("Отправлен сигнал остановки...", "orange")
        return {'success': True}

    def open_result_file(self):
        """Открыть файл результата"""
        if self.path_outfile:
            try:
                os.startfile(self.path_outfile)
                self._log_callback("-Файл открыт", "#788084")
                return {'success': True}
            except Exception as e:
                self._log_callback(f"Ошибка при открытии файла: {e}", "red")
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Путь к файлу не указан'}

    def open_work_table(self):
        """Переключить видимость таблицы"""
        self._table_window_open = not self._table_window_open
        return {
            'success': True,
            'is_open': self._table_window_open,
            'data': self.table_data,
            'headers': self.table_headers
        }

    def get_table_data(self):
        """Получить данные таблицы"""
        return {
            'headers': self.table_headers,
            'data': self.table_data
        }

    def get_help_text(self):
        """Получить текст справки"""
        try:
            from static.help_text import help_text as help_text_str
            return {'success': True, 'text': help_text_str}
        except Exception as e:
            return {'success': False, 'error': str(e), 'text': f"Ошибка загрузки справки:\n{str(e)}"}

    def _send_notification(self, title, message, timeout=15):
        """Отправить уведомление"""
        try:
            ico_path = self.get_resource_path('static/ico/bam-parcer-sql.ico')
            plyer.notification.notify(
                title=title,
                message=message,
                app_name='SQL Order Engine',
                timeout=timeout,
                app_icon=ico_path
            )
        except:
            pass
