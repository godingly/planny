""" main widget for the app"""

import datetime
from PyQt5.QtWidgets import QDialog
from planny.task import Task
from planny.ui.lineEdit import LineEdit
from planny.ui.eventWindow import EventWindow
import planny.utils.time as utils_time


class PlannyWidget():
    def __init__(self, args):
        self.lineEdit = LineEdit(args)
        self.eventWindow = EventWindow(args)
        self.args = args

    def show(self):
        self.lineEdit.show()

    def get_query(self): return self.lineEdit.lineEditText()
    def clear_query(self): return self.lineEdit.clearLineEditText()
    def set_query(self, txt): self.lineEdit.setLineEditText(txt)

    def is_timer_ended(self) -> bool:
        return self.eventWindow.is_timer_ended()

    def add_event(self, task: Task):
        self.eventWindow.start(task)
        self.lineEdit.showMinimized()
    
    def end_cur_event(self): 
        self.eventWindow.end_cur_event()

    def change_minutes(self, minutes):
        self.eventWindow.change_minutes(minutes)

    # Callbacks
    def set_timer_callback(self, callback):
        self.eventWindow.set_timer_callback(callback)

    def set_refresh_callback(self, callback):
        self.eventWindow.set_refresh_callback(callback)
        self.lineEdit.set_refresh_callback(callback)

    def set_finish_event_callback(self, callback):
        self.eventWindow.set_finish_event_callback(callback)

    def set_change_minutes_callback(self, callback):
        self.eventWindow.set_change_minutes_callback(callback)
