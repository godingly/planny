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
        self.current_board = DEFAULT_BOARD
        self.planny_cmd_timer = None
        self.connect_signals()
        self.start_current_task()
    
    def evaluate(self) -> None:
        expr = self.view.get_query()
        self.view.clear_query()

        type_, data = parser.parse(expr)
        print(f"Ctrl::evaluate() type: {type_}, data={data}")

        if type_ == Expr_Type.EXIT:
            self.exit()

        elif type_ == Expr_Type.REFRESH:
            self.start_current_task()
        
        elif type_ == Expr_Type.EVENT_FINISH:
            self.finish_event()

        if type_ == Expr_Type.EVENT:
            task = Task(name=data['name'],
                        board=data.get('board', self.current_board),
                        start_datetime=data['start']['datetime'],
                        end_datetime=data['end']['datetime'],)
            self.add_event(task)

        if type_ == Expr_Type.BREAK:
            self.start_break(data)

        elif type_ == Expr_Type.CHANGE_MINUTES:
            self.change_minutes(data['minutes'])
        
        elif type_ == Expr_Type.BEEMINDER:
            self.model.add_beeminder_datapoint(data)

        elif type_ == Expr_Type.BOARD_START:
            self.start_board(data['board'])

    def exit(self):
        self.model.end_cur_event(force_update_track_time=True)
        exit()
    
    def start_current_task(self):
        if self.planny_cmd_timer:
            self.planny_cmd_timer.stop()
        # get current task
        task = self.model.get_current_task()
        if not task: return
        self.current_board = task.board
        # start update command timer
        now = utils_time.get_current_local()
        td = utils_time.get_timedelta_from_now_to(task.end_datetime)
        assert td.total_seconds() > 0, f"start_planny_cmd, now={now}, cmd_end_datetime = {task.end_datetime}, board = {self.current_board}"
        self.planny_cmd_timer = utils_qt.startSingleShotTimer(partial(self.start_current_task), (td.total_seconds()+1)*1000 )
        # start event
        self.start_event(task)

    
    def start_break(self, data):
        task = Task(name='break',
                    board=self.model.current_task.name,
                    start_datetime=data['start']['datetime'],
                    end_datetime=data['end']['datetime'],
                    origin='break',
                    next_event_name = f"{self.current_board}:{self.model.current_task.name}")
        self.start_event(task)

    def finish_event(self):
        self.end_cur_event(is_completed=True)
        self.start_current_task()
    
    def start_board(self, board_name : str):
        self.current_board = board_name
        self.model.start_board(board_name)
        self.start_current_task()
    
    def change_minutes(self, minutes):
        self.view.change_minutes(minutes)
        self.model.change_minutes(minutes)
    
    def add_event(self, task: Task):
        """ add event from CLI"""
        # add event to current board
        self.model.add_event(task)
        # start event
        self.start_event(task)
    
    def start_event(self, task : Task):
        self.end_cur_event()
        self.model.current_task = task
        self.current_board = task.board
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
    
    def timer_callback(self, name, board="event", amount=0):
        print("ctrl(): timer ended")
        if name != "break" and board not in ['events', 'chores', 'break']:
            self.model.bee_charge(name, amount)
        self.start_current_task()
            
        
    def refresh_callback(self):
        self.start_current_task()

