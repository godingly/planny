import datetime
from datetime import timedelta
from typing import List, Optional, Set, Tuple

from planny.task import Task
from planny.services.beeminder import Beeminder
from planny.services.gcal import GCal
from planny.services.trello import Trello
from planny.services.toggl import Toggl
from planny.db.tasks_db import TasksDB
from planny.utils.utils import *
import planny.utils.time as utils_time
import planny.utils.qt as utils_qt

SECS_BTWN_BREAKS = 80 * 60 
BREAK_LENGTH = 5

class Model:
    def __init__(self, args) -> None:
        self.args = args
        self.bee = Beeminder(args.beeminder_json, args.debug)
        self.gcal = GCal(args.gcal_credentials_json, args.gcal_token_path, args.debug)
        self.trello = Trello(args.trello_json)
        self.toggl = Toggl(args.toggl_json)
        self.secs_tracked = 0 # in seconds
        self.last_break_datetime = utils_time.get_current_local(with_seconds=True)
        self.current_project : str = ''
        self.current_task : Task
    
    def exit(self):
        self.gcal.exit()
    # CURRENT
    def get_current_cmd(self) -> Task:
        """ returns cmd_end_datetime + Task of the project specified in Calendar planny_cmd"""
        cmd_name, cmd_start_datetime, cmd_end_datetime, next_cmd = self.get_current_planny_cmd()
        if not cmd_name: return None # type: ignore
        now = utils_time.get_current_local(with_seconds=True)
        if cmd_name in self.trello.board_name_to_id: # trello board
            if self.is_break_time(): return self.give_me_a_break(next_event=cmd_name)
            task = self.trello.get_first_card(cmd_name)
            task.start_datetime = now
            task.end_datetime = min( (now + timedelta(minutes=task.duration)), cmd_end_datetime)
            return task
            
        else:
            self.reset_break(cmd_end_datetime)
            return Task(name=cmd_name, start_datetime = now, end_datetime = cmd_end_datetime,
                        project="tasks", origin="tasks", next_event_name=next_cmd)
                
    def secs_since_last_break(self) -> int:
        """ return seconds since last break"""
        now = utils_time.get_current_local(with_seconds=True)
        return int((now - self.last_break_datetime).total_seconds())

    def is_break_time(self): return self.secs_since_last_break() > SECS_BTWN_BREAKS
    
    def reset_break(self, time=None):
        if not time:
            time = utils_time.get_current_local(with_seconds=True)
        self.last_break_datetime = time
    
    def give_me_a_break(self, next_event='') -> Task:
        """ return a break Task"""
        print(f"model::give_me_a_break() secs_since_last_break {self.secs_since_last_break}")
        now = utils_time.get_current_local(with_seconds=True)
        self.reset_break(utils_time.get_now_plus_duration(duration_in_minutes=BREAK_LENGTH))
        return Task(name=BREAK, start_datetime = now, end_datetime = now + timedelta(minutes=BREAK_LENGTH),
                    project=BREAK, origin=BREAK, next_event_name=next_event)
    
    def get_current_planny_cmd(self) -> Tuple[CmdName, Datetime, Datetime, CmdName]:
        """ returns the current planny cmd from Google Calendar. 
            Returns project_name, start and end datetimes"""
        current_cmd_dict = self.gcal.get_current_planny_cmd() #  {'id', 'summary', 'start':{'dateTime'}, 'end':{'dateTime'}, 'next_event' }
        if current_cmd_dict:
            cmd_name = current_cmd_dict['summary']
            next_cmd = current_cmd_dict['next_event']
            # start_datetime = datetime.datetime.fromisoformat( current_cmd_dict['start']['dateTime'] )
            start_datetime = utils_time.get_current_local(with_seconds=True)
            end_datetime = datetime.datetime.fromisoformat( current_cmd_dict['end']['dateTime'] )
            return cmd_name, start_datetime, end_datetime, next_cmd
        else:
            return "", None, None, "" # type: ignore

    def get_current_task_name(self) -> str:
        try:
            return self.current_task.name
        except AttributeError as e:
            return ''
    
    def change_minutes(self, minutes: float):
        td = timedelta(minutes=minutes)
        self.current_task.end_datetime += td
    
    def add_event(self, task: Task):
        self.trello.prepend_card_to_board(task.project, task.name)
    
    def get_second(self) -> Task:
        """ if current_cmd is from trello, play 2nd card. 
        else, look for planny_next cmd and start it as a task"""
        cmd_name, cmd_start_datetime, cmd_end_datetime, next_cmd = self.get_current_planny_cmd()
        if cmd_name in self.trello.board_name_to_id:
            # get second card on trello board
            if self.is_break_time():
                return self.give_me_a_break()
            task = self.trello.switch_first_and_second_cards(cmd_name)
            task.start_datetime = utils_time.get_current_local(with_seconds=True)
            task.end_datetime = min( (task.start_datetime + timedelta(minutes=task.duration)), cmd_end_datetime)
            return task
        else: # get next gcal event
            second_cmd_dict = self.gcal.get_second_planny_cmd()
            if second_cmd_dict:
                second_cmd_name = second_cmd_dict['summary']
                now = utils_time.get_current_local(with_seconds=True)
                second_cmd_end_datetime = datetime.datetime.fromisoformat( second_cmd_dict['end']['dateTime'] )
                self.reset_break()
                return Task(name=second_cmd_name, start_datetime = now, end_datetime = second_cmd_end_datetime,
                        project="tasks", origin="tasks", next_event_name=next_cmd)
            else:
                return None # type: ignore
    
    # Projects
    def start_project(self, project_name : str):
        self.gcal.delete_current_planny_cmd()
        start_datetime = utils_time.get_current_local()
        end_datetime = start_datetime + timedelta(hours=1)
        self.gcal.add_planny_cmd_event(project_name, start_datetime, end_datetime)
    
    # END EVENT 
    def end_cur_event(self, is_completed=False, force_update_track_time: bool=False):
        # update time tracking
        time_now_aware = utils_time.get_current_local(with_seconds=True)
        try: self.current_task.end_datetime = time_now_aware
        except AttributeError: return
        
        event_duration_in_seconds = (time_now_aware - self.current_task.start_datetime).total_seconds()
        print(f"model::end_cur_event() adding {event_duration_in_seconds} seconds after task {self.current_task}\n")
        self.update_time_tracked(int(event_duration_in_seconds), force_update_track_time)
        
        # update trello
        if is_completed and self.current_task.name != BREAK:
            self.trello.complete_first_card(self.current_task.project)
        # toggl
        self.toggl.add_time_entry(self.current_task.name, self.current_task.project,
                                self.current_task.start_datetime, self.current_task.end_datetime)
        
        if event_duration_in_seconds > 60:
            # create gcal event
            summary = f'{self.current_task.name}'
            if self.current_task.origin == 'trello':
                summary = f'{self.current_task.project}:' + summary
            self.gcal.add_event(summary=summary,
                                start=self.current_task.start_datetime,
                                end=self.current_task.end_datetime)

    def update_time_tracked(self, secs_tracked: int, force_update_track_time: bool = False):
        self.secs_tracked += secs_tracked
        if self.secs_tracked > 3600 or force_update_track_time:
            self.bee.add_time_tracked(secs_tracked)
    
    # Trello
    def add_task_after(self, project_name, name, desc=''):
        self.trello.prepend_second_card_to_board(board_name=project_name,
                                        name=name,
                                        desc=desc,)
    
    # BEEMINDER
    def add_beeminder_datapoint(self, slug_value_dict):
        for slug,value in slug_value_dict.items():
            self.bee.add_datapoint(slug=slug, value=value)

    def bee_charge(self, name, amount=0):
        if name==BREAK:
            return
        self.bee.charge(note=name,amount=amount)
