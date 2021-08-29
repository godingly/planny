

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtWidgets import QApplication, QWidget

LARGE_FONT_SIZE = 22

def getScreenCenter() -> QPoint:
    screenGeometry = QApplication.desktop().availableGeometry() #QRect, (0,0,1920,1048) (x,y, width, height)
    return screenGeometry.center()
    

def getScreenUpperRight() -> QPoint:
    screenGeometry = QApplication.desktop().availableGeometry() #QRect, (0,0,1920,1048) (x,y, width, height)
    return QPoint(int(screenGeometry.right()*0.96), screenGeometry.height()//3)

def setFont(widget: QWidget, size: int):
    font = widget.font()
    font.setPointSize(size)
    widget.setFont(font)

def toggleWindow(qWidget: QWidget):
    if qWidget.isVisible():
        qWidget.hide()
    else:
        qWidget.show()



# flash

def resetBackgroundColor(qWidget : QWidget): qWidget.setStyleSheet("")