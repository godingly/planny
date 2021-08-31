import datetime
from datetime import timedelta

from planny.tasks import Tasker
from planny.services.gcal import GCal
from planny.services.beeminder import Beeminder
from planny.db.tasks_db import TasksDB
from planny.utils.utils import *
import planny.utils.time as utils_time



class Model:
    def __init__(self, args) -> None:
        self.args = args
        self.tasker = Tasker()
        self.bee = Beeminder(args.beeminder_json, args.debug)
        self.gcal = GCal(args.gcal_credentials_json, args.debug)
        self.tasks_db = TasksDB()
        self.secs_tracked = 0 # in seconds
        self.current_playlist = 'misc'
        self.current_event_dict= {}
    
    def exit(self):
        """ methods to run when closing"""
        self.update_time_tracked()
        self.tasks_db.close()
    
    def delete_playlist(self, playlist):
        self.tasks_db.delete_playlist(playlist)
    
    def add_task(self, data):
        summary = data['summary']
        playlist = data['playlist']
        duration = data['start']['datetime'] - data['start']['endtime']
        duration_in_minutes = duration.total_seconds() // 60
        self.tasks_db.add_task(summary, playlist, duration_in_minutes)
    
    def add_minutes(self, minutes: int):
        # TODO 
        td = timedelta(minutes=minutes)
        self.current_event_dict['end']['datetime'] += td

    
    def update_time_tracked(self):
        if self.secs_tracked > 0:
            self.bee.add_time_tracked(self.secs_tracked)
            self.secs_tracked = 0
    
    def add_time_tracked(self, timeInSeconds: int):
        self.secs_tracked += timeInSeconds
        if self.secs_tracked > 3600:
            self.update_time_tracked()
            
    def add_event(self, d):
        self.current_event_dict = d
    
    def end_cur_event(self):
        if not self.current_event_dict: return
        time_now_aware = utils_time.get_current_local()
        self.current_event_dict['end']['datetime'] = time_now_aware
        event_duration_in_seconds = (time_now_aware - self.current_event_dict['start']['datetime']).total_seconds()
        self.add_time_tracked(event_duration_in_seconds)
        if event_duration_in_seconds < 60:
            return
    
        self.gcal.add_event(summary=self.current_event_dict['summary'],
                            start=self.current_event_dict['start']['datetime'],
                            end=self.current_event_dict['end']['datetime'],
                            all_day=False)
    
    def add_beeminder_datapoint(self, slug_value_dict):
        for slug,value in slug_value_dict.items():
            self.bee.add_datapoint(slug=slug, value=value)

    def start_playlist(self, playlist):
        self.current_playlist = playlist
    
    def bee_charge(self, summary, amount=0):
        if amount:
            self.bee.charge(note=summary,amount=amount)
        else:
            self.bee.charge(note=summary)