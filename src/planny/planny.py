import sys

from PyQt5.QtWidgets import QApplication
from planny.model import Model
from planny.ctrl import Ctrl
from planny.ui.plannyWidget import PlannyWidget
import planny.utils.qt as utils_qt
from pathlib import Path

def set_icon(app):
    dir_path = Path(__file__).parent.resolve()
    icon_path = Path(dir_path.parent, 'resources', 'todo_icon.png')
    utils_qt.set_icon(app, str(icon_path), 'planny_app')

def main(args):
    app = QApplication(sys.argv)
    set_icon(app)

    # Viewer
    view = PlannyWidget(args)
    # Controller
    model = Model(args)
    Ctrl(view=view, model=model)
    view.show()
    # Execute
    sys.exit(app.exec())

