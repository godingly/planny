import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QGridLayout, QLineEdit, QMainWindow
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget
from functools import partial
ERROR_MSG='ERROR'

# View
class PyCalcUi(QMainWindow):
    def __init__(self):
        # init
        super().__init__()
        self.setWindowTitle('PyCalc')
        self.setFixedSize(235,235)
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        # layout
        self.generalLayout = QVBoxLayout()
        self._centralWidget.setLayout(self.generalLayout)
        self._createDisplay()
        self._createButtons()

    def _createDisplay(self):
        self.display = QLineEdit()
        self.display.setFixedHeight(35)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        self.generalLayout.addWidget(self.display)

    def _createButtons(self):
        """Create the buttons."""
        self.buttons = {}
        buttonsLayout = QGridLayout()
        # Button text | position on the QGridLayout
        buttons = {'7': (0, 0),
                   '8': (0, 1),
                   '9': (0, 2),
                   '/': (0, 3),
                   'C': (0, 4),
                   '4': (1, 0),
                   '5': (1, 1),
                   '6': (1, 2),
                   '*': (1, 3),
                   '(': (1, 4),
                   '1': (2, 0),
                   '2': (2, 1),
                   '3': (2, 2),
                   '-': (2, 3),
                   ')': (2, 4),
                   '0': (3, 0),
                   '00': (3, 1),
                   '.': (3, 2),
                   '+': (3, 3),
                   '=': (3, 4),
                  }
        # Create the buttons and add them to the grid layout
        for btnText, pos in buttons.items():
            self.buttons[btnText] = QPushButton(btnText)
            self.buttons[btnText].setFixedSize(40, 40)
            buttonsLayout.addWidget(self.buttons[btnText], pos[0], pos[1])
        # Add buttonsLayout to the general layout
        self.generalLayout.addLayout(buttonsLayout)

    def setDisplayText(self, text):
        self.display.setText(text)
        self.display.setFocus()
    def displayText(self):
        return self.display.text()
    def clearDisplay(self):
        self.setDisplayText('')

# Controller
class PyCalcCtrl:
    def __init__(self,model, view):
        self._view=view # view.generalLayout, view.display, view._centralWidget, view.buttons{'7':QPushButton}
        self._evaluate=model
        self._connectSignals()

    def _calculateResult(self):
        result = self._evaluate(expression=self._view.displayText())
        self._view.setDisplayText(result)
    
    def _buildExpression(self, sub_exp):
        if self._view.displayText()==ERROR_MSG:
            self._view.clearDisplay()
        expression = self._view.displayText()+sub_exp
        self._view.setDisplayText(expression)
    
    def _connectSignals(self):
        for btnText, btn in self._view.buttons.items():
            if btnText not in {'=','C'}:
                btn.clicked.connect(partial(self._buildExpression, btnText))
        self._view.buttons['='].clicked.connect(self._calculateResult)
        self._view.display.returnPressed.connect(self._calculateResult)
        self._view.buttons['C'].clicked.connect(self._view.clearDisplay)

# MODEL
def evaluateExpression(expression):
    try:
        result = str(eval(expression,{},{}))
    except ValueError:
        result = ERROR_MSG
    return result

def main():
    app = QApplication(sys.argv)
    # GUI - Create and Show
    view = PyCalcUi()
    view.show()
    # Create Model and controllel
    PyCalcCtrl(view=view, model=evaluateExpression)
    # Excecuate Main loop
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
    
    