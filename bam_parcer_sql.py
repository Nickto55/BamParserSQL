import os
from dotenv import load_dotenv

from handlings.handling_config import ConfigSQLRecvetions
from script.excel_enter import ExcelDataInserter
from script.excel_reader import ExcelReader
from script.scr_cmd_run import ScriptCmd
import time


class MainLogic:
    def __init__(self):
        self._load_env()
        self.config_program = ConfigSQLRecvetions()

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
        for num_row,row_reply in self.data_input_file.items():
            print(f'Обработка дсе: {row_reply.get('Дсе',''):<20} ', end='')
            cmd_app = ScriptCmd()
            dse_ctr = cmd_app.main(row_reply.get('Дсе',''))
            cmd_data.append(dse_ctr[0])

            count_dse +=1

            print(f'прошла. |{str(count_dse):<{len(str(len(self.data_input_file)))}}/{len(self.data_input_file)}|')
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        # str_dse_into_reply = str_dse_into_reply[1:]
        # cmd_app = ScriptCmd()
        # cmd_data = cmd_app.main(str_dse_into_reply)
        self.data = {}
        print(cmd_data)
        print(f"Время обращения к базе данных: {execution_time:.4f} секунд")
        # cmd_data = [{'DrawNoStr': 'ЛТИЯ.464132.001-30', 'ShortName': 'Автоматическая радиопередающая система стационарного радиоцентра КВ-диапазона АРПС-20', 'TPNoArch': 1768, 'TPNoRoot': 18, 'TPNoMat': 1, 'TPNoLabor': 1, 'TPNoYP': 31}, {'DrawNoStr': 'ЛТИЯ.464639.001-01', 'ShortName': 'Антенно-мачтовое устройство на базе шасси МАО-22М', 'TPNoArch': 1028, 'TPNoRoot': 0, 'TPNoMat': 0, 'TPNoLabor': 6, 'TPNoYP': 16}, {'DrawNoStr': 'ЛТИЯ.464531.001', 'ShortName': 'Автоматизированная станция помех КВ-радиосвязи оперативно-тактического звена управления РБ-312А', 'TPNoArch': 3260, 'TPNoRoot': 7, 'TPNoMat': 5, 'TPNoLabor': 11, 'TPNoYP': 31}]
        for num_row,row_reply in self.data_input_file.items():
           for row_cmd in cmd_data:
               if row_reply.get('Дсе','') == row_cmd.get('DrawNoStr',''):
                   row_reply.update(
                       {
                           "ТП не в архиве":row_cmd.get('TPNoArch','')
                           ,"ДСЕ без маршрутов":row_cmd.get('TPNoRoot','')
                           ,"ДСЕ без основного материала":row_cmd.get('TPNoMat','')
                           ,"Дсе без трудоемкости":row_cmd.get('TPNoLabor','')
                           ,"Всего нет УП":row_cmd.get('TPNoYP','')
                           , "Наименование изделия": row_cmd.get('ShortName', '')
                       }
                   )
               # else:
               #     print('_____________________________________________')
               #     print('Не удалось соеденить значения')
               #     print(row_reply.get('Дсе',''),row_cmd.get('DrawNoStr',''))
               self.data[row_reply.get('Дсе','')] = row_reply






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