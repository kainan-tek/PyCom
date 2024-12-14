import sys
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtWidgets import QApplication, QWidget, QPushButton
from PySide6.QtGui import QPainter, QColor, QPen


class SwitchButton(QPushButton):
    def __init__(self, parent: QWidget = None) -> None:
        """
        Initialize the SwitchButton.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.

        Returns:
            None
        """
        super(SwitchButton, self).__init__(parent)
        self.bt_width: int = 80
        self.bt_heigh: int = 30
        self.setFixedSize(QSize(self.bt_width, self.bt_heigh))
        self.setCheckable(True)
        self.setChecked(False)

    def paintEvent(self, event: QEvent) -> None:
        """
        Paint the button's background and handle.

        Args:
            event (QEvent): The paint event.

        Returns:
            None
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # bg_color: QColor = QColor(197, 197, 197)
        bg_color: QColor = QColor(212, 215, 220)
        handle_color: QColor = QColor(255, 255, 255)

        if self.isChecked():
            # bg_color = QColor(1, 116, 209)
            # bg_color = QColor(191, 236, 223)
            bg_color = QColor(199, 237, 204)
            handle_color = QColor(255, 255, 255)

        painter.setBrush(bg_color)
        painter.setPen(QPen(Qt.NoPen))
        # painter.setPen(QPen(Qt.black,2,Qt.SolidLine))
        painter.drawRoundedRect(
            0, 0, self.bt_width, self.bt_heigh, self.bt_heigh//2, self.bt_heigh//2)

        gap_size: int = 4
        handle_height: int = self.bt_heigh - 2*gap_size
        handle_x: int = self.bt_width - handle_height - \
            gap_size if self.isChecked() else gap_size
        handle_y: int = gap_size
        painter.setBrush(handle_color)
        painter.setPen(QPen(Qt.NoPen))
        painter.drawEllipse(handle_x, handle_y, handle_height, handle_height)


class Example(QWidget):
    def __init__(self) -> None:
        """
        Initialize the Example widget.

        Args:
            None

        Returns:
            None
        """
        super().__init__()
        switchBtn: SwitchButton = SwitchButton(self)
        switchBtn.move(50, 50)
        switchBtn.toggled.connect(self.onToggle)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('QSwitchButton')
        self.show()

    def onToggle(self, checked: bool) -> None:
        """
        Called when the switch button's toggle state changes.

        Args:
            checked: True if the button is checked, False otherwise

        Returns:
            None
        """
        if checked:
            self.setWindowTitle('Button Opened')
        else:
            self.setWindowTitle('Button Closed')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec())
