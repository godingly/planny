from functools import partial

from planny.model import Model
from planny.ui.plannyWidget import PlannyWidget
from planny.utils.utils import *
import planny.parser as parser




class Ctrl:
    def __init__(self, model: Model, view: PlannyWidget) -> None:
        self.view = view
        self.model = model
        self.connect_signals()
        self.minutesTracked = 0
    
    def evaluate(self) -> None:
        expr = self.view.get_query()
        self.view.clear_query()

        type_, data = parser.parse(expr)
        print(f"Ctrl::evaluate() type: {type_}, data={data}")

        if type_ == Expr_Type.EXIT:
            self.exit()

        elif type_ == Expr_Type.EVENT_FINISH:
            self.end_cur_event()

        if type_ == Expr_Type.EVENT:
            self.add_event(data)

        elif type_ == Expr_Type.MORE_MINUTES:
            self.add_minutes(int(data['minutes']))

        elif type_ == Expr_Type.TASK:
            self.add_task(data)
        
        elif type_ == Expr_Type.BEEMINDER:
            self.model.add_beeminder_datapoint(data)

        elif type_ == Expr_Type.PLAYLIST_DELETE:
            self.model.delete_playlist(data['playlist'])

        elif type_ == Expr_Type.PLAYLIST_START:
            self.start_playlist(data)

        elif type_ == Expr_Type.NEXT_TASK:
            self.end_cur_event()
        
    
    def exit(self):
        self.end_cur_event()
        self.model.exit()
        exit()
    
    def add_task(self,data):
        self.model.add_task(data)
    
    def add_minutes(self, minutes):
        self.view.add_minutes(minutes)
        self.model.add_minutes(minutes)

    def add_event(self, data):
        self.end_cur_event()
        self.view.add_event(data)
        self.model.add_event(data)

    def get_secs_to_start(self) -> int:
        return self.view.get_secs_to_start()

    def end_cur_event(self):
        self.model.end_cur_event()
        self.view.end_cur_event()

    def start_playlist(self, data):
        playlist = data['playlist']
        self.end_cur_event()
        event_data = self.model.start_playlist(playlist)
        pass

    # SLOTS
    def connect_signals(self) -> None:
        self.view.lineEdit.editline.returnPressed.connect(partial(self.evaluate))
        self.view.set_timer_callBack(self.timer_callback)
    
    def timer_callback(self, summary, amount=0):
        print("timer ended")
        self.model.bee_charge(summary, amount)