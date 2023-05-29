from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QWidget

import globalvar as gl
from ui.about_ui import Ui_About


class About(QWidget):
    def __init__(self):
        super(About, self).__init__()
        self.ui = Ui_About()
        self.ui.setupUi(self)
        self.ui_init()

    def ui_init(self):
        self.ui.textEdit_About.moveCursor(QTextCursor.Start)
        self.ui.textEdit_About.insertPlainText(gl.AboutInfo)
        self.ui.textEdit_About.moveCursor(QTextCursor.Start)
