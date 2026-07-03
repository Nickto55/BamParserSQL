import os
from dotenv import load_dotenv

from handlings.handling_config import ConfigSQLRecvetions
from script.excel_enter import ExcelDataInserter
from script.excel_reader import ExcelReader
from script.scr_cmd_run import ScriptCmd
import time


class MainLogic:
    def __init__(self, log_callback=None):
        self._load_env()
        self.config_program = ConfigSQLRecvetions()
        self.log_program = log_callback

    def _load_env(self):

        load_dotenv()

        self.sql_server = os.getenv("SQL_SERVER")
        self.sql_db = os.getenv("SQL_DB")
        self.sql_exc = os.getenv("SQL_EXC")

    def main(self, file_path):
        self.file_path = file_path

        input_data = ExcelReader(file_path, sheet_name="Изделия")

        self.data_input_file = input_data.get_dict_all_data()

        self.filter_data()
        return self.data

    def filter_data(self):
        cmd_data = []
        count_dse = 0
        start_time = time.perf_counter()
        self.log_program(f'< |{str(count_dse):<{len(str(len(self.data_input_file)))}}/{len(self.data_input_file)}| >',color_log="#788084")
        for num_row, row_reply in self.data_input_file.items():
            self.log_program(f'Обработка дсе: {row_reply.get('Дсе', ''):<20} ')
            cmd_app = ScriptCmd()
            dse_ctr = cmd_app.main(row_reply.get('Дсе', ''))
            cmd_data.append(dse_ctr[0])

            count_dse += 1

            self.log_program(f'< |{str(count_dse):<{len(str(len(self.data_input_file)))}}/{len(self.data_input_file)}| >',color_log="#788084")
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        self.data = {}

        minutes, sec = divmod(execution_time, 60)
        hours, minutes = divmod(minutes, 60)
        if execution_time / 60 > 1:
            if execution_time / 3600 >1:
                self.log_program(f"Время обращения к базе данных: {hours:.0f} ч, {minutes:.0f} мин, {sec:.4f} сек", color_log='#9d853c')
            else:
                self.log_program(f"Время обращения к базе данных: {minutes:.0f} мин, {sec:.4f} сек", color_log='#8d9d3c')
        else:
            self.log_program(f"Время обращения к базе данных: {sec:.4f} секунд", color_log='#6e9d3c')


        for num_row, row_reply in self.data_input_file.items():
            for row_cmd in cmd_data:
                if row_reply.get('Дсе', '') == row_cmd.get('DrawNoStr', ''):
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


if __name__ == "__main__":
    path_file = input("Введите ссылку на файл отчета: ")
    app = MainLogic()
    data = {}
    data[""] = app.main(path_file)
    # data[""] = app.main(r"C:\Users\yakovlev_nd\Desktop\Tests\gfgdgssd\26,06,01-08,31 — копия (2).xlsx")
    print(data)
    inserter = ExcelDataInserter(path_file)
    # inserter = ExcelDataInserter(r"C:\Users\yakovlev_nd\Desktop\Tests\gfgdgssd\26,06,01-08,31 — копия (2).xlsx")
    inserter.insert_data(data, sheet_name="Изделия")
    input()
