""" main widget for the app"""

import datetime
from PyQt5.QtWidgets import QDialog
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

    def getQuery(self): return self.lineEdit.lineEditText()
    def clearQuery(self): return self.lineEdit.clearLineEditText()
    def setQuery(self, txt): self.lineEdit.setLineEditText(txt)

    def isTimerEnded(self) -> bool:
        return self.eventWindow.isTimerEnded()

    def setTimerCallBack(self, callback):
        self.eventWindow.setTimerCallBack(callback)


    def endCurEvent(self): 
        self.eventWindow.endCurEvent()
    
    def getSecsToStart(self) -> int:
        """ return number of seconds since start"""
        mSecsToStart =  self.eventWindow.getMSecsToStart()
        return mSecsToStart // 1000
    
    def createEvent(self, data):
        # create new event
        summary = data['summary']
        startDateTime = data['start']['datetime'] # type: datetime.datetime
        endDateTime = data['end']['datetime'] # type: datetime.datetime
        duration = utils_time.timedelta_to_datetime_time(data['duration']) # type: datetime.time
        self.eventWindow.start(summary, startDateTime, endDateTime, duration)
        if self.eventWindow.isVisible() is False: self.eventWindow.show()
        self.lineEdit.showMinimized()
        
        # close window
        # self.eventWindow.close()

    def addMinutes(self, minutes):
        self.eventWindow.addMinutes(minutes)