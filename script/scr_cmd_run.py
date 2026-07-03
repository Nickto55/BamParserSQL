import json

import sys
import io
import pyodbc


import os
from dotenv import load_dotenv

from handlings.handling_config import ConfigSQLRecvetions

class ScriptCmd:
    def __init__(self, log_callback=None):
        self._load_env()
        self.config_program = ConfigSQLRecvetions()
        self.result = {}
        self.log_program = log_callback

    def test_connection(self) -> bool:
        """
        Проверяет соединение с SQL-сервером.
        Возвращает True в случае успеха, False при ошибке.
        """
        # На всякий случай обновляем переменные окружения
        self._load_env()

        conn_str = (
            f"Driver={{SQL Server}};"
            f"Server={self.sql_server};"
            f"Database={self.sql_db};"
            f"Trusted_Connection=yes;"
        )

        conn = None
        cursor = None
        try:
            self.log_program(f"Тестирование подключения к {self.sql_server}...")
            # Ставим таймаут на подключение 5 секунд, чтобы скрипт не зависал долго
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()

            # Выполняем самый легкий тестовый запрос к системной переменной
            cursor.execute("SELECT @@VERSION")
            db_version = cursor.fetchone()[0]

            self.log_program("Успешно! Соединение с базой данных установлено.", color_log='green' )
            self.log_program(f"Версия SQL Server: {db_version.splitlines()[0]}", color_log='#9aa5aa')
            return True

        except pyodbc.InterfaceError as e:
            self.log_program(f"[Ошибка сети/драйвера]: Не удалось связаться с сервером '{self.sql_server}'.", color_log='red')
            self.log_program(f"Детали: {e}", color_log='red')
            return False
        except pyodbc.DatabaseError as e:
            self.log_program(f"[Ошибка авторизации/БД]: Сервер ответил, но возникла проблема с базой '{self.sql_db}'.", color_log='red')
            self.log_program(f"Детали: {e}", color_log='red')
            return False
        except Exception as e:
            self.log_program(f"[Неизвестная ошибка теста]: {e}", color_log='red')
            return False

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _load_env(self):
        CONFIG_DIR = os.path.join(
            os.path.expanduser("~")
            ,"configs"
            ,".BamParserSQL"
        )
        file_path = os.path.join(CONFIG_DIR, ".env")
        load_dotenv(dotenv_path=file_path,override=True, verbose=True)

        self.sql_server = os.getenv("SQL_SERVER")
        self.sql_db = os.getenv("SQL_DB")
        self.sql_exc = os.getenv("SQL_EXC")


    def main(self,search_dse):
        self._load_env()
        self.result = {}


        output_file = self.config_program.get_output_file()

        conn_str = (
            f"Driver={{SQL Server}};"
            f"Server={self.sql_server};"
            f"Database={self.sql_db};"
            f"Trusted_Connection=yes;"
        )

        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            query = f"EXEC {self.sql_exc} ?"
            param = search_dse
            cursor.execute(query, param)

            columns = [column[0] for column in cursor.description]

            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            self.result = results

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)




        except Exception as e:
            print(f"Произошла ошибка: {e}")


        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()
        return self.result

if __name__ == '__main__':
    app = ScriptCmd()
