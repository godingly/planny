from functools import partial

from planny.model import Model
from planny.ui.plannyWidget import PlannyWidget
from planny.utils.utils import *
SHOW_EVENT = 'SHOW_EVENT'


class Ctrl:
    def __init__(self, model: Model, view: PlannyWidget) -> None:
        self.view = view
        self.model = model
        self.connectSignals()
        self.minutesTracked = 0
    
    def evaluate(self) -> None:
        expr = self.view.getQuery()
        self.view.clearQuery()
        if expr.lower() == 'exit':
            self.exit()
        elif expr.lower() in EVENT_FINISH_CODES:
            self.endCurEvent()
        
        type_, data = self.model.evaluate(expr)

        if type_== Expr_Type.EVENT:
            self.endCurEvent()
            self.view.createEvent(data)

        elif type_ == Expr_Type.MORE_MINUTES:
            self.addMinutes(int(data['minutes']))


    def exit(self):
        self.endCurEvent()
        self.model.updateTimeTracked()
        exit()
    
    def connectSignals(self) -> None:
        self.view.lineEdit.editline.returnPressed.connect(partial(self.evaluate))
        self.view.setTimerCallBack(self.timerCallback)

    def timerCallback(self, summary, amount=0):
        print("timer ended")
        self.model.beeCharge(summary, amount)

    def addMinutes(self, minutes):
        self.view.addMinutes(minutes)


    def getSecsToStart(self) -> int:
        return self.view.getSecsToStart()

    def endCurEvent(self):
        secsToStart = self.view.getSecsToStart() # int
        self.model.addTimeTracked(secsToStart)
        self.view.endCurEvent()