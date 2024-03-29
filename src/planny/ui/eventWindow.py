from PyQt5.QtWidgets import QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer, QTime, Qt
from PyQt5.QtMultimedia import QSound

import os
import datetime
from pathlib import Path
from planny.task import Task

from planny.utils import qt as utils_qt
from planny.utils import time as utils_time
from planny.utils.utils import BREAK


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
        self.countdownDeltaMS = 1000
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint) # type: ignore
        # self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint) # type: ignore
        file_path = Path(__file__).resolve()
        wav_path = Path(file_path.parent.parent.parent, 'resources','kill_bill_whistle.wav')
        self.alarm = QSound(str(wav_path))


        # flash
        self.flashTime = QTime(0,0,40)
        self.breakFlashTime = QTime(0,0,20)
        self.isFlashOn = False
        self.isRedBackground = False
        
        self.setLayout(self.layout_)
    
    # init
    def _init_widgets(self):
        # projectLabel + listLabel
        self.projectLabel = QLabel()
        self.listLabel = QLabel()
        utils_qt.setFont(self.projectLabel, 20, isBold=True) # _, font size
        self.layout_.addWidget(self.projectLabel,0,0)
        self.layout_.addWidget(self.listLabel,0,1)
        
        # add line between
        qLine = QFrame(); qLine.setFrameShape(qLine.HLine);qLine.setLineWidth(2)
        h_layout = QHBoxLayout(); h_layout.addWidget(qLine)
        self.layout_.addItem(h_layout, 1, 0, rowSpan=1, columnSpan=2)
        
        # nameLabel + countdownLabel
        self.nameLabel = QLabel()
        self.countdownLabel = QLabel()
        utils_qt.setFont(self.nameLabel, 20)
        utils_qt.setFont(self.countdownLabel, 20)
        self.layout_.addWidget(self.nameLabel,2,0)
        self.layout_.addWidget(self.countdownLabel,2,1)

        # startEndLabel and nextEvent label
        self.startEndLabel = QLabel()
        self.nextEventLabel = QLabel()
        self.layout_.addWidget(self.startEndLabel,3,0)
        self.layout_.addWidget(self.nextEventLabel,3,1)
    
    def _position(self):
        """ positions widget at right edge of screen, slightly above center"""
        self.show()   
        geo = self.frameGeometry() # QRect (x,y, width, height)
        screen_upper_right = utils_qt.getScreenUpperRight()
        geo.moveBottomRight(screen_upper_right)
        self.move(geo.topLeft()) # move(QPoint=x,y)
       
    # labels
    def update_startEnd_label(self):
        """ sets StarTEndLabel to show 8:30-12:40"""
        startEndStr = utils_time.datetimes_to_hours_minutes(self.start_datetime, self.end_datetime)
        self.startEndLabel.setText(startEndStr)
    
    def set_name(self, name: str):
         self.nameLabel.setText(name)
         self.nameLabel.adjustSize()
    
    def get_name(self) -> str: return self.nameLabel.text()
 
    def reset_labels(self):
        self.projectLabel.setText('')
        self.listLabel.setText('')
        self.nameLabel.setText('')
        self.countdownLabel.setText('')
        self.startEndLabel.setText('')
        self.nextEventLabel.setText('')

    def update_countdown_label(self):
        countdown_str = utils_time.QTime_to_str(self.countdown_time)
        self.countdownLabel.setText(countdown_str)
        self.countdownLabel.adjustSize()
    
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
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.showMinimized() 
        elif e.key() in [Qt.Key_F5, Qt.Key_R]:
            self.refresh_callback()
        elif e.key() == Qt.Key_F:
            self.finish_event_callback()
        elif e.key() in [Qt.Key_Equal, Qt.Key_Plus]:
            self.change_minutes_callback(2)
        elif e.key() in [Qt.Key_Underscore, Qt.Key_Minus]:
            self.change_minutes_callback(-0.2)
        elif e.key() == Qt.Key_N:
            self.play_next_callback()
        elif e.key() == Qt.Key_Q:
            self.exit_callback()
        elif e.key() == Qt.Key_B:
            self.break_callback()
        
    
    # general
    def start(self, task: Task):
        """starts new event"""    
        self.timer.stop()
        self.task = task
        # set labels
        self.setWindowTitle(task.name)
        self.projectLabel.setText(task.project.capitalize())
        self.listLabel.setText(task.list)
        self.projectLabel.adjustSize(); self.listLabel.adjustSize()
        self.nextEventLabel.setText(task.next_event_name); self.nextEventLabel.adjustSize()
        self.name = task.name
        self.set_name(task.name)
        
        # set startime, endtime
        self.start_datetime = task.start_datetime 
        self.end_datetime = task.end_datetime
        self.update_startEnd_label()
        
        # set coundown
        countdown_time = utils_time.timedelta_to_datetime_time(task.end_datetime - task.start_datetime) # type: datetime.time
        self.countdown_time = QTime(countdown_time) # type: ignore
        self.update_countdown_label()
        # start timer
        self.timer.start(self.countdownDeltaMS)

        if self.isVisible() is False:
            self.show()
        self.adjustSize()
        self._position()
        self.setToolTip(task.description)

    # time
    def reset_coundown_time(self): self.countdown_time = QTime()
    
    def end_cur_event(self):
        self.stop_flash()
        self.reset_coundown_time()
        self.timer.stop()
        self.reset_labels()    
    
    def is_timer_ended(self) -> bool:
        return self.countdown_time == QTime(0,0,1)
    
    def change_minutes(self, minutes: float):
        self.end_datetime += datetime.timedelta(minutes=minutes)
        self.update_startEnd_label()
        
        self.countdown_time = self.countdown_time.addSecs(int(minutes * 60))
        self.update_countdown_label()
        self.stop_flash()
        
    def is_event(self):
        return self.name != BREAK and self.task.project.lower() not in ['tasks', 'events', 'chores', BREAK]
    
    # Callbacks
    def timeout(self):
        self.countdown_time = self.countdown_time.addMSecs(-self.countdownDeltaMS)
        self.update_countdown_label()
        if self.is_timer_ended():
            now = utils_time.get_current_local(with_seconds=True)
            print(f'eventWindow::timeout() timer for {self.name} ended!!! at ', now.time())
            self.timer.stop()
            self.timer_callback()
        elif self.countdown_time < self.flashTime and self.is_event() : # type: ignore
            self.start_flash()
            self.toggle_background_color()
        elif self.countdown_time < self.breakFlashTime and not self.is_event() : # type: ignore
            self.start_flash()
            self.toggle_background_color()
    
    def set_timer_callback(self, callback): 
        self.timer_callback = callback 

    def set_refresh_callback(self, callback):
        self.refresh_callback = callback

    def set_finish_event_callback(self, callback): self.finish_event_callback = callback
    
    def set_change_minutes_callback(self, callback): self.change_minutes_callback = callback
    
    def set_play_next_callback(self, callback): self.play_next_callback = callback
    
    def set_exit_callback(self, callback): self.exit_callback = callback
    
    def set_break_callback(self, callback): self.break_callback = callback
    
    # flash
    def toggle_background_color(self):
        if self.isRedBackground:
            self.setStyleSheet("background-color: blue;")
            self.isRedBackground = False
        else:
            self.setStyleSheet("background-color: red;")
            self.isRedBackground = True
    
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



    