from planny import ERROR_MSG
import sys,os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QStatusBar, QToolBar
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget
from functools import partial

# GUI
class PlannyUi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("planny")
        self.generalLayout=QVBoxLayout()
        self._createDisplay()
        self.setLayout(self.generalLayout)

    def _createDisplay(self):
        self.display = QLineEdit()
        self.display.setFixedHeight(35)
        self.display.setAlignment(Qt.AlignLeft)
        self.generalLayout.addWidget(self.display)

    def displayText(self): return self.display.text()
    def setDisplayText(self, text): self.display.setText(text); self.display.setFocus()
    def clearDisplay(self): self.setDisplayText('')

# Controller
class PlannyCtrl:
    def __init__(self, model, view):
        self._view=view
        self._model=model
        self._connectSignals()
    
    def _evaluate(self):
        expr = self._view.displayText()
        self._model.evaluate(expr)
        self._view.clearDisplay()
    
    def _connectSignals(self):
        self._view.display.returnPressed.connect(self._evaluate)
# Model
class PlannyModel:
    def init(self):
        pass
    def evaluate(self, expression):
        print(expression)

def main():
    app = QApplication(sys.argv)
    # Viewer
    view = PlannyUi()
    view.show()
    # Controller
    model = PlannyModel()
    ctrl = PlannyCtrl(view=view, model=model)
    # Executre
    sys.exit(app.exec_())

if __name__=='__main__':
    main()