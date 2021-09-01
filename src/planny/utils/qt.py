from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget

import random
import string

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


def set_icon(app, icon_path: str, app_id: str=""):
    if not app_id: app_id = "".join(random.choices(string.ascii_lowercase, k=10))
    # icon
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    icon = QIcon(icon_path)
    app.setWindowIcon(icon)

# flash

def resetBackgroundColor(qWidget : QWidget):
     qWidget.setStyleSheet("")