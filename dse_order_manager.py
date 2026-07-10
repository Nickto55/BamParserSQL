from scripts.excel_enter import ExcelDataInserter
from scripts.reply_script import ScriptReplyTabel

class DseOrderLogic:
    def __init__(self, log_callback=None):
        self.list_path_to_replacce_tabel = None

    def main(self, list_path_to_replacce_tabel: list):
        for path_to_replacce_tabel in list_path_to_replacce_tabel:
            app = ScriptReplyTabel()
            datas = app.main(path_to_replacce_tabel)

            inserter = ExcelDataInserter(path_to_replacce_tabel)
            inserter.insert_data(datas, sheet_name="Изделия")