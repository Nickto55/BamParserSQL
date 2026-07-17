from CTkMessagebox import CTkMessagebox

from bam_parcer_sql import SqlParserLogic
from dse_order_manager import DseOrderLogic

from script.excel_reader import ExcelReader


class EngineLogic:
    def __init__(self, log_callback=None, table_callback = None):
        self.path_to_file = None

        self.sheet_names = None

        self.callback_gui_log = log_callback
        if log_callback:
            self.bool_log = True
        else:
            self.bool_log = False

        self.bam_parser_sql = SqlParserLogic(log_callback, table_callback)
        self.dse_order_manager = DseOrderLogic(log_callback)

    def log_program(self, message, color_log=None):
        if self.bool_log:
            if color_log:
                self.callback_gui_log(message, color_log=color_log)
            else:
                self.callback_gui_log(message)
        else:
            print(message)

    def main(self, path_to_file: str):
        self.path_to_file = path_to_file
        reader_file = ExcelReader(path_to_file)

        self.sheet_names = reader_file.sheet_names
        if len(self.sheet_names) > 0:
            if 'Изделия' in self.sheet_names:
                self.log_program('Обнаружен лист "Изделия"', color_log="#ACA6A0")
                self.log_program('<запуск Bam parser SQL>', color_log='#847E78')
                try:
                    self.bam_parser_sql.main(self.path_to_file)
                except Exception as e:
                    self.log_program(f'Error EngineLogic main sheet in file: {e}', color_log='red')
            else:
                self.log_program('Лист "Изделия" не обнаружен', color_log='#ACA6A0')
                self.log_program('<запуск Dse order manager>', color_log='#847E78')
                try:
                    self.dse_order_manager.main(self.path_to_file)
                    self.log_program('<запуск Bam parser SQL>', color_log='#847E78')
                    self.bam_parser_sql.main(self.path_to_file)
                except Exception as e:
                    self.log_program(f'Обработчик SQl parser engine.', color_log='red')
                    self.log_program(f'Error EngineLogic main: {e}', color_log='red')




if __name__ == '__main__':
    app = EngineLogic()
    data = app.main(r"C:\Users\yakovlev_nd\Desktop\Tests\gfgdgssd\Новая папка\26,06,01-08,31eeej — копия — копия.xlsx")

    for i, k in data.items():
        print(i, k)
