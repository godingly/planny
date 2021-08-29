import sys

from PyQt5.QtWidgets import QApplication
from planny.model import Model
from planny.ctrl import Ctrl
from planny.ui.plannyWidget import PlannyWidget


def main(args):
    app = QApplication(sys.argv)
    # Viewer
    view = PlannyWidget(args)
    # Controller
    model = Model(args)
    Ctrl(view=view, model=model)
    view.show()
    # Execute
    sys.exit(app.exec())

