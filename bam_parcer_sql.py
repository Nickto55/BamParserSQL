import os
import random
import time

from CTkMessagebox import CTkMessagebox
from dotenv import load_dotenv

from handlings.handling_config import ConfigSQLRecvetions
from script.excel_enter import ExcelDataInserter
from script.excel_reader import ExcelReader
from script.scr_cmd_run import ScriptCmd


class SqlParserLogic:
    def __init__(self, log_callback=None, table_callback=None):
        self._load_env()
        self.config_program = ConfigSQLRecvetions()
        self.callback_gui_log = log_callback
        self.table_callback = table_callback
        if log_callback:
            self.bool_log = True
        else:
            self.bool_log = False
        self.no_repeat = False

    def log_program(self, message, color_log=None, line_target=None, mode=None):
        """
                Публичный метод логирования — можно вызывать из любого потока

                Args:
                    message: текст сообщения
                    color_log: цвет текста
                    line_target: номер строки (1-based), None = в конец
                    mode: 'append' или 'replace'
                """
        if self.bool_log:
            self.callback_gui_log(message, color_log=color_log, line_target=line_target, mode=mode)
        else:
            print(message)

    def _load_env(self):

        load_dotenv()

        self.sql_server = os.getenv("SQL_SERVER")
        self.sql_db = os.getenv("SQL_DB")
        self.sql_exc = os.getenv("SQL_EXC")

    def main(self, file_path):
        """

        :param file_path: str - путь к файлу
        :return:
        """
        data_result = {}
        self.file_path = file_path

        input_data = ExcelReader(file_path, sheet_name="Изделия")

        self.data_input_file = input_data.get_dict_all_data()

        self.filter_data()

        data_result[""] = self.data.copy()
        inserter = ExcelDataInserter(file_path, self.callback_gui_log)
        inserter.insert_data(data_result, sheet_name="Изделия")

    def filter_data(self):
        cmd_data = []
        count_dse = 0

        estimated_processing_time_for_one_request = 385  # среднее время на обработку одного запроса, в мсек
        # предполагаемое время работы программы
        estimated_running_program = (len(self.data_input_file) * estimated_processing_time_for_one_request) / 10

        self.time_transformations(
            estimated_running_program
            , 'Расчетное время работы программы'
            , '#F39741'
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
            self.log_program(
                f'\n < |{str(count_dse):<{len(str(len(self.data_input_file)))}}/{len(self.data_input_file)}| >\n'
                , color_log="#847E78"
                , line_target=10
                , mode='replace'
            )
            self.log_program('')

            start_time = time.perf_counter()
            count_time_to_dse = 0.0
            for num_row, row_reply in self.data_input_file.items():
                stat_time_to_one_request = time.perf_counter()
                self.log_program(
                    f'Обработка дсе: {row_reply.get('Дсе', ''):<20} '
                    , line_target=11
                    , mode='replace'
                )
                ##------------------------
                # time.sleep(random.randint(0, 1))
                # cmd_data.append(i for i in range(12))
                # dse_ctr = [{}]
                ##------------------------
                cmd_app = ScriptCmd()
                dse_ctr = cmd_app.main(row_reply.get('Дсе', ''))
                try:
                    cmd_data.append(dse_ctr[0])
                    row_reply.update(
                        {
                            "ТП не в архиве": dse_ctr[0].get('TPNoArch', '')
                            , "ДСЕ без маршрутов": dse_ctr[0].get('TPNoRoot', '')
                            , "ДСЕ без основного материала": dse_ctr[0].get('TPNoMat', '')
                            , "Дсе без трудоемкости": dse_ctr[0].get('TPNoLabor', '')
                            , "Всего нет УП": dse_ctr[0].get('TPNoYP', '')
                            , "Наименование изделия (ИС)": dse_ctr[0].get('ShortName', '')
                        }
                    )
                except Exception as error_server_read:
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
                        f"{messege_excel}: {row_reply.get('Дсе', '')}",
                        color_log='#8d0914'
                        , line_target=15
                    )
                if self.table_callback:
                    self.table_callback(row_reply)
                count_dse += 1

                self.log_program(
                    f'< |{str(count_dse):<{len(str(len(self.data_input_file)))}}/{len(self.data_input_file)}| >'
                    , color_log="#788084"
                    , line_target=10
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
            self.log_program('')

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

    def time_transformations(self, sekunds_inp, text_log, color_text, line_target=12):
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
    path_file = input("Введите ссылку на файл отчета: ")
    app = SqlParserLogic()
    data = {}
    data[""] = app.main(path_file)
    # data[""] = app.main(r"C:\Users\yakovlev_nd\Desktop\Tests\gfgdgssd\26,06,01-08,31 — копия (2).xlsx")
    print(data)
    inserter = ExcelDataInserter(path_file)
    # inserter = ExcelDataInserter(r"C:\Users\yakovlev_nd\Desktop\Tests\gfgdgssd\26,06,01-08,31 — копия (2).xlsx")
    inserter.insert_data(data, sheet_name="Изделия")
    input()
