import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QHBoxLayout,QLineEdit, QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from functools import partial
from planny.model import Model

# View
class PlannyUi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("planny")
        self.generalLayout=QHBoxLayout()
        self._createDisplay()
        self.setLayout(self.generalLayout)

    def _createDisplay(self):
        self.display = QLineEdit()
        self.display.setFixedHeight(35)
        self.display.setAlignment(Qt.AlignLeft)
        self.display.setText('hello'); self.display.setText('')
        self.generalLayout.addWidget(self.display)
        

    def displayText(self): return self.display.text()
    def setDisplayText(self, text): self.display.setText(text); self.display.setFocus()
    def clearDisplay(self): self.setDisplayText('')

# Controller
class PlannyCtrl:
    def __init__(self, model: Model, view: PlannyUi) -> None:
        self._view = view
        self._model = model
        self._connectSignals()
    
    def _evaluate(self) -> None:
        expr = self._view.displayText()
        if expr.lower() == 'exit':
            exit()
        self._model.evaluate(expr)
        # update View 
        self._view.clearDisplay()
    
    def _connectSignals(self) -> None:
        self._view.display.returnPressed.connect(partial(self._evaluate))


def main():
    app = QApplication(sys.argv)
    # Viewer
    view = PlannyUi()
    # Controller
    model = Model()
    PlannyCtrl(view=view, model=model)
    view.show()
    # Executre
    sys.exit(app.exec_())

