import datetime

import pandas as pd

from script.excel_reader import ExcelReader
from script.excel_enter import ExcelDataInserter


class TableTransformation:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.data_return = {}

    def main(self):
        reader = ExcelReader(self.file_path, sheet_name='Изделия')
        self.data = reader.get_dict_all_data()
        if pd.isna(self.data):
            return

        for num, row in self.data.items():
            self.data_return.update(
                {
                    num: {
                        'Дсе': row.get('Дсе', '')
                        , 'Наименование изделия (ИС)': row.get('Наименование изделия (ИС)', '')
                        , 'ТП не в архиве': row.get('ТП не в архиве', '')
                        , 'ДСЕ без маршрутов': row.get('ДСЕ без маршрутов', '')
                        , 'ДСЕ без основного материала': row.get('ДСЕ без основного материала', '')
                        , 'Дсе без трудоемкости': row.get('Дсе без трудоемкости', '')
                        , 'Всего нет УП': row.get('Всего нет УП', '')
                    }
                }
            )

        writer_excel = ExcelDataInserter(self.file_path)
        writer_excel.insert_data(data={'':self.data_return}, sheet_name=f'Итог {str(datetime.date.today()).replace('-','.')}')




if __name__ == '__main__':
    app = TableTransformation(r"C:\Users\yakovlev_nd\Desktop\Tests\gfgdgssd\Новая папка\26,06,01-08,31.xlsx")
    app.main()
