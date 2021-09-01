""" Viewer """
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt

class LineEdit(QDialog):
    def __init__(self, args, parent=None):
        super().__init__(parent)
        self.args = args
        if args.debug:
            self.setWindowTitle("planny test")
        else:
            self.setWindowTitle("planny real")
        self.layout_=QHBoxLayout()
        self.createEditLine()
        self.setLayout(self.layout_)

    def createEditLine(self):
        self.editline = QLineEdit()
        self.editline.setFixedHeight(35)
        self.editline.setAlignment(Qt.AlignLeft)
        # hack to make input more easier
        self.editline.setText('hello'); self.editline.setText('')

        self.layout_.addWidget(self.editline)
        
    # overriding
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.showMinimized()
    
    def lineEditText(self): return self.editline.text()
    def setLineEditText(self, text): self.editline.setText(text); self.editline.setFocus()
    def clearLineEditText(self): self.setLineEditText('')




