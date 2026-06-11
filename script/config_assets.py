import json
import os
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog

from static.config import configProgram


class HandlerConfig:
    def __init__(self):
        """
        Обработчик базы данных
        """
        self.name_programm_config_dir = ".BamParserSQL"

        self.CONFIG_DIR = os.path.join(os.path.expanduser("~"), os.path.join('configs', self.name_programm_config_dir))
        self.file_path = os.path.join(self.CONFIG_DIR, "config.json")
        self.data = configProgram

        self.transferring_config()
        self._ensure_file_exists()
        self.load()

    def save(self):
        """Сохраняет текущие данные в файл."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        self.load()

    def transferring_config(self):
        try:
            if self.name_programm_config_dir in os.listdir(
                    os.path.expanduser("~")) and not self.name_programm_config_dir in os.listdir(
                os.path.join(os.path.expanduser("~"), 'configs')):
                shutil.copytree(os.path.join(os.path.expanduser("~"), self.name_programm_config_dir),
                                os.path.dirname(self.file_path))
        except:
            pass

    def _ensure_file_exists(self):
        """Создаёт файл и структуру данных, если их нет."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)

    def load(self):
        """Загружает данные из файла."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("Config файл пуст")

    def recoveryLoseKeyAndValue(self):
        """
        Восстанавливает отсутствующие ключи и значения из шаблона configProgram.
        Сравнивает текущие данные с шаблоном и добавляет недостающие элементы.
        """

        def _merge_missing(current, template, path=""):
            """
            Рекурсивно сравнивает текущие данные с шаблоном и добавляет недостающее.
            """
            changes_made = False

            if isinstance(template, dict):
                if not isinstance(current, dict):
                    # Если текущее значение не словарь, заменяем его полностью
                    print(f"Recovery: replacing non-dict at '{path}' with template dict")
                    return template, True

                for key, template_value in template.items():
                    current_path = f"{path}.{key}" if path else key

                    if key not in current:
                        # Ключ отсутствует — добавляем из шаблона
                        print(f"Recovery: missing key '{current_path}' added")
                        current[key] = template_value
                        changes_made = True
                    else:
                        # Ключ есть — рекурсивно проверяем вложенные структуры
                        if isinstance(template_value, (dict, list)):
                            new_value, nested_changed = _merge_missing(
                                current[key], template_value, current_path
                            )
                            if nested_changed:
                                current[key] = new_value
                                changes_made = True
                        # Если значение примитивное и отличается от шаблона —
                        # оставляем текущее (пользовательское значение)

            elif isinstance(template, list):
                if not isinstance(current, list):
                    print(f"Recovery: replacing non-list at '{path}' with template list")
                    return template, True

                # Для списков: если текущий пуст, а шаблон нет — копируем шаблон
                if len(current) == 0 and len(template) > 0:
                    print(f"Recovery: empty list at '{path}' filled from template")
                    return template, True

            return current, changes_made

        # Создаём копию текущих данных для сравнения
        original_data = json.dumps(self.data, sort_keys=True)

        # Запускаем восстановление
        self.data, was_changed = _merge_missing(self.data, configProgram.copy())

        # Проверяем, были ли изменения
        new_data = json.dumps(self.data, sort_keys=True)
        if new_data != original_data:
            print("Recovery: changes detected, saving...")
            self.save()

        return was_changed


if __name__ == '__main__':
    app = HandlerConfig()
