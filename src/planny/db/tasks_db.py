from sqlite3.dbapi2 import IntegrityError, OperationalError
import sys
if __name__=='__main__': sys.path.insert(0,r'C:\Users\godin\Python\planny\src')

import sqlite3
from typing import List, Optional, Set, Tuple, Union
from collections import OrderedDict

import planny.db.utils as utils_db
from planny.db.utils import sval

DEFAULT_DURATION = 20
PLAYLISTS_TABLE = 'playlists'
NOT_EXISTENT = -1
# col names
PREV = 'prev'
NEXT = 'next'
NAME = 'name'
ROWID = 'rowid'

class TasksDB:
    def __init__(self):
        self.conn = sqlite3.connect(f"tasks.db")
        self.cols_names_types_dict  = OrderedDict([
            (NAME,'TEXT NOT NULL'),
            (PREV,'INT'),
            (NEXT,'INT'),
            ('duration','INT NOT NULL'),
        ])
        self.cols_names_types_str = utils_db.dict_to_col_types(self.cols_names_types_dict)
        self.cols_names_str = ','.join(self.cols_names_types_dict.keys())
        self.create_playlists_table()
    
    def close(self):
        self.conn.close()
    
    def get_first_track(self, table_name) -> Optional[Tuple]:
        """ return none if there is no first track"""
        try:
            res = list(self.conn.execute(f"SELECT rowid, * FROM {table_name} ORDER BY prev ASC ;"))
        except OperationalError:
            print(f"get_first_track(), table {table_name} doesn't exist")
            return None

        if not res: return None
        else: return res[0]
    
    def get_last_track(self, table_name) -> Optional[Tuple]:
        """ return none if there is no last track"""
        res = list(self.conn.execute(f"SELECT rowid, * FROM {table_name} ORDER BY next ASC ;"))
        if not res: return None
        else: return res[0]
    
    def select_all(self, table_name) -> List[Tuple]:
        try:
            return list(self.conn.execute(f"SELECT rowid, * FROM {table_name} ;"))
        except OperationalError as e:
            print(f"select_all({table_name}): no such table: {table_name}  ")
            return []

    def select_track(self, table_name, col_name, val):
        """ returns empty list if val doesn't exist, raises an error if table_name doesn't exist"""
        assert col_name in [NAME, ROWID]
        return list(self.conn.execute(f"SELECT rowid, * from {table_name} WHERE {col_name}={sval(val)} ;"))
    
    def select_track_by_name(self, table_name, track_name) -> List[Tuple]:
        """ returns empty list if track_name doesn't exist, raises an error if table_name doesn't exist """
        return self.select_track(table_name, NAME, track_name)

    def select_track_by_rowid(self, table_name, rowid) -> List[Tuple]:
        """ returns empty list if rowid doesn't exist, raises an error if table_name doesn't exist"""
        return self.select_track(table_name, ROWID, rowid)
    
    def get_prev_track(self, table_name, col_name, val) -> Optional[Tuple]:
        """ returns previos track, None if there isn't one. Raises an error if table_name / track do not exist"""
        track_record = self.select_track(table_name, col_name, val) # rowid, name, prev, next
        if len(track_record) != 1:
            raise Exception(f"get_prev_track({table_name}, {col_name}, {val} ), len(track_record)={len(track_record)}")
        
        prev_track_rowid = track_record[1]

        if prev_track_rowid == NOT_EXISTENT:
            return None

        prev_track_record = self.select_track_by_rowid(table_name, prev_track_rowid)
        if len(prev_track_record) != 1:
            raise Exception(f"get_prev_track({table_name}, {col_name}, {val}), prev_track_rowid={prev_track_rowid}, len(prev_track_record)={len(prev_track_record)}")
        return prev_track_record[0]
    
    def get_prev_track_by_rowid(self, table_name, rowid) -> Optional[Tuple]:
        return self.get_prev_track(table_name, ROWID, rowid)
    
    def get_prev_track_by_track_name(self, table_name, track_name) -> Optional[Tuple]:
         return self.get_prev_track(table_name, NAME, track_name)
    
    def get_next_track(self, table_name, col_name, val) -> Optional[Tuple]:
        """ returns next track, None if there isn't one. Raises an error if table_name / track do not exist"""
        track_record = self.select_track(table_name, col_name, val) # rowid, name, prev, next
        if len(track_record) != 1:
            raise Exception(f"get_next_track({table_name}, {col_name}, {val} ), len(track_record)={len(track_record)}")
        
        next_track_rowid = track_record[2]
        if next_track_rowid == NOT_EXISTENT:
            return None

        next_track_record = self.select_track_by_rowid(table_name,next_track_rowid)
        if len(next_track_record) != 1:
            raise Exception(f"get_next_track({table_name},  {col_name}, {val}), next_track_rowid={next_track_rowid}, len(next_track_record)={len(next_track_record)}")
        return next_track_record[0]

    def get_next_track_by_rowid(self, table_name: str, rowid: int) -> Optional[Tuple]: 
        return self.get_next_track(table_name, ROWID, rowid)

    def get_next_track_by_track_name(self, table_name: str, track_name: str) -> Optional[Tuple]:
        return self.get_next_track(table_name, NAME, track_name)
    
    def update_col_by_track_name(self, table_name: str, track_name: str, col_name: str, new_val):
        self.conn.execute(f"UPDATE {table_name} SET {col_name}={sval(new_val)} WHERE name='{track_name}' ;")
        self.conn.commit()

    def update_col_by_rowid(self, table_name: str, rowid: int, col_name: str, new_val):
        self.conn.execute(f"UPDATE {table_name} SET {col_name}={sval(new_val)} WHERE rowid={rowid} ;")
        self.conn.commit()    
    
    def delete_track(self, table_name: str, col_name: str, val: Union[str, int]):
        """col_name can be "name" or "rowid"
         raises an exception if table_name / track_name don't exist, updates prev and next tracks"""
        # get track
        track_record = self.select_track(table_name, col_name, val)
        if len(track_record) != 1:
            raise Exception(f"delete_track({table_name}, {col_name}, {val}), len(track_record)={len(track_record)}")
        track_record = track_record[0]
        # remove track from table
        self.conn.execute(f"DELETE FROM {table_name} WHERE {col_name}={sval(val)};")
        self.conn.commit()
        
        # update rest of table
        prev_track_rowid = track_record[2]
        next_track_rowid = track_record[3]

        # update prev track, if one exists
        if prev_track_rowid != NOT_EXISTENT:
            self.update_col_by_rowid(table_name, prev_track_rowid, NEXT, next_track_rowid)
        # update next
        if next_track_rowid != NOT_EXISTENT:
            self.update_col_by_rowid(table_name, next_track_rowid, PREV, prev_track_rowid)
    
    def delete_track_by_track_name(self, table_name: str, track_name: str): return self.delete_track(table_name, NAME, track_name)

    def delete_track_by_rowid(self, table_name: str, rowid: int): return self.delete_track(table_name, ROWID, rowid)

    #### PLAYLISTS ####
    
    def create_playlists_table(self):
        self.conn.execute((
            f"CREATE TABLE IF NOT EXISTS {PLAYLISTS_TABLE}"
            f" ({NAME} TEXT NOT NULL UNIQUE, {PREV} INT, {NEXT} INT) ;"
        ))
        self.conn.commit()
    
    def create_table_if_not_exists_for_playlist(self, playlist_name):
        if self.select_track_by_name(PLAYLISTS_TABLE, playlist_name):
            return
        # else

        # create new table
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {playlist_name} ({self.cols_names_types_str}) ;")
        
        # add {playlist_name} to PLAYLISTS table
        last_playlist = self.get_last_track(PLAYLISTS_TABLE) # rowid, name, prev, next
        last_playlist_rowid = last_playlist[0] if last_playlist else NOT_EXISTENT
        # append new playlists
        new_playlist_cursor = self.conn.execute((f"INSERT INTO {PLAYLISTS_TABLE} ({NAME}, {PREV}, {NEXT})"
                                                f" VALUES ('{playlist_name}', {last_playlist_rowid}, {NOT_EXISTENT}) ;"))
        if last_playlist:
            self.update_col_by_rowid(PLAYLISTS_TABLE, last_playlist_rowid, PREV, new_playlist_cursor.lastrowid)
        else:
            self.conn.commit()
        
    def get_playlist_tasks(self, playlist_name: str) -> List[Tuple]:
        """ returns a list of tuples, each tuple (col1, col2,...)"""
        return self.select_all(playlist_name) # [(rowid, name, prev, next, duration), (), ...] 

    def delete_playlist(self, playlist_name: str):
        self.conn.execute(f"DROP TABLE IF EXISTS {playlist_name} ;")
        self.delete_track_by_track_name(PLAYLISTS_TABLE, playlist_name)

    def get_all_playlists_names(self) -> Set[str]:
        playlists_records = self.select_all(PLAYLISTS_TABLE) # rowid, name, prev, next
        return {tup[1] for tup in playlists_records}
    
    #### TASKS ####
       
    def preprend_task(self, summary: str, playlist_name: str='misc', duration: int=DEFAULT_DURATION) -> Tuple:
        """ adds new task to end of {playlist_name}, returns record of new task"""
        self.create_table_if_not_exists_for_playlist(playlist_name)
        duration = int(duration)
        # get first track, if one exists
        first_task = self.get_first_track(playlist_name) # rowid, name, prev, next, duration
        first_task_rowid = first_task[0] if first_task else NOT_EXISTENT
        
        # creates new track
        new_track_cursor = self.conn.execute(
                f"INSERT INTO {playlist_name} ({self.cols_names_str})",
                f"VALUES ( '{summary}', {NOT_EXISTENT}, {first_task_rowid}, {duration} )  ;")
        # updates last track
        new_task_rowid = new_track_cursor.lastrowid
        if first_task:    
            self.update_col_by_rowid(playlist_name, first_task_rowid, PREV, new_task_rowid)
        else:
            self.conn.commit()
        
        return list(new_track_cursor)[0]
    
    def append_task(self, summary: str, playlist_name: str='misc', duration: int=DEFAULT_DURATION) -> Tuple:
        """ adds new task to end of {playlist_name}, returns record of new task"""
        # create new playlist table if needed
        self.create_table_if_not_exists_for_playlist(playlist_name)
        duration = int(duration)
        # get last track, if one exists
        last_task = self.get_last_track(playlist_name) # rowid, name, prev, next, duration
        last_task_rowid = last_task[0] if last_task else NOT_EXISTENT
        
        # creates new track
        new_track_cursor = self.conn.execute((
                f"INSERT INTO {playlist_name} ({self.cols_names_str})"
                f" VALUES ( '{summary}', {last_task_rowid}, {NOT_EXISTENT}, {duration} )  ;"))
        # updates last track
        new_task_rowid = new_track_cursor.lastrowid
        if last_task:    
            self.update_col_by_rowid(playlist_name, last_task_rowid, NEXT, new_task_rowid)
        else:
            self.conn.commit()
        
        return new_task_rowid

    def complete_task(self, playlist_name: str, task_rowid: int) -> Optional[Tuple]:
        """ deletes task with {row_id} from {playlist_name}, returns next track or None"""
        next_task_record = self.get_next_track_by_rowid(playlist_name, task_rowid)
        self.delete_track_by_rowid(playlist_name, task_rowid)
        return next_task_record
        


if __name__=='__main__':
    tasks_db = TasksDB()
    playlist = 'mechanics'
    print(f'before, tabels names {tasks_db.get_all_playlists_names()}')
    tasks_db.delete_playlist(playlist)
    # tasks_db.add_task('pages 1-3', playlist, 20)
    # tasks_db.add_task('pages 4-5', playlist, 30)
    # cursor = tasks_db.get_all_tasks(playlist)
    # for row in cursor:
    #     print(row)
    print(f'after, tabels names {tasks_db.get_all_playlists_names()}')
    tasks_db.close()
    
