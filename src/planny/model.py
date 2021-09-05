import datetime
from datetime import timedelta
from typing import List, Optional, Set, Tuple

from planny.task import Task
from planny.services.gcal import GCal
from planny.services.trello import Trello
from planny.services.beeminder import Beeminder
from planny.db.tasks_db import TasksDB
from planny.utils.utils import *
import planny.utils.time as utils_time
import planny.utils.qt as utils_qt



class Model:
    def __init__(self, args) -> None:
        self.args = args
        self.bee = Beeminder(args.beeminder_json, args.debug)
        self.gcal = GCal(args.gcal_credentials_json, args.debug)
        self.trello = Trello(args.trello_json)
        self.secs_tracked = 0 # in seconds
        self.current_task : Task
    
    def exit(self):
        """ methods to run when closing"""
        self.update_time_tracked()
    
    # CURRENT
    
    def get_current_planny_cmd(self) -> Tuple[CmdName, Datetime, Datetime]:
        """ returns the current planny cmd from Google Calendar. 
            Returns board_name, start and end datetimes"""
        current_cmd_dict = self.gcal.get_current_planny_cmd() #  {'id', 'summary', 'start':{'dateTime'}, 'end':{'dateTime'}
        if current_cmd_dict:
            cmd_name = current_cmd_dict['summary']
            start_datetime = datetime.datetime.fromisoformat( current_cmd_dict['start']['dateTime'] )
            end_datetime = datetime.datetime.fromisoformat( current_cmd_dict['end']['dateTime'] )
            return cmd_name, start_datetime, end_datetime
        else:
            return "", None, None # type: ignore
        
        return cmd_name, start_datetime, end_datetime
    
    def get_board_first_task(self, board_name: str) -> Task:
        """ returns first Task from given board"""
        trello_d = self.trello.get_first_card(board_name) # {'id', 'name', 'pos', 'idList', 'due', 'desc', 'list,'board'}
        task = Task(name=trello_d['name'],
                    desc=trello_d['desc'],
                    duration=trello_d['duration'],
                    board=trello_d['board'],
                    list=trello_d['list'],
                    num_cards_in_list=trello_d['num_cards_in_list'],
                    num_total_cards=trello_d['num_total_cards'],
                    num_completed_cards=trello_d['num_completed_cards'],
                    )
        task.start_datetime = utils_time.get_current_local()
        task.end_datetime = task.start_datetime + timedelta(minutes=task.duration)
        return task
           
    def get_current_task(self) -> Task:
        """ returns cmd_end_datetime + Task of the board specified in Calendar planny_cmd"""
        cmd_name, cmd_start_datetime, cmd_end_datetime = self.get_current_planny_cmd()
        if not cmd_name:
            return None # type: ignore
        if cmd_name.startswith('event'):
            event_name = cmd_name
            task = Task(name=event_name, board="Events",start_datetime=cmd_start_datetime, end_datetime=cmd_end_datetime)
            return task
        else:
            board_name = cmd_name
            task = self.get_board_first_task(board_name)
            task.end_datetime = min( (task.start_datetime + timedelta(minutes=task.duration)), cmd_end_datetime)
            return task
    
    def change_minutes(self, minutes: int):
        td = timedelta(minutes=minutes)
        self.current_task.end_datetime += td
    
    def add_event(self, task: Task):
        self.trello.prepend_card_to_board(task.board, task.name)
    
    # BOARDS
    def start_board(self, board_name : str):
        self.gcal.delete_current_planny_cmd()
        start_datetime = utils_time.get_current_local()
        end_datetime = start_datetime + timedelta(hours=1)
        self.gcal.add_planny_cmd_event(board_name, start_datetime, end_datetime)
    
    # END EVENT 
    def update_time_tracked(self):
        if self.secs_tracked > 0:
            self.bee.add_time_tracked(self.secs_tracked)
            self.secs_tracked = 0
    
    def add_time_tracked(self, timeInSeconds: int):
        self.secs_tracked += timeInSeconds
        if self.secs_tracked > 3600:
            self.update_time_tracked()
    
    def end_cur_event(self, is_completed=False):
        # update time tracking
        time_now_aware = utils_time.get_current_local()
        try:
            self.current_task.end_datetime = time_now_aware
        except AttributeError:
            return
        
        event_duration_in_seconds = (time_now_aware - self.current_task.start_datetime).total_seconds()
        self.add_time_tracked(int(event_duration_in_seconds))
        
        # update trello
        if is_completed:
            self.trello.complete_first_card(self.current_task.board)
        
        if event_duration_in_seconds > 60:
            # create gcal event
            self.gcal.add_event(summary=f"{self.current_task.board}:{self.current_task.name}",
                                start=self.current_task.start_datetime,
                                end=self.current_task.end_datetime,)

        
    
    # BEEMINDER
    def add_beeminder_datapoint(self, slug_value_dict):
        for slug,value in slug_value_dict.items():
            self.bee.add_datapoint(slug=slug, value=value)

    def bee_charge(self, name, amount=0):
        if name=='break':
            return
        self.bee.charge(note=name,amount=amount)
