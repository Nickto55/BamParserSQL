import os
import time
from tkinter import IntVar, BooleanVar
import tkinter as tk

import pandas as pd
from CTkMessagebox import CTkMessagebox
from dotenv import load_dotenv

from handlings.handling_config import ConfigSQLRecvetions
from script.excel_enter import ExcelDataInserter
from script.excel_reader import ExcelReader
from script.scr_cmd_run import ScriptCmd


class SqlParserLogic:
    def __init__(self, log_callback=None, table_callback=None, stop_event=None):
        self._load_env()
        self.config_program = ConfigSQLRecvetions()
        self.callback_gui_log = log_callback
        self.table_callback = table_callback
        self.stop_event = stop_event
        if log_callback:
            self.bool_log = True
        else:
            self.bool_log = False
        self.no_repeat = False

        self.data_dse_not_realiseted = {}

    def log_program(self, message, color_log=None, line_target=None, mode=None):
        if self.bool_log:
            self.callback_gui_log(message, color_log=color_log, line_target=line_target, mode=mode)
            # self.callback_gui_log(message, color_log=color_log)
            print(message, line_target)
        else:
            print(message)

    def _load_env(self):
        load_dotenv()
        self.sql_server = os.getenv("SQL_SERVER")
        self.sql_db = os.getenv("SQL_DB")
        self.sql_exc = os.getenv("SQL_EXC")

    def main(
            self
            , file_path
            , var_radiobutton_value_query_split: IntVar = None
            , var_bool_error_handler_inside_request_for_swith: BooleanVar = True
    ):
        data_result = {}
        self.file_path = file_path

        self.var_radiobutton_value_query_split = var_radiobutton_value_query_split
        self.var_bool_error_handler_inside_request_for_swith = var_bool_error_handler_inside_request_for_swith

        if pd.isna(var_radiobutton_value_query_split):
            self.var_radiobutton_value_query_split = IntVar(value=1)
        if self.var_radiobutton_value_query_split.get() == 1:
            self.var_bool_error_handler_inside_request_for_swith = BooleanVar(value=True)

        input_data = ExcelReader(file_path, sheet_name="Изделия")
        self.data_input_file = input_data.get_dict_all_data()

        self.filter_data()

        print('data_dse_not_realiseted')
        print(self.data_dse_not_realiseted)

        data_result[""] = self.data.copy()
        inserter = ExcelDataInserter(file_path)
        inserter.insert_data(data_result, sheet_name="Изделия")

    def filter_data(self):
        cmd_data = []
        count_dse = 0

        estimated_processing_time_for_one_request = 385
        estimated_running_program = (len(self.data_input_file) * estimated_processing_time_for_one_request) / 10
        self.log_program('')
        self.log_program('')
        self.log_program('')
        self.log_program('')

        self.time_transformations(
            estimated_running_program
            , 'Расчетное время работы программы'
            , '#F39741'
            , line_target=5
        )

        if estimated_running_program / 60 >= 30:
            if CTkMessagebox(
                    title="Продолжить?"
                    ,
                    message="Предполагаемое время работы программы, превышает 30 мин.\nЖелаете ли вы продолжить запуск"
                    , option_2='Да'
                    , option_1='Нет'
            ).get() == 'Нет':
                self.no_repeat = True

        if not self.no_repeat:
            len_data_dse = len(self.data_input_file)

            self.log_program(
                f'< |{str(count_dse):<{len(str(len_data_dse))}}/{len_data_dse}| >'
                , color_log="#847E78"
                , line_target=6
                , mode='replace'
            )

            start_time = time.perf_counter()
            count_time_to_dse = 0.0

            last_num_row = 0

            list_dse = []
            for num_row, row_reply in self.data_input_file.items():
                print(num_row,'|', row_reply.get('Дсе', ''))
                if self.stop_event and self.stop_event.is_set():
                    self.log_program("Получен сигнал остановки. Сохранение промежуточного результата...",
                                     color_log="orange")
                    break

                last_dse = False
                if self.var_radiobutton_value_query_split.get() != 11:
                    if num_row < last_num_row + self.var_radiobutton_value_query_split.get() -1:
                        if len_data_dse > num_row + self.var_radiobutton_value_query_split.get():
                            list_dse.append(row_reply.get('Дсе', ''))
                            continue
                        elif len_data_dse - 1 > num_row:
                            list_dse.append(row_reply.get('Дсе', ''))
                            continue
                        elif len_data_dse - 1 == num_row:
                            last_dse = True
                            list_dse.append(row_reply.get('Дсе', ''))
                else:
                    if len_data_dse - 1 > num_row:
                        list_dse.append(row_reply.get('Дсе', ''))
                        continue
                    elif len_data_dse - 1 == num_row:
                        last_dse = True
                        list_dse.append(row_reply.get('Дсе', ''))

                if not last_dse:
                    list_dse.append(row_reply.get('Дсе', ''))
                last_num_row = num_row
                str_dse_count_value_query_split = "".join(f"{i};" for i in list_dse)[:-1]
                list_dse = []

                stat_time_to_one_request = time.perf_counter()
                self.log_program(
                    f'Обработка дсе: {str_dse_count_value_query_split:<20} '
                    , line_target=7
                    , mode='replace'
                )

                print(f'|{str_dse_count_value_query_split}|')
                cmd_app = ScriptCmd()
                list_dse_ctr = cmd_app.main(str_dse_count_value_query_split)

                print(list_dse_ctr)
                for dse_ctr in list_dse_ctr:
                    print(dse_ctr)
                    try:
                        cmd_data.append(dse_ctr)
                        row_reply.update(
                            {
                                "ТП не в архиве": dse_ctr.get('TPNoArch', '')
                                , "ДСЕ без маршрутов": dse_ctr.get('TPNoRoot', '')
                                , "ДСЕ без основного материала": dse_ctr.get('TPNoMat', '')
                                , "Дсе без трудоемкости": dse_ctr.get('TPNoLabor', '')
                                , "Всего нет УП": dse_ctr.get('TPNoYP', '')
                                , "Наименование изделия (ИС)": dse_ctr.get('ShortName', '')
                            }
                        )
                    except Exception as error_server_read:
                        self.data_dse_not_realiseted[len(self.data_dse_not_realiseted)] = dse_ctr
                        messege_excel = 'Ошибка сервера, нет данных'
                        row_reply.update(
                            {
                                "ТП не в архиве": messege_excel
                                , "ДСЕ без маршрутов": messege_excel
                                , "ДСЕ без основного материала": messege_excel
                                , "Дсе без трудоемкости": messege_excel
                                , "Всего нет УП": messege_excel
                                , "Наименование изделия (ИС)": messege_excel
                            }
                        )
                        self.log_program(
                            f"{messege_excel}: {str_dse_count_value_query_split}",
                            color_log='#8d0914'
                            , line_target=15
                        )


                    if self.table_callback:
                        self.table_callback(row_reply)

                    count_dse += 1

                    self.log_program(
                        f'< |{str(count_dse):<{len(str(len(self.data_input_file)))}}/{len(self.data_input_file)}| >'
                        , color_log="#788084"
                        , line_target=6
                        , mode='replace'
                    )

                    count_time_to_dse += time.perf_counter() - stat_time_to_one_request
                    remaining_time = (count_time_to_dse / count_dse) * (len(self.data_input_file) - count_dse)
                    if remaining_time > 1:
                        self.time_transformations(remaining_time, 'До завершения', '#F39741')

            end_time = time.perf_counter()
            execution_time = end_time - start_time

            self.data = {}

            self.time_transformations(execution_time, 'Время обращения к базе данных', '#6e9d3c')

            for num_row, row_reply in self.data_input_file.items():
                for row_cmd in cmd_data:
                    if row_reply.get('Дсе', '') == row_cmd.get('DrawNoStr', '') and not self.no_repeat:
                        row_reply.update(
                            {
                                "ТП не в архиве": row_cmd.get('TPNoArch', '')
                                , "ДСЕ без маршрутов": row_cmd.get('TPNoRoot', '')
                                , "ДСЕ без основного материала": row_cmd.get('TPNoMat', '')
                                , "Дсе без трудоемкости": row_cmd.get('TPNoLabor', '')
                                , "Всего нет УП": row_cmd.get('TPNoYP', '')
                                , "Наименование изделия (ИС)": row_cmd.get('ShortName', '')
                            }
                        )
                    self.data[row_reply.get('Дсе', '')] = row_reply

    def time_transformations(self, sekunds_inp, text_log, color_text, line_target=8):
        minutes, sec = divmod(sekunds_inp, 60)
        hours, minutes = divmod(minutes, 60)
        if sekunds_inp / 60 > 1:
            if sekunds_inp / 3600 > 1:
                if line_target is None:
                    self.log_program(
                        f"{text_log}: {hours:.0f} ч, {minutes:.0f} мин, {sec:.2f} сек"
                        , color_log=color_text
                    )
                else:
                    self.log_program(
                        f"{text_log}: {hours:.0f} ч, {minutes:.0f} мин, {sec:.2f} сек"
                        , color_log=color_text
                        , line_target=line_target
                        , mode='replace'
                    )
            else:
                if line_target is None:
                    self.log_program(
                        f"{text_log}: {minutes:.0f} мин, {sec:.2f} сек"
                        , color_log=color_text
                    )
                else:
                    self.log_program(
                        f"{text_log}: {minutes:.0f} мин, {sec:.2f} сек"
                        , color_log=color_text
                        , line_target=line_target
                        , mode='replace'
                    )
        else:
            if line_target is None:
                self.log_program(
                    f"{text_log}: {sec:.2f} секунд"
                    , color_log=color_text
                )
            else:
                self.log_program(
                    f"{text_log}: {sec:.2f} секунд"
                    , color_log=color_text
                    , line_target=line_target
                    , mode='replace'
                )


if __name__ == "__main__":
    # path_file = input("Введите ссылку на файл отчета: ")
    root = tk.Tk()
    # path_file = r"C:\Users\yakovlev_nd\Desktop\Tests\gfgdgssd\Новая папка\26,06,01-08,31 — копия (2) — копия — копия.xlsx"
    path_file = r"C:\Users\yakovlev_nd\Desktop\Tests\gfgdgssd\Новая папка\26,06,01-08,31.xlsx"
    app = SqlParserLogic()
    app.main(
        path_file
        , var_radiobutton_value_query_split=IntVar(value=1)
        , var_bool_error_handler_inside_request_for_swith=BooleanVar(value=False)
    )
    # data = {
    #     "":
    # }.copy()
    # print(data)
    # inserter = ExcelDataInserter(path_file)
    # inserter.insert_data(data, sheet_name="Изделия")
    # input()
