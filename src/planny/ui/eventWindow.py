from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel
from PyQt5.QtCore import QTimer, QTime, Qt
from planny.utils import qt as utils_qt
from planny.utils import time as utils_time
import datetime

class EventWindow(QDialog):
    def __init__(self, args):
        super().__init__()
        self.args = args
        # init
        self.layout_ = QGridLayout()
        self.resize(100, 50) # width, height
        self.zeroTime = QTime(0,0,0)
        self._initWidgets()
        
        # timer        
        self.timer = QTimer()
        self.timer.timeout.connect(self.timeout)
        self.startDateTime = datetime.datetime.min
        self.endtDateTime : datetime.datetime
        self.countdownTime : QTime
        self.mSecsPassed = 0  # int, number of microsecnds from start
        self.countdownDeltaMS = 1000
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint) # type: ignore

        # flash
        self.flashTime = QTime(0,0,40)
        self.isFlashOn = False
        self.isBlueBackground = False
        
        self.setLayout(self.layout_)


    def _initWidgets(self):
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
        screenUperrRight = utils_qt.getScreenUpperRight()
        geo.moveBottomRight(screenUperrRight)
        self.move(geo.topLeft()) # move(QPoint=x,y)
    
    def updateStartEndLabel(self):
        """ sets StarTEndLabel to show 8:30-12:40"""
        startEndStr = utils_time.datetimes_to_hours_minutes(self.startDateTime, self.endDateTime)
        self.startEndLabel.setText(startEndStr)
    
    # overriding
    def closeEvent(self, event):
        self.endCurEvent()
        event.accept()
    
    def start(self, summary: str,
              startDateTime: datetime.datetime,
              endDateTime: datetime.datetime,
              countdownTime : datetime.time):
        """ starts new event"""    
        self.timer.stop()
        
        # set summary
        self.setWindowTitle(summary)
        self.setSummary(summary)
        
        # set startime, endtime
        self.startDateTime = startDateTime 
        self.endDateTime = endDateTime
        self.updateStartEndLabel()
        
        # set coundown
        self.setCountdownTime(countdownTime)
        self.updateCountdownLabel()
        # start timer
        self.timer.start(self.countdownDeltaMS)

    
    def setSummary(self, summary: str):
         self.summaryLabel.setText(summary)
         self.adjustSize()
         self._position()
    
    def getSummary(self) -> str: return self.summaryLabel.text()
    
    def setCountdownTime(self, time: datetime.time): self.countdownTime = QTime(time) # type: ignore
    def resetCoundownTime(self): self.countdownTime = QTime()
    def getMSecsToStart(self) -> int: 
        """ how many microseconds have passed since the start"""
        return self.mSecsPassed

    def endCurEvent(self):
        self.stopFlash()
        self.resetCoundownTime()
        self.timer.stop()
        self.mSecsPassed = 0
        self.summaryLabel.setText('')
        self.countdownLabel.setText('')

    def timeout(self):
        self.countdownTime = self.countdownTime.addMSecs(-self.countdownDeltaMS)
        self.mSecsPassed += self.countdownDeltaMS
        self.updateCountdownLabel()
        if self.isTimerEnded():
            summary = self.getSummary()
            print(f'timer for {summary} ended!!!')
            self.timer.stop()
            self.timerCallback(summary)
        elif self.countdownTime < self.flashTime: # type: ignore
            self.startFlash()
            self.toggleBackGroundColor()
            
    def setTimerCallBack(self, callback): 
        self.timerCallback = callback 
    
    def updateCountdownLabel(self):
        countdown_str = utils_time.QTime_to_str(self.countdownTime)
        self.countdownLabel.setText(countdown_str)

    def isTimerEnded(self) -> bool:
        return self.countdownTime == self.zeroTime
    
    def addMinutes(self, minutes: int):
        self.endDateTime += datetime.timedelta(minutes=minutes)
        self.updateStartEndLabel()
        
        self.countdownTime = self.countdownTime.addSecs(minutes * 60)
        self.updateCountdownLabel()
        self.stopFlash()
        
    # flash
    def toggleBackGroundColor(self):
        if self.isBlueBackground:
            self.setStyleSheet("background-color: red;")
            self.isBlueBackground = False
        else:
            self.setStyleSheet("background-color: blue;")
            self.isBlueBackground = True
    
    def startFlash(self):
        if self.isFlashOn:
            return
        self.timer.stop()
        self.countdownDeltaMS = 200
        self.timer.start(self.countdownDeltaMS)
        self.isFlashOn = True
    
    def stopFlash(self):
        utils_qt.resetBackgroundColor(self)
        self.isFlashOn = False
        self.timer.stop()
        self.countdownDeltaMS = 1000
        self.timer.start(self.countdownDeltaMS)



    