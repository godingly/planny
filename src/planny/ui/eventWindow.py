from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel
from PyQt5.QtCore import QTimer, QTime, Qt
from PyQt5.QtMultimedia import QSound

import os
import datetime
from pathlib import Path

from planny.utils import qt as utils_qt
from planny.utils import time as utils_time


class EventWindow(QDialog):
    def __init__(self, args):
        super().__init__()
        self.args = args
        # init
        self.layout_ = QGridLayout()
        self.resize(100, 50) # width, height
        self.zeroTime = QTime(0,0,0)
        self._init_widgets()
        
        # timer        
        self.timer = QTimer()
        self.timer.timeout.connect(self.timeout)
        self.start_datetime = datetime.datetime.min
        self.endtDateTime : datetime.datetime
        self.countdownTime : QTime
        self.mSecsPassed = 0  # int, number of microsecnds from start
        self.countdownDeltaMS = 1000
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint) # type: ignore
        # self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint) # type: ignore
        file_path = Path(__file__).resolve()
        wav_path = Path(file_path.parent.parent.parent, 'resources','kill_bill_whistle.wav')
        self.alarm = QSound(str(wav_path))


        # flash
        if args.debug:
            self.flashTime = QTime(0,0,58)
        else:
            self.flashTime = QTime(0,0,40)
        self.isFlashOn = False
        self.isBlueBackground = False
        
        self.setLayout(self.layout_)
    
    def _init_widgets(self):
        # create widgets
        # summary and timeLabel
        self.summaryLabel = QLabel()
        self.countdownLabel = QLabel()
        utils_qt.setFont(self.summaryLabel, utils_qt.LARGE_FONT_SIZE)
        utils_qt.setFont(self.countdownLabel, utils_qt.LARGE_FONT_SIZE)
        self.layout_.addWidget(self.summaryLabel, 0, 0)
        self.layout_.addWidget(self.countdownLabel, 0, 1)

        # startEndLabel and nextEvent label
        self.startEndLabel = QLabel()
        self.layout_.addWidget(self.startEndLabel,1,0)
        self.nextEventLabel = QLabel('next event')
        self.layout_.addWidget(self.nextEventLabel,1,1)
    
    def _position(self):
        """ positions widget at right edge of screen, slightly above center"""
        self.show()   
        geo = self.frameGeometry() # QRect (x,y, width, height)
        screen_upper_right = utils_qt.getScreenUpperRight()
        geo.moveBottomRight(screen_upper_right)
        self.move(geo.topLeft()) # move(QPoint=x,y)
    
    def update_startEnd_label(self):
        """ sets StarTEndLabel to show 8:30-12:40"""
        startEndStr = utils_time.datetimes_to_hours_minutes(self.start_datetime, self.end_datetime)
        self.startEndLabel.setText(startEndStr)
    
    # overriding
    def close_event(self, event):
        self.end_cur_event()
        event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            qPoint = event.globalPos() 
            geo = self.frameGeometry() # QRect (x,y, width, height)
            geo.moveCenter(qPoint)
            self.move(geo.topLeft()) # move(QPoint=x,y)    
    
    def start(self, summary: str,
              start_datetime: datetime.datetime,
              end_datetime: datetime.datetime):
        """ starts new event"""    
        self.timer.stop()
        
        # set summary
        self.setWindowTitle(summary)
        self.set_summary(summary)
        
        # set startime, endtime
        self.start_datetime = start_datetime 
        self.end_datetime = end_datetime
        self.update_startEnd_label()
        
        # set coundown
        countdown_time = utils_time.timedelta_to_datetime_time(end_datetime - start_datetime) # type: datetime.time
        self.set_countdown_time(countdown_time)
        self.update_countdown_label()
        # start timer
        self.timer.start(self.countdownDeltaMS)

        if self.isVisible() is False:
            self.show()
        self._position()

    def play_alert(self):
        pass
    def set_summary(self, summary: str):
         self.summaryLabel.setText(summary)
         self.adjustSize()
         self._position()
    
    def get_summary(self) -> str: return self.summaryLabel.text()
    
    def set_countdown_time(self, time: datetime.time): self.countdown_time = QTime(time) # type: ignore
    def reset_coundown_time(self): self.countdown_time = QTime()
    def get_MSecs_to_start(self) -> int: 
        """ how many microseconds have passed since the start"""
        return self.mSecsPassed

    def reset_labels(self):
        self.summaryLabel.setText('')
        self.countdownLabel.setText('')
        # self.nextEventLabel.setText('')
        # self.startEndLabel.setText('')

    
    def end_cur_event(self):
        self.stop_flash()
        self.reset_coundown_time()
        self.timer.stop()
        self.mSecsPassed = 0
        self.reset_labels()
        

    def timeout(self):
        self.countdown_time = self.countdown_time.addMSecs(-self.countdownDeltaMS)
        self.mSecsPassed += self.countdownDeltaMS
        self.update_countdown_label()
        if self.is_timer_ended():
            summary = self.get_summary()
            print(f'timer for {summary} ended!!!')
            self.timer.stop()
            self.timerCallback(summary)
        elif self.countdown_time < self.flashTime: # type: ignore
            self.start_flash()
            self.toggle_background_color()
            
    def set_timer_callback(self, callback): 
        self.timerCallback = callback 
    
    def update_countdown_label(self):
        countdown_str = utils_time.QTime_to_str(self.countdown_time)
        self.countdownLabel.setText(countdown_str)

    def is_timer_ended(self) -> bool:
        return self.countdown_time == self.zeroTime
    
    def add_minutes(self, minutes: int):
        self.end_datetime += datetime.timedelta(minutes=minutes)
        self.update_startEnd_label()
        
        self.countdown_time = self.countdown_time.addSecs(minutes * 60)
        self.update_countdown_label()
        self.stop_flash()
        
    # flash
    def toggle_background_color(self):
        if self.isBlueBackground:
            self.setStyleSheet("background-color: red;")
            self.isBlueBackground = False
        else:
            self.setStyleSheet("background-color: blue;")
            self.isBlueBackground = True
    
    def start_flash(self):
        if self.isFlashOn:
            return
        self.timer.stop()
        self.countdownDeltaMS = 200
        self.timer.start(self.countdownDeltaMS)
        self.isFlashOn = True
        self.alarm.play()
    
    def stop_flash(self):
        utils_qt.resetBackgroundColor(self)
        self.isFlashOn = False
        self.timer.stop()
        self.alarm.stop()
        self.countdownDeltaMS = 1000
        self.timer.start(self.countdownDeltaMS)



    