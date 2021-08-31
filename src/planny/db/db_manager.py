import sqlite3


import planny.db.utils as utils_db

class SQLite_DB:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(f"{db_name}.db")
        self.db_aname = db_name
        self.table_names = []

    def create_table(self, table_name, col_names_types_dict):
        cols_names_types_str = utils_db.dict_to_col_types(col_names_types_dict)
        self.table_names.append(table_name)
        query = (
            f'CREATE TABLE IF NOT EXISTS {table_name}'
            f' ({cols_names_types_str})'
            f';')
        self.conn.execute(query)
        
    def insert(self, table_name : str,
               col_names :str,
               values: list):
        str_values = utils_db.values_to_sql(values)
        query = (
            f'INSERT INTO {table_name}'
            f' ({col_names})'
            f' VALUES ({str_values})'
            f';')
        self.conn.execute(query)
    
    def select(self, col_names: str, table_name: str):
        query = (
            f'SELECT {col_names}'
            f' FROM {table_name}'
            f';'
        )
        cursor = self.conn.execute(query)
        return cursor

    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()

    def get_all_tables_names(self):
        query = utils_db.query_all_tables_names()
        cursor = self.conn.execute(query)
        return cursor

