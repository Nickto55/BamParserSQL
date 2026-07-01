import os.path
import sys
import threading
import customtkinter as ctk
import plyer

from tkinter import filedialog, END
from bam_parcer_sql import MainLogic
from handlings.handling_config import ConfigMainProgram

import pandas as pd

from script.excel_enter import ExcelDataInserter
from dotenv import load_dotenv

def resource_path(relative_path):
    try:
        from PIL import Image
        source_png = "static/png/bam-parcer-sql.png"

        # 2. Открываем изображение
        img = Image.open(source_png)

        # 3. Список обязательных размеров для Windows
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
        self.config_program = ConfigMainProgram()
        self.geomitri_constants()
        super().__init__()
        self.name_program = self.config_program.get_all_config_program().get('name', '')
        self.title(self.name_program)
        self.geometry(f"{self.window_main_x}x{self.window_main_y}")
        ctk.set_appearance_mode("dark")

        self.management_window()
        self.path_outfile = None


    #     self.init_program()
    # def init_program(self):
    #     load_dotenv()
    #     print('sql_server', os.getenv("SQL_SERVER"))
    #     print('sql_db', os.getenv("SQL_DB"))
    #     print('sql_exc', os.getenv("SQL_EXC"))

    def geomitri_constants(self):
        self.window_main_x = int(self.config_program.get_size_config().get('window x', ''))
        self.window_main_y = int(self.config_program.get_size_config().get('window y', ''))

        """ indent's """
        self.indent_self = 15
        self.indent_frame = 5

        """ main frame """
        self.height_main_frame = 85
        self.height_row_in_frame = 30

        self.width_path_entry = 480
        self.width_name_entry = 149

        self.width_open_button = 50

    def management_window(self):
        main_frame = ctk.CTkFrame(
            self
            , width=self.window_main_x - 2 * self.indent_self
            , height=self.height_main_frame
        )
        main_frame.place(x=self.indent_self, y=self.indent_self)

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

        self.batton_open_result_tabl = ctk.CTkButton(
            main_frame
            , width=100
            , height=self.height_row_in_frame
            , text="Открыть результат"
            , command=self.command_batton_open_result
            , fg_color='#b69765'
            , hover_color='#8f764f'
        )

        self.progress_bar = ctk.CTkProgressBar(
            main_frame
            , width=self.window_main_x - 2 * self.indent_self - 2 * self.indent_frame
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

        logs_frame = ctk.CTkFrame(
            self
            , width=self.window_main_x - 2 * self.indent_self
            , height=self.window_main_y - 3 * self.indent_self - self.height_main_frame
        )
        logs_frame.place(x=self.indent_self, y=2 * self.indent_self + self.height_main_frame)

        self.status_text = ctk.CTkTextbox(
            logs_frame
            , width=self.window_main_x - 2 * self.indent_self - 2 * self.indent_frame
            , height=self.window_main_y - 3 * self.indent_self - self.height_main_frame - 2 * self.indent_frame
        )
        self.status_text.place(x=self.indent_frame, y=self.indent_frame)
        self.status_text.insert("0.0", "Готов к запуску...\n")

    def command_batton_open_result(self):
        if not self.path_outfile is None:
            self.start_button.configure(state="disabled")
            self.batton_open_result_tabl.configure(fg_color='green', hover_color='darkgreen')

            def merge_color():
                self.batton_open_result_tabl.configure(fg_color='#8f764f', hover_color='#5c4b32')

            self.batton_open_result_tabl.after(1000, merge_color)

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
            self.batton_open_result_tabl.after(5000, self.start_button.configure(state="normal"))
        else:
            self.log("Ошибка при открытии файла, отсссуствует путь", color_log="red")
            self.batton_open_result_tabl.place_forget()

    def button_path_commands(self, label_batton: str):
        if label_batton == 'reply':
            # noinspection PyTypeChecker
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

    def log(self, message, color_log=None):
        """Вывод логов в текстовое поле GUI с цветом"""
        self.status_text.insert("end", f"{message}\n")

        if color_log:
            # Получаем позицию только что вставленной строки
            end_index = self.status_text.index("end-1c")
            line_num = end_index.split('.')[0]
            start_pos = f"{int(line_num) - 1}.0"
            end_pos = f"{int(line_num) - 1}.end"

            # Создаём/настраиваем тег и применяем
            tag_name = f"color_{color_log}"
            self.status_text.tag_config(tag_name, foreground=color_log)
            self.status_text.tag_add(tag_name, start_pos, end_pos)

        self.status_text.see("end")

    def run_manager_thread(self):
        """Запуск в отдельном потоке, чтобы GUI не зависал"""
        self.batton_open_result_tabl.place_forget()
        self.start_button.configure(state="disabled")

        if pd.isna(self.reply_path_entry.get()):
            self.log("Ошибка, укажите путь к файлу", color_log="red")
            self.start_button.configure(state="normal")
            return

        # ===== ПОКАЗЫВАЕМ И ЗАПУСКАЕМ ПРОГРЕСС БАР =====
        self.progress_bar.place(
            x=self.indent_frame
            , y=self.height_main_frame - self.indent_frame - 6
        )
        self.progress_bar.start()  # запускаем анимацию
        # ================================================

        thread = threading.Thread(target=self.execute_logic, daemon=True)
        thread.start()

    def execute_logic(self):
        self.path_outfile = None
        if pd.isna(self.reply_path_entry.get()) or self.reply_path_entry.get() == "":
            self.log("Введите путь к файлу", color_log='red')
            self.reply_path_entry.configure(border_color="red")
            self.start_button.configure(state="normal")

            # ===== СКРЫВАЕМ ПРОГРЕСС БАР =====
            self.progress_bar.stop()
            self.progress_bar.place_forget()
            # ==================================

            return
        else:
            self.reply_path_entry.configure(border_color='#788084')

        self.log("Запуск программы...")
        try:
            self.path_outfile = None
            manager = MainLogic()
            data_result = {}

            data_result[""] = manager.main(self.reply_path_entry.get())
            self.path_outfile = self.reply_path_entry.get()

            inserter = ExcelDataInserter(self.path_outfile)
            inserter.insert_data(data_result, sheet_name="Изделия")

            self.batton_open_result_tabl.place(
                x=self.width_path_entry + 22
                , y=self.height_row_in_frame + 2 * self.indent_frame + 1
            )
            self.log("Процесс успешно завершен.", color_log="green")
            send_notification(
                "Программа завершена"
                , "Программа завершена , проверте файл"
                , self.name_program
                , 16
            )
            self.start_button.configure(state="normal")
        except Exception as e:
            self.log(f"ERROR: {str(e)}", color_log="red")
        finally:
            self.start_button.configure(state="normal")
            # ===== ОСТАНАВЛИВАЕМ И СКРЫВАЕМ ПРОГРЕСС БАР =====
            self.progress_bar.stop()
            self.progress_bar.place_forget()
            # ==================================================


if __name__ == "__main__":
    app = AppGui()
    app.mainloop()