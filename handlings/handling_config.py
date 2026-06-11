from CTkMessagebox import CTkMessagebox

from script.config_assets import HandlerConfig


class ConfigMainProgram:
    def __init__(self):
        self.data_base = HandlerConfig()

    def get_all_config_program(self):
        self.data_base.load()
        return self.data_base.data.get('program', '')

    def set_config_progrm(self,key,data):
        if key in self.data_base.data.get('program','').keys():
            self.data_base.data['program'][key]=data
            self.data_base.save()
            self.data_base.load()

    def get_size_config(self):
        self.data_base.load()
        return self.data_base.data['program'].get('size', '')


    def set_size_config(self, key_name_file, path_to_file):
        data = self.data_base.data['program'].get('size', '')
        if key_name_file in data.keys():
            self.data_base.data['program']["size"][key_name_file] = path_to_file
            self.data_base.save()
            self.data_base.load()
        else:
            print(
                f"Данного ключа('{key_name_file}') нет в словаре 'size', возможные варианты {list(data.keys())}")
            CTkMessagebox(title="Не критическая ошибка",
                          message=f"Ошибка при записи размера\nКлюча ('{key_name_file}') нет в словаре 'size'\nПуть к файлу не сохранен",
                          icon="warning", option_1="Не сохранять путь")

class ConfigSQLRecvetions:
    def __init__(self):
        self.data_base = HandlerConfig()

    def get_output_file(self):
        self.data_base.load()
        return self.data_base.data['handling cmd'].get('output file', '')

    def get_all_config_cmd(self):
        self.data_base.load()
        return self.data_base.data.get('handling cmd', '')

    def set_config_cmd(self,key,data):
        if key in self.data_base.data.get('handling cmd','').keys():
            self.data_base.data['handling cmd'][key]=data
            self.data_base.save()
            self.data_base.load()



if __name__ == "__main__":
    app = ConfigMainProgram()
    print(app.get_all_config_program())
    # app12.mainloop()
