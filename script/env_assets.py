import os
import shutil
from dataclasses import dataclass, fields
from typing import Optional


@dataclass
class EnvConfig:
    """Структура конфигурации с валидацией."""
    SQL_SERVER: str = ""
    SQL_DB: str = ""
    SQL_EXC: str = ""

    def is_valid(self) -> bool:
        """Проверяет, что все обязательные поля заполнены."""
        return all([
            self.SQL_SERVER.strip(),
            self.SQL_DB.strip(),
            self.SQL_EXC.strip(),
        ])

    def get_missing_fields(self) -> list[str]:
        """Возвращает список незаполненных полей."""
        missing = []
        for field in fields(self):
            value = getattr(self, field.name)
            if not str(value).strip():
                missing.append(field.name)
        return missing


class HandlerEnv:
    DEFAULT_CONFIG = EnvConfig()

    def __init__(self, app_name: str = "BamParserSQL"):
        self.name_programm_config_dir = f".{app_name}"
        self.CONFIG_DIR = os.path.join(
            os.path.expanduser("~"),
            "configs",
            self.name_programm_config_dir
        )
        self.file_path = os.path.join(self.CONFIG_DIR, ".env")

        self._migrate_old_config()
        self._ensure_file_exists()
        self.config: EnvConfig = self._load()
        self._sync_with_template()


    def save(self) -> None:
        """Сохраняет конфиг в .env формате KEY='VALUE'."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            for field in fields(self.config):
                value = getattr(self.config, field.name)
                safe_value = str(value).replace("'", "\\'")
                f.write(f"{field.name}='{safe_value}'\n")
        print(f"Конфиг сохранён: {self.file_path}")

    def update(self, **kwargs) -> None:
        """Обновляет поля конфигурации и сохраняет."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, str(value))
            else:
                raise ValueError(f"Неизвестное поле: {key}")
        self.save()

    def validate(self) -> tuple[bool, list[str]]:
        """Проверяет конфигурацию. Возвращает (ok, список_ошибок)."""
        if not self.config.is_valid():

            return False, self.config.get_missing_fields()
        return True, []

    def _migrate_old_config(self) -> None:
        """Переносит конфиг из старого расположения."""
        old_dir = os.path.join(os.path.expanduser("~"), self.name_programm_config_dir)

        if not os.path.exists(old_dir):
            return
        if os.path.exists(self.CONFIG_DIR):
            return

        try:
            shutil.copytree(old_dir, self.CONFIG_DIR)
            print(f"Конфиг перенесён: {old_dir} → {self.CONFIG_DIR}")
        except Exception as e:
            print(f"Ошибка переноса: {e}")

    def _ensure_file_exists(self) -> None:
        """Создаёт .env файл с дефолтными значениями, если его нет."""
        if os.path.exists(self.file_path):
            return

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            for field in fields(self.DEFAULT_CONFIG):
                f.write(f"{field.name}=''\n")
        print(f"Создан дефолтный конфиг: {self.file_path}")

    def _load(self) -> EnvConfig:
        """Загружает .env файл, парсит KEY='VALUE'."""
        raw_data = {}

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if '=' not in line:
                        print(f"Пропускаю строку {line_num}: нет '='")
                        continue

                    key, value = line.split('=', 1)
                    key = key.strip()

                    value = value.strip()
                    if (value.startswith("'") and value.endswith("'")) or \
                            (value.startswith('"') and value.endswith('"')):
                        value = value[1:-1]

                    raw_data[key] = value

        except FileNotFoundError:
            print("Файл не найден, создаю дефолтный...")
            self._ensure_file_exists()
            return self.DEFAULT_CONFIG
        except Exception as e:
            print(f"Ошибка чтения ({e}), восстанавливаю...")
            self._ensure_file_exists()
            return self.DEFAULT_CONFIG

        valid_keys = {f.name for f in fields(EnvConfig)}
        filtered = {k: v for k, v in raw_data.items() if k in valid_keys}

        return EnvConfig(**filtered)

    def _sync_with_template(self) -> None:
        """Добавляет отсутствующие поля из шаблона."""
        current_dict = {}
        for field in fields(self.config):
            current_dict[field.name] = getattr(self.config, field.name)

        template_dict = {}
        for field in fields(self.DEFAULT_CONFIG):
            template_dict[field.name] = getattr(self.DEFAULT_CONFIG, field.name)

        changed = False
        for key, default_value in template_dict.items():
            if key not in current_dict or current_dict[key] == "" and default_value != "":
                print(f"Добавлено отсутствующее поле: {key}")
                current_dict[key] = default_value
                changed = True

        if changed:
            self.config = EnvConfig(**current_dict)
            self.save()


import tkinter as tk
from tkinter import messagebox


class EnvConfigGUI:
    def __init__(self, handler: HandlerEnv):
        self.handler = handler
        self.root = tk.Tk()
        self.root.title("Настройки подключения")

        self.entries = {}
        self._build_form()

    def _build_form(self):
        for i, field in enumerate(fields(self.handler.config)):
            value = getattr(self.handler.config, field.name)
            print(field.name, value)

            tk.Label(self.root, text=field.name).grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(self.root, width=40)
            entry.insert(0, value)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[field.name] = entry

        tk.Button(self.root, text="Сохранить", command=self._save).grid(
            row=len(self.entries), column=0, columnspan=2, pady=10
        )

    def _save(self):
        try:
            self.handler.update(**{k: v.get() for k, v in self.entries.items()})
            ok, errors = self.handler.validate()
            if not ok:
                messagebox.showwarning("Внимание", f"Не заполнены: {', '.join(errors)}")
            else:
                messagebox.showinfo("Успех", "Сохранено!")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    env = HandlerEnv()
    gui = EnvConfigGUI()
    gui.run()