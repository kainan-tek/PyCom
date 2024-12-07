from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QWidget

import globalvar as gl
from ui.about_ui import Ui_About


class About(QWidget):
    def __init__(self) -> None:
        """
        Constructor of the About window class.

        Initialize the UI and set up the About window.

        Args:
            None

        Returns:
            None
        """
        super(About, self).__init__()

        # Set up the UI
        self.ui: Ui_About = Ui_About()
        self.ui.setupUi(self)

        # Initialize the About window
        self.ui_init()

    def ui_init(self) -> None:
        """
        Initialize the UI of the About window.

        Move the cursor to the start of the text, insert the text into the text edit widget, and then move the cursor back to the start of the text.

        Args:
            None

        Returns:
            None
        """
        # Move the cursor to the start of the text.
        self.ui.textEdit_About.moveCursor(QTextCursor.Start)  # type: QTextCursor
        # Insert the text into the text edit widget.
        self.ui.textEdit_About.insertPlainText(gl.AboutInfo)  # type: str
        # Move the cursor back to the start of the text.
        self.ui.textEdit_About.moveCursor(QTextCursor.Start)  # type: QTextCursor
