from functools import partial
import datetime
from datetime import timedelta

from PyQt5.QtCore import QTimer

from planny.model import Model
from planny.task import Task
from planny.ui.plannyWidget import PlannyWidget
from planny.utils.utils import *
import planny.utils.time as utils_time
import planny.utils.qt as utils_qt
import planny.parser as parser



class Ctrl:
    def __init__(self, model: Model, view: PlannyWidget) -> None:
        self.view = view
        self.model = model
        self.current_project = DEFAULT_PROJECT
        self.planny_cmd_timer : QTimer = None # type: ignore
        self.connect_signals()
        self.start_current_cmd()
    
    def evaluate(self) -> None:
        expr = self.view.get_query()
        self.view.clear_query()

        type_, data = parser.parse(expr)
        print(f"Ctrl::evaluate() type: {type_}, data={data}")

        if type_ == Expr_Type.EXIT:
            self.exit()

        elif type_ == Expr_Type.REFRESH:
            self.start_current_cmd()
        
        elif type_ == Expr_Type.EVENT_FINISH:
            self.finish_event()

        if type_ == Expr_Type.EVENT:
            task = Task(name=data['name'],
                        project=data.get('project', self.current_project),
                        start_datetime=data['start']['datetime'],
                        end_datetime=data['end']['datetime'],
                        origin='trello')
            self.end_cur_event()
            self.add_event(task)

        if type_ == Expr_Type.BREAK:
            self.start_break(data)

        elif type_ == Expr_Type.CHANGE_MINUTES:
            self.change_minutes(data['minutes'])
        
        elif type_ == Expr_Type.ADD_TASK_AFTER:
            self.add_task_after(data)
        
        elif type_ == Expr_Type.BEEMINDER:
            self.model.add_beeminder_datapoint(data)

        elif type_ == Expr_Type.PROJECT_START:
            self.start_project(data['project'])

        elif type_ == Expr_Type.NEXT:
            self.play_next()

    def exit(self):
        self.model.end_cur_event(force_update_track_time=True)
        exit()
    
    def start_current_cmd(self):
        # get current task
        task = self.model.get_current_cmd()
        if not task: return
        self.current_project = task.project
        # start update command timer
        td = utils_time.get_timedelta_from_now_to(task.end_datetime)
        assert td.total_seconds() > 0, f"start_planny_cmd, now={utils_time.get_current_local()}, cmd_end_datetime = {task.end_datetime}, project = {self.current_project}"
        self.planny_cmd_timer = utils_qt.startSingleShotTimer(partial(self.end_and_start_current_cmd), (td.total_seconds()+4)*1000 )
        # start event
        self.start_event(task)

    def end_and_start_current_cmd(self):
        print("end_and_start_current_cmd", utils_time.get_current_local(with_seconds=True).time())
        self.planny_cmd_timer.stop()
        self.end_cur_event()
        self.start_current_cmd()

    def add_task_after(self, data):
        name = data['name']
        project_name = data.get('project', self.current_project)
        desc = data.get('description', '')
        if 'duration' in data:
            name += f" {data['duration']}m"
        self.model.add_task_after(project_name, name, desc)

    def start_break(self, data):
        task = Task(name='break',
                    project=self.model.current_task.name,
                    start_datetime=data['start']['datetime'],
                    end_datetime=data['end']['datetime'],
                    origin='break',
                    next_event_name = f"{self.current_project}:{self.model.current_task.name}")
        self.start_event(task)

    def finish_event(self):
        self.end_cur_event(is_completed=True)
        self.start_current_cmd()
    
    def start_project(self, project_name : str):
        self.current_project = project_name
        self.model.start_project(project_name)
        self.start_current_cmd()
    
    def change_minutes(self, minutes: int):
        if self.model.is_break_time():
            break_task = self.model.give_me_a_break()
            self.end_cur_event()
            self.start_event(break_task)
        self.view.change_minutes(minutes)
        self.model.change_minutes(minutes)
        # reset single shot timer
        if self.planny_cmd_timer:
            self.planny_cmd_timer.stop()
        td = utils_time.get_timedelta_from_now_to(self.model.current_task.end_datetime)
        self.planny_cmd_timer = utils_qt.startSingleShotTimer(partial(self.start_current_cmd), (td.total_seconds()+1)*1000 )
    
    def add_event(self, task: Task):
        """ add event from CLI"""
        # add event to current project
        self.model.add_event(task)
        # start event
        self.start_event(task)
    
    def play_next(self):
        """ if current_cmd is from trello, play 2nd card. 
        else, look for planny_next cmd and start it as a task"""
        task = self.model.get_second()
        self.end_cur_event()
        self.start_event(task)

    
    def start_event(self, task : Task):
        self.model.current_task = task
        self.current_project = task.project
        self.view.add_event(task)

    def end_cur_event(self, is_completed=False):
        self.model.end_cur_event(is_completed)
        self.view.end_cur_event()
    
    # SLOTS
    def connect_signals(self) -> None:
        self.view.lineEdit.editline.returnPressed.connect(partial(self.evaluate))
        self.view.set_timer_callback(self.timer_callback)
        self.view.set_refresh_callback(self.refresh_callback)
        self.view.set_finish_event_callback(self.finish_event)
        self.view.set_change_minutes_callback(self.change_minutes)
        self.view.eventWindow.set_play_next_callback(self.play_next) 
        self.view.eventWindow.set_exit_callback(self.exit) 
    
    def timer_callback(self, amount=0):
        print("ctrl::timer_callback() timer ended")
        task = self.model.current_task
        if task.name != BREAK and task.project.lower() not in ['events', 'chores', BREAK, 'tasks', 'stam']:
            self.model.bee_charge(task.name, amount)
        self.end_cur_event()
        self.start_current_cmd()
            
    def refresh_callback(self):
        self.start_current_cmd()

