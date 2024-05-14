from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QWidget

import globalvar as gl
from ui.about_ui import Ui_About


class About(QWidget):
    """
    Constructor of the About window class.

    Initialize the UI, and set up the About window.
    """
    def __init__(self):
        super(About, self).__init__()
        
        # Set up the UI
        self.ui = Ui_About()
        self.ui.setupUi(self)
        
        # Initialize the About window
        self.ui_init()

    """
    Initialize the UI of the About window.

    Load the information from the global variable 'gl.AboutInfo' into the
    text edit widget of the About window.
    """
    def ui_init(self):
        # Move the cursor to the start of the text.
        self.ui.textEdit_About.moveCursor(QTextCursor.Start)
        # Insert the text into the text edit widget.
        self.ui.textEdit_About.insertPlainText(gl.AboutInfo)
        # Move the cursor back to the start of the text.
        self.ui.textEdit_About.moveCursor(QTextCursor.Start)
