import sys
import time
import queue
import plyer
import os.path
import threading
import pandas as pd
import customtkinter as ctk

from PIL import Image
from CTkTable import CTkTable
from dataclasses import fields
from PIL._tkinter_finder import tk
from tkinter import filedialog, END

from sql_order_engine import EngineLogic
from script.env_assets import HandlerEnv
from bam_parcer_sql import SqlParserLogic
from dse_order_manager import DseOrderLogic
from script.excel_return import TableTransformation
from handlings.handling_config import ConfigMainProgram


def checking_dependencies(log_callback=None):
    env = HandlerEnv()
    value = []
    for i, field in enumerate(fields(env.config)):
        value.append(getattr(env.config, field.name))

    CONFIG_DIR = os.path.join(
        os.path.expanduser("~")
        , "configs"
        , ".BamParserSQL"
    )
    file_path = os.path.join(CONFIG_DIR, ".env")

    if None in value or '' in value:
        log_callback('.env файл пуст.', color_log='red')
        log_callback(f'Путь к файлу: {file_path}', color_log='#ff8d52')
        return True
    return False


def get_resource_path(relative_path):
    """ Возвращает абсолютный путь к ресурсу, учитывая сборку PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def resource_path(relative_path):
    try:
        from PIL import Image
        source_png = "static/png/bam-parcer-sql.png"

        img = Image.open(source_png)

        icon_sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
        img.save("static/ico/app_icon.ico", sizes=icon_sizes)
        relative_path = "static/ico/app_icon.ico"
    except:
        print("Не удалось создать иконку")
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.normpath(os.path.join(base_path, relative_path))


path_to_main_ico = resource_path(r'static/ico/bam-parcer-sql.ico')


def open_fils_to_path(name):
    filepaths = filedialog.askopenfilenames(
        title=f"Выберите Excel файлы для {name}",
        filetypes=(("Excel files", "*.xlsx *.xls *.xlsm"), ("All files", "*.*"))
    )
    if not filepaths:
        return
    return filepaths


def send_notification(title, message, name_program, settime=15):
    plyer.notification.notify(title=title, message=message, app_name=name_program, timeout=settime,
                              app_icon=resource_path(path_to_main_ico))


class AppGui(ctk.CTk):

    def __init__(self):
        self.stop_event = threading.Event()  # Флаг остановки для рабочего потока
        self.config_program = ConfigMainProgram()
        self.geomitri_constants()
        super().__init__()
        self.name_program = 'SQL order engine'
        self.title(self.name_program)
        self.geometry(f"{self.window_main_x}x{self.window_main_y}")
        ctk.set_appearance_mode("dark")

        self.management_window()
        self.path_outfile = None

        self.log_queue = queue.Queue()
        self.table_queue = queue.Queue()
        self.check_stop_var = queue.Queue()

        self.check_log_queue()
        self.check_table_queue()

        checking_dependencies(log_callback=self.log)

        self.init_program()

        self.bool_button_tabel_window = False

    def init_program(self):
        self.table_window = TableWindow(self)
        from script.scr_cmd_run import ScriptCmd

        test_bd_connect = ScriptCmd(log_callback=self.log)
        if test_bd_connect.test_connection():
            time.sleep(2)
            self.log("Готов к запуску...")

    def geomitri_constants(self):
        self.window_main_x = int(self.config_program.get_size_config().get('window x', ''))
        self.window_main_y = int(self.config_program.get_size_config().get('window y', ''))

        ### SIZE
        """ indent's """
        self.indent_self = 15
        self.indent_frame = 5

        """size frames"""
        self.height_sidebar_frame = self.window_main_y - 2 * self.indent_self
        self.width_sidebar_frame = 220

        self.height_main_frame = 85
        self.width_main_frame = self.window_main_x - self.width_sidebar_frame - 3 * self.indent_self

        self.height_logs_frame = self.height_sidebar_frame - self.height_main_frame - self.indent_self
        self.width_logs_frame = self.window_main_x - self.width_sidebar_frame - 3 * self.indent_self

        """sidebar frame"""
        self.height_logo_sidebar_frame = 95
        self.width_logo_sidebar_frame = self.height_logo_sidebar_frame

        """ main frame """
        self.height_row_in_frame = 30

        self.width_path_entry = 480
        self.width_name_entry = 149

        self.width_open_button = 50

        ### POSITION
        """position frames"""
        self.pos_sidebar_frame_x = self.indent_self
        self.pos_sidebar_frame_y = self.indent_self

        self.pos_main_frame_x = self.pos_sidebar_frame_x + self.width_sidebar_frame + self.indent_self
        self.pos_main_frame_y = self.pos_sidebar_frame_y

        self.pos_logs_frame_x = self.pos_sidebar_frame_x + self.width_sidebar_frame + self.indent_self
        self.pos_logs_frame_y = self.pos_main_frame_y + self.height_main_frame + self.indent_self

    def management_window(self):
        self._sidebar_frame()
        self._main_frame()
        self._logs_frame()

    def _sidebar_frame(self):

        side_bar_frame = ctk.CTkFrame(
            self
            , width=self.width_sidebar_frame
            , height=self.height_sidebar_frame
        )
        side_bar_frame.place(x=self.pos_sidebar_frame_x, y=self.pos_sidebar_frame_y)

        icon_englie = ctk.CTkImage(
            light_image=Image.open(get_resource_path("static/png/bam-parcer-sql.png"))
            , dark_image=Image.open(get_resource_path("static/png/bam-parcer-sql.png"))
            , size=(self.height_logo_sidebar_frame, self.width_logo_sidebar_frame)
        )
        ctk.CTkButton(
            side_bar_frame
            , image=icon_englie
            , compound='top'
            , width=self.width_logo_sidebar_frame
            , height=self.height_logo_sidebar_frame
            , hover=False
            , fg_color='#2b2b2b'
        ).place(x=self.indent_frame + self.width_logo_sidebar_frame / 2, y=self.indent_frame)

        checkbox_frame = ctk.CTkFrame(
            side_bar_frame
            , width=self.width_sidebar_frame - 2 * self.indent_frame
            , height=2 * self.height_row_in_frame + 3 * self.indent_frame
            , fg_color='#1d1e1e'
        )
        checkbox_frame.place(
            x=self.indent_frame
            , y=self.width_logo_sidebar_frame + 3 * self.indent_frame
        )

        self.checkbox_dse_order = ctk.CTkCheckBox(
            checkbox_frame
            , text='Dse order manager'
            , hover=True
            , checkbox_width=12
            , checkbox_height=12
        )
        self.checkbox_dse_order.select(1)
        self.checkbox_dse_order.place(x=self.indent_frame, y=self.indent_frame)

        self.checkbox_bam_parser = ctk.CTkCheckBox(
            checkbox_frame
            , text='Bam parser SQL'
            , hover=True
            , checkbox_width=12
            , checkbox_height=12
        )
        self.checkbox_bam_parser.select(1)
        self.checkbox_bam_parser.place(x=self.indent_frame, y=self.height_row_in_frame + 2 * self.indent_frame)

        checkbox_frame_2 = ctk.CTkFrame(
            side_bar_frame
            , width=self.width_sidebar_frame - 2 * self.indent_frame
            , height=1 * self.height_row_in_frame + 2 * self.indent_frame
            , fg_color='#1d1e1e'
        )
        checkbox_frame_2.place(
            x=self.indent_frame
            ,
            y=self.width_logo_sidebar_frame + 2 * self.height_row_in_frame + 3 * self.indent_frame + 4 * self.indent_frame
        )

        self.checkbox_result = ctk.CTkCheckBox(
            checkbox_frame_2
            , text='Generate table summary'
            , hover=True
            , checkbox_width=12
            , checkbox_height=12
        )
        self.checkbox_result.select(1)
        self.checkbox_result.place(x=self.indent_frame, y=self.indent_frame)

    def _main_frame(self):
        main_frame = ctk.CTkFrame(
            self
            , width=self.width_main_frame
            , height=self.height_main_frame
        )
        main_frame.place(x=self.pos_main_frame_x, y=self.pos_main_frame_y)

        self.reply_name_entry = ctk.CTkEntry(
            main_frame
            , width=self.width_name_entry
            , height=self.height_row_in_frame
            , corner_radius=4
            , placeholder_text='Имя файла'
            , state='readonly'
            , border_color='#788084'
        )
        self.reply_name_entry.place(x=5, y=5)
        self.reply_name_entry.configure(text_color='#9aa5aa', state='normal')
        self.reply_name_entry.delete(0, END)
        self.reply_name_entry.insert(0, 'Файл')
        self.reply_name_entry.configure(state='readonly')

        self.reply_path_entry = ctk.CTkEntry(
            main_frame
            , width=self.width_path_entry
            , height=self.height_row_in_frame
            , corner_radius=4
            , placeholder_text='Введите путь к файлу/файлам отчетов'
            , border_color='#788084'
        )
        self.reply_path_entry.place(x=self.width_name_entry + 2 * self.indent_frame, y=5)

        self.button_open_folder_reply = ctk.CTkButton(
            main_frame
            , text='Открыть'
            , width=self.width_open_button
            , height=self.height_row_in_frame
            , command=lambda: self.button_path_commands(label_batton='reply')
            , fg_color="#343638"
            , hover_color="#9aa5aa"
        )
        self.button_open_folder_reply.place(x=self.width_name_entry + self.width_path_entry + 3 * self.indent_frame,
                                            y=self.indent_frame)

        self.start_button = ctk.CTkButton(
            main_frame
            , width=72
            , height=self.height_row_in_frame
            , text="Начать"
            , fg_color="green"
            , hover_color="darkgreen"
            , command=self.run_manager_thread
        )
        self.start_button.place(
            x=self.width_name_entry + self.width_path_entry + 9
            , y=self.height_row_in_frame + 2 * self.indent_frame + 1
        )

        self.button_open_result_tabel = ctk.CTkButton(
            main_frame
            , width=100
            , height=self.height_row_in_frame
            , text="Открыть результат"
            , command=self.command_button_open_result
            , fg_color='#b69765'
            , hover_color='#8f764f'
        )

        self.button_open_work_tabel = ctk.CTkButton(
            main_frame
            , width=100
            , height=self.height_row_in_frame
            , text='Таблица обр. дсе'
            , command=self.command_button_open_work
            , fg_color='#b69765'
            , hover_color='#8f764f'
        )
        self.button_open_work_tabel.place(
            x=self.indent_frame
            , y=self.height_row_in_frame + 2 * self.indent_frame + 1
        )

        self.button_stop_program = ctk.CTkButton(
            main_frame
            , height=self.height_row_in_frame
            , width=40
            , text='Прекратить, сохранить результат'
            , fg_color='#a93c22'
            , hover_color='#752917'
            , command=self.stop_execution  # БЕЗ скобок!
        )
        self.button_stop_program.place(
            x=415
            , y=self.height_row_in_frame + 2 * self.indent_frame + 1
        )

        self.progress_bar = ctk.CTkProgressBar(
            main_frame
            , width=self.width_main_frame - 2 * self.indent_frame
            , height=6
            , corner_radius=3
            , fg_color='#2b2b2b'
            , progress_color='#00aaff'
            , mode='indeterminate'
        )
        self.progress_bar.place(
            x=self.indent_frame
            , y=self.height_main_frame - self.indent_frame - 6
        )
        self.progress_bar.set(0)
        self.progress_bar.place_forget()

    def _logs_frame(self):
        logs_frame = ctk.CTkFrame(
            self
            , width=self.width_logs_frame
            , height=self.height_logs_frame
        )
        logs_frame.place(x=self.pos_logs_frame_x, y=self.pos_logs_frame_y)

        self.status_text = ctk.CTkTextbox(
            logs_frame
            , width=self.width_logs_frame - 2 * self.indent_frame
            , height=self.height_logs_frame - 2 * self.indent_frame
        )
        self.status_text.place(x=self.indent_frame, y=self.indent_frame)

    def stop_execution(self):
        """Отправляет сигнал остановки в рабочий поток"""
        self.stop_event.set()
        self.log("Отправлен сигнал остановки...", color_log="orange")
        self.button_stop_program.configure(state="disabled", text="Остановка...")

    def command_button_open_work(self):
        if self.bool_button_tabel_window:
            self.table_window.destroy()
        else:
            self.table_window = TableWindow(self)

        self.bool_button_tabel_window = not self.bool_button_tabel_window

    def command_button_stop(self):
        """Проверяет очередь таблицы и обновляет GUI в главном потоке"""
        try:
            while True:
                row_data = self.check_stop_var.get_nowait()
                self.table_window.add_row(row_data)
        except queue.Empty:
            pass
        finally:
            self.after(50, self.command_button_stop)

    def command_button_open_result(self):
        if not self.path_outfile is None:
            self.start_button.configure(state="disabled")
            self.button_open_result_tabel.configure(fg_color='green', hover_color='darkgreen')

            def merge_color():
                self.button_open_result_tabel.configure(fg_color='#8f764f', hover_color='#5c4b32')

            self.button_open_result_tabel.after(1000, merge_color)

            try:
                os.startfile(self.path_outfile)
                self.log("-Файл открыт", color_log="#788084")
            except Exception as e:
                self.log(f"Ошибка при открытии файла: {e}", color_log="red")
                self.start_button.configure(state="normal")
                return

            try:
                send_notification(
                    f"Файл открыт: {os.path.basename(self.path_outfile).replace('.xlsx', '')}"
                    , ""
                    , self.name_program
                    , 16
                )
            except:
                send_notification(
                    f"Файл открыт: {os.path.basename(self.path_outfile)}"
                    , ""
                    , self.name_program
                    , 16
                )
            self.button_open_result_tabel.after(5000, self.start_button.configure(state="normal"))
        else:
            self.log("Ошибка при открытии файла, отсссуствует путь", color_log="red")
            self.button_open_result_tabel.place_forget()

    def button_path_commands(self, label_batton: str):
        if label_batton == 'reply':

            path_list_filr = list(open_fils_to_path(name='отчетов'))

            str_paths = ""
            for path in path_list_filr: str_paths += f"{path}, "
            str_paths = str_paths[:-2]

            self.reply_path_entry.delete(0, END)
            self.reply_path_entry.insert(0, str_paths)

            self.reply_name_entry.configure(text_color='#fff', state='normal')
            self.reply_name_entry.delete(0, END)
            self.reply_name_entry.insert(0, os.path.basename(str_paths))
            self.reply_name_entry.configure(state='readonly')

            self.start_button.configure(state="normal")
            self.log(f"<Установлен путь для файла отчетов>", color_log='#9aa5aa')
            self.reply_path_entry.configure(border_color='#788084')
            self.reply_name_entry.configure(border_color='#788084')

    def check_table_queue(self):
        """Проверяет очередь таблицы и обновляет GUI в главном потоке"""
        try:
            while True:
                row_data = self.table_queue.get_nowait()
                self.table_window.add_row(row_data)
        except queue.Empty:
            pass
        finally:
            self.after(50, self.check_table_queue)

    def table_callback(self, row_data):
        """Колбэк для передачи данных из фонового потока в очередь"""
        self.table_queue.put(row_data)

    def check_log_queue(self):
        """Проверяет очередь логов и выводит в GUI"""
        try:
            while True:
                message, color_log, line_target, mode = self.log_queue.get_nowait()
                self._log_to_gui(message, color_log, line_target, mode)
        except queue.Empty:
            pass
        finally:
            self.after(50, self.check_log_queue)

    def _log_to_gui(self, message, color_log=None, line_target=None, mode='append'):
        if line_target is not None:
            line_pos = f"{line_target}.0"
            line_end = f"{line_target}.end"

            try:
                self.status_text.index(line_end)
            except tk.TclError:
                current_lines = int(self.status_text.index('end-1c').split('.')[0])
                for _ in range(line_target - current_lines + 1):
                    self.status_text.insert("end", "\n")

            if mode == 'replace':
                self.status_text.delete(line_pos, line_end)
                self.status_text.insert(line_pos, message)
            else:
                current_end = self.status_text.index(line_end)
                line_content = self.status_text.get(line_pos, line_end)
                if line_content.endswith('\n'):
                    insert_pos = f"{line_target}.{len(line_content) - 1}"
                else:
                    insert_pos = line_end
                self.status_text.insert(insert_pos, message)

            if color_log:
                tag_name = f"color_{color_log}_{line_target}"
                self.status_text.tag_config(tag_name, foreground=color_log)
                self.status_text.tag_add(tag_name, line_pos, line_end)
        else:
            self.status_text.insert("end", f"{message}\n")

            if color_log:
                end_index = self.status_text.index("end-1c")
                line_num = end_index.split('.')[0]
                start_pos = f"{int(line_num) - 1}.0"
                end_pos = f"{int(line_num) - 1}.end"
                tag_name = f"color_{color_log}"
                self.status_text.tag_config(tag_name, foreground=color_log)
                self.status_text.tag_add(tag_name, start_pos, end_pos)

        self.status_text.see("end")

    def log(self, message, color_log=None, line_target=None, mode='append'):
        self.log_queue.put((message, color_log, line_target, mode))

    def run_manager_thread(self):
        """Запуск в отдельном потоке, чтобы GUI не зависал"""
        self.button_open_result_tabel.place_forget()
        self.start_button.configure(state="disabled")
        self.button_stop_program.configure(state="normal", text='Прекратить, сохранить результат')
        self.stop_event.clear()

        if pd.isna(self.reply_path_entry.get()):
            self.log("Ошибка, укажите путь к файлу", color_log="red")
            self.start_button.configure(state="normal")
            return

        self.progress_bar.place(
            x=self.indent_frame
            , y=self.height_main_frame - self.indent_frame - 6
        )
        self.progress_bar.start()

        thread = threading.Thread(target=self.execute_logic, daemon=True)
        thread.start()

    def execute_logic(self):
        self.path_outfile = None
        if checking_dependencies(log_callback=self.log):
            return
        if pd.isna(self.reply_path_entry.get()) or self.reply_path_entry.get() == "":
            self.log("Введите путь к файлу", color_log='red')
            self.reply_path_entry.configure(border_color="red")
            self.reply_name_entry.configure(border_color="red")
            self.start_button.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.place_forget()
            return
        else:
            self.reply_path_entry.configure(border_color='#788084')
            self.reply_name_entry.configure(border_color='#788084')

        self.log("Начало работы...")

        try:
            self.path_outfile = None
            if self.checkbox_dse_order.get() and self.checkbox_bam_parser.get():
                manager = EngineLogic(
                    log_callback=self.log,
                    table_callback=self.table_callback,
                    stop_event=self.stop_event
                )
                manager.main(self.reply_path_entry.get())
            elif self.checkbox_dse_order.get() and not self.checkbox_bam_parser.get():
                manager = DseOrderLogic()
                manager.main(self.reply_path_entry.get())
            elif not self.checkbox_dse_order.get() and self.checkbox_bam_parser.get():
                manager = SqlParserLogic(
                    log_callback=self.log,
                    table_callback=self.table_callback,
                    stop_event=self.stop_event
                )
                manager.main(self.reply_path_entry.get())
            else:
                self.log(f'Произошла ошибка: {self.checkbox_dse_order.get()} {self.checkbox_bam_parser.get()}')

            if self.checkbox_result.get():
                result = TableTransformation(self.reply_path_entry.get())
                result.main()
            self.path_outfile = self.reply_path_entry.get()
            self.button_open_result_tabel.place(
                x=self.width_path_entry + 22
                , y=self.height_row_in_frame + 2 * self.indent_frame + 1
            )

            if self.stop_event.is_set():
                self.log("Процесс остановлен пользователем. Результат сохранён.", color_log="orange")
            else:
                self.log("Процесс успешно завершен.", color_log="green")
                send_notification(
                    "Программа завершена"
                    , "Программа завершена , проверте файл"
                    , self.name_program
                    , 16
                )

            self.start_button.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.place_forget()
            self.button_stop_program.configure(state="normal", text='Прекратить, сохранить результат')

        except Exception as e:
            self.log(f"\nERROR GUI:", color_log="red")
            self.log(f" {str(e)}", color_log="red")
        finally:
            self.start_button.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.place_forget()
            self.button_stop_program.configure(state="normal", text='Прекратить, сохранить результат')


class TableWindow(ctk.CTkToplevel):
    def __init__(self, param):
        super().__init__(param)
        self.title('Полученные данные')
        self.geometry('1565x600')

        self.headers = [
            "Дсе", "ТП не в архиве", "ДСЕ без маршрутов",
            "ДСЕ без основного материала", "Дсе без трудоемкости",
            "Всего нет УП", "Наименование изделия (ИС)"
        ]

        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            width=1525,
            height=560
        )
        self.scroll_frame.pack(expand=True, fill='both', padx=20, pady=20)

        self.tabel_data = [self.headers]

        self.table = CTkTable(
            master=self.scroll_frame,
            row=1,
            column=len(self.headers),
            values=self.tabel_data,
            hover_color="#2A2A2A",
            header_color="#1f538d",
            wraplength=200
        )
        self.table.pack(expand=True, fill='both')

        self._row_count = 1

    def add_row(self, row_data):
        """Добавляет новую строку в таблицу без полного пересоздания"""
        row_list = [str(row_data.get(col, "")) for col in self.headers]
        self.tabel_data.append(row_list)

        try:
            if hasattr(self.table, 'add_row'):
                self.table.add_row(values=row_list)
                self._row_count += 1
            elif hasattr(self.table, 'insert_row'):
                self.table.insert_row(self._row_count, values=row_list)
                self._row_count += 1
            else:
                self._rebuild_table()
        except Exception:
            self._rebuild_table()

    def _rebuild_table(self):
        """Пересоздание таблицы (только при необходимости)"""
        self.table.destroy()
        self.table = CTkTable(
            master=self.scroll_frame,
            row=len(self.tabel_data),
            column=len(self.headers),
            values=self.tabel_data,
            hover_color="#2A2A2A",
            header_color="#1f538d",
            wraplength=200
        )
        self.table.pack(expand=True, fill='both')
        self._row_count = len(self.tabel_data)

    def clear(self):
        """Очищает таблицу, оставляя только заголовки"""
        self.tabel_data = [self.headers]
        self._rebuild_table()

    def refresh_last_row(self, row_data):
        """Обновляет последнюю добавленную строку"""
        if len(self.tabel_data) > 1:
            row_list = [str(row_data.get(col, "")) for col in self.headers]
            self.tabel_data[-1] = row_list
            try:
                if hasattr(self.table, 'edit_row'):
                    self.table.edit_row(self._row_count - 1, values=row_list)
                else:
                    self._rebuild_table()
            except Exception:
                self._rebuild_table()


if __name__ == "__main__":
    app = AppGui()
    app.mainloop()
