import json

import sys
import io
import pyodbc


import os
from dotenv import load_dotenv

from handlings.handling_config import ConfigSQLRecvetions


class ScriptCmd:
    def __init__(self):
        self._load_env()
        self.config_program =  ConfigSQLRecvetions()
        self.result = {}

    def _load_env(self):
        load_dotenv()

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
    app.main()
