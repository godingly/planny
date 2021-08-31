import sys
if __name__=='__main__':
    sys.path.insert(0,r'C:\Users\godin\Python\planny\src')

import sqlite3
from typing import Set
from collections import OrderedDict

import planny.db.utils as utils_db

DEFAULT_DURATION = 20

class TasksDB:
    def __init__(self):
        self.conn = sqlite3.connect(f"tasks.db")
        self.cols_names_types_dict  = OrderedDict([
            ('summary','TEXT NOT NULL'),
            ('duration','INT'),
        ])
        self.cols_names_types_str = utils_db.dict_to_col_types(self.cols_names_types_dict)
        self.cols_names_str = ','.join(self.cols_names_types_dict.keys())

    def add_task(self, summary: str, playlist: str='misc', duration: int=DEFAULT_DURATION):
        self.create_playlist(playlist)
        
        query = (
            f"INSERT INTO {playlist}"
            f" ({self.cols_names_str})"
            f" VALUES ('{summary}',{duration})"
            f";")
        self.conn.execute(query)
        # TODO wasteful
        self.conn.commit()

    def get_playlist_tasks(self, playlist):
        """ returns a list of tuples, each tuple (col1, col2,...)"""
        query = f'SELECT * from {playlist};'
        cursor = self.conn.execute(query)
        return cursor

    def delete_playlist(self, playlist):
        query = f'DROP TABLE IF EXISTS {playlist};'
        print(query)
        self.conn.execute(query)
        self.conn.commit()
        

    def create_playlist(self, table_name, cols_names_types_str=None):
        if not cols_names_types_str:
            cols_names_types_str = self.cols_names_types_str
        query = (
            f'CREATE TABLE IF NOT EXISTS {table_name}'
            f' ({self.cols_names_types_str})'
            f';')
        self.conn.execute(query)

    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()

    def get_all_tables_names(self) -> Set[str]:
        query = utils_db.query_all_tables_names()
        cursor = self.conn.execute(query)
        tables_names = set()
        for row in cursor:
            tables_names.add(row[0])
        return tables_names


if __name__=='__main__':
    tasks_db = TasksDB()
    playlist = 'mechanics'
    print(f'before, tabels names {tasks_db.get_all_tables_names()}')
    tasks_db.delete_playlist(playlist)
    # tasks_db.add_task('pages 1-3', playlist, 20)
    # tasks_db.add_task('pages 4-5', playlist, 30)
    # cursor = tasks_db.get_all_tasks(playlist)
    # for row in cursor:
    #     print(row)
    print(f'after, tabels names {tasks_db.get_all_tables_names()}')
    tasks_db.close()
    
