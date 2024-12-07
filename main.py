import os
import queue
import re
import string
import sys
import time

import chardet
import serial
import serial.tools.list_ports
from PySide6.QtCore import QEvent, QMutex, QThread, QTimer, Signal, QObject
from PySide6.QtGui import QIcon, QIntValidator, Qt, QTextCursor
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QMainWindow, QMessageBox, QLineEdit

import globalvar as gl
import resrc.resource_rc
from about import About
from jsonparser import JsonFlag, JsonParser
from logwrapper import log_inst
from ui.mainwindow_ui import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        """
        Initialize the MainWindow class.

        This function initializes the UI by calling the setupUi method of the
        Ui_MainWindow class. It also initializes some variables and objects for
        the MainWindow class.

        Args:
            None

        Returns:
            None
        """
        super(MainWindow, self).__init__()
        self.log = log_inst.logger
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.about = About()
        self.var_init()
        self.gui_init()
        self.parse_ports()

    def var_init(self) -> None:
        """
        Initialize various variables and objects for the MainWindow class.

        Sets up initial values for send/receive sizes, data encoding, and UI components.
        Also sets up timers and threads for data sending and receiving.

        Args:
            None

        Returns:
            None
        """
        self.total_sendsize: int = 0  # The total send size
        self.total_recsize: int = 0  # The total received size
        self.datasize_text: str = ""  # The text to show the send/receive size
        self.recdatas_file: str = ""  # The file name of the received data
        self.encode_info: str = "gbk"  # The encoding of the received data
        self.multi_dict: dict = {}  # The dictionary of the multiple send data
        self.js_send_list: list = []  # The list of the json file data
        self.mutex: QMutex = QMutex()  # The mutex for the data sending
        self.msgbox: QMessageBox = QMessageBox()  # The message box instance
        self.ser_instance: serial.Serial = serial.Serial()  # The serial port instance
        self.send_timer: QTimer = QTimer()  # The timer for the data sending
        self.send_timer.timeout.connect(self.data_send)
        self.fsend_timer: QTimer = QTimer()  # The timer for the json file data sending
        self.fsend_timer.timeout.connect(self.jsfile_data_send)
        self.recthread: WorkThread = WorkThread(self.ser_instance)
        self.recthread.rec_signal.connect(self.update_receive_ui)
        self.recthread.close_signal.connect(self.post_close_port)
        self.recthread.start()

        self.key_limits: list = [
            Qt.Key_0, Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5, Qt.Key_6, Qt.Key_7, Qt.Key_8,
            Qt.Key_9, Qt.Key_A, Qt.Key_B, Qt.Key_C, Qt.Key_D, Qt.Key_E, Qt.Key_F, Qt.Key_Space,
            Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Right, Qt.Key_Left, Qt.Key_Up, Qt.Key_Down,
            Qt.Key_Control, Qt.Key_Shift, Qt.Key_Copy, Qt.Key_Paste
        ]

    def gui_init(self) -> None:
        """
        Initialize the GUI components

        Set up the window title and icon, configure the serial port options,
        connect the actions to corresponding functions, and set up the single
        and multiple send options.

        Args:
            None

        Returns:
            None
        """
        # Set window title and icon
        self.setWindowTitle(f'{gl.GuiInfo["proj"]} {gl.GuiInfo["version"]}')
        self.setWindowIcon(QIcon(":/icon/pycom"))

        # Menu setup: connect actions to corresponding functions
        self.ui.actionOpen_File.triggered.connect(self.action_open_file)
        self.ui.actionExit.triggered.connect(self.action_exit)
        self.ui.actionASCII.triggered.connect(self.action_encoding_ascii)
        self.ui.actionUTF_8.triggered.connect(self.action_encoding_utf8)
        self.ui.actionUTF_16.triggered.connect(self.action_encoding_utf16)
        self.ui.actionUTF_32.triggered.connect(self.action_encoding_utf32)
        self.ui.actionGBK_GB2312.triggered.connect(self.action_encoding_gbk)
        self.ui.actionAbout.triggered.connect(self.action_about)

        # Serial port setup: configure serial port options
        self.ui.comboBox_BRate.addItems(gl.SerialInfo["baudrate"])  # Add baud rate options
        self.ui.comboBox_BRate.setCurrentText('115200')  # Set default baud rate
        self.ui.comboBox_BSize.addItems(gl.SerialInfo["bytesize"])  # Add byte size options
        self.ui.comboBox_BSize.setCurrentText('8')  # Set default byte size
        self.ui.comboBox_SBit.addItems(gl.SerialInfo["stopbit"])  # Add stop bit options
        self.ui.comboBox_SBit.setCurrentText('1')  # Set default stop bit
        self.ui.comboBox_PBit.addItems(gl.SerialInfo["paritybit"])  # Add parity bit options
        self.ui.comboBox_PBit.setCurrentText('None')  # Set default parity bit
        self.ui.pushButton_Check.clicked.connect(self.parse_ports)  # Connect check button
        self.ui.pushButton_Open.clicked.connect(self.open_port)  # Connect open button
        self.ui.pushButton_Close.clicked.connect(self.close_port)  # Connect close button
        self.ui.pushButton_Open.setEnabled(True)  # Enable open button
        self.ui.pushButton_Close.setEnabled(False)  # Disable close button

        # Single send setup: connect single send options
        self.ui.pushButton_sSend.clicked.connect(self.single_data_send)
        self.ui.pushButton_sClear.clicked.connect(self.send_clear)
        self.ui.pushButton_RClear.clicked.connect(self.receive_clear)
        self.ui.pushButton_RSave.clicked.connect(self.receive_save)
        self.ui.checkBox_sHexmode.clicked.connect(self.send_set_hexmode)
        self.ui.checkBox_RHexmode.clicked.connect(self.receive_set_hexmode)
        self.ui.checkBox_sCycle.clicked.connect(self.send_set_cyclemode)
        self.ui.textEdit_sSend.installEventFilter(self)
        self.ui.lineEdit_sCycle.setValidator(QIntValidator())

        # Multiple send setup: connect multiple send options
        self.ui.pushButton_m1.clicked.connect(self.multi_send_m1)
        self.ui.pushButton_m2.clicked.connect(self.multi_send_m2)
        self.ui.pushButton_m3.clicked.connect(self.multi_send_m3)
        self.ui.pushButton_m4.clicked.connect(self.multi_send_m4)
        self.ui.pushButton_m5.clicked.connect(self.multi_send_m5)
        self.ui.pushButton_m6.clicked.connect(self.multi_send_m6)
        self.ui.checkBox_mCycle.clicked.connect(self.multi_send_set_cyclemode)
        self.ui.lineEdit_mCycle.setValidator(QIntValidator())

        # File send setup: connect file send options
        self.ui.pushButton_fSelect.clicked.connect(self.file_send_select)
        self.ui.pushButton_fSend.clicked.connect(self.file_send)

        # Guide setup: set guide information text
        self.ui.plainTextEdit_Guide.setPlainText(gl.GuideInfo)

        # Status bar setup: initialize and add data size status
        self.datasize_text = "  Send: 0  |  Receive: 0  "
        self.label_rwsize = QLabel(self.datasize_text)
        self.label_rwsize.setStyleSheet("color:blue")
        self.ui.statusbar.addPermanentWidget(self.label_rwsize, stretch=0)

    def send_clear(self) -> None:
        """
        Clear the single send text edit and move the cursor to the start.

        Args:
            None

        Returns:
            None
        """
        self.ui.textEdit_sSend.clear()
        self.ui.textEdit_sSend.moveCursor(QTextCursor.Start)

########################## port function ############################

    def parse_ports(self) -> bool:
        """
        Parse the serial ports and add them to the combo box.

        If the serial port is open, show an information message box and return False.

        Args:
            None

        Returns:
            bool: True if the port is closed and the ports are parsed successfully, False otherwise
        """
        if self.ser_instance.isOpen():  # Check if the port is open
            self.msgbox.information(self, "Info", "Please close port first")
            return False  # Return False if the port is open

        # Clear the combo box
        self.ui.comboBox_SPort.clear()

        # Get the list of serial ports
        port_list: list = list(serial.tools.list_ports.comports())
        ports_list: list = [port[0] for port in port_list]
        self.ui.comboBox_SPort.addItems(ports_list)
        return True

    def open_port(self) -> bool:
        """
        Open the serial port.

        This function opens the serial port according to the settings in the combo boxes.

        Args:
            None

        Returns:
            bool: True if the port is opened successfully, False otherwise
        """
        self.ser_instance.port = self.ui.comboBox_SPort.currentText().strip()
        self.ser_instance.baudrate = int(self.ui.comboBox_BRate.currentText().strip())
        self.ser_instance.bytesize = int(self.ui.comboBox_BSize.currentText().strip())
        self.ser_instance.stopbits = int(self.ui.comboBox_SBit.currentText().strip())
        self.ser_instance.parity = self.ui.comboBox_PBit.currentText().strip()[0]
        self.ser_instance.timeout = gl.SerialInfo["timeout"]

        if not self.ser_instance.port:
            self.msgbox.information(self, "Info", "No port be selected")
            return False

        if not self.ser_instance.isOpen():
            try:
                self.ser_instance.open()
            except Exception as err:
                self.log.error(f"Error of opening port, err: {str(err)}")
                if "PermissionError" in str(err):
                    self.msgbox.critical(self, "PermissionError", "The selected port may be occupied!")
                else:
                    self.msgbox.critical(self, "Error", "Can not open the port with these params")
                return False
        if self.ser_instance.isOpen():
            self.ui.pushButton_Open.setEnabled(False)
            self.ui.pushButton_Close.setEnabled(True)
            return True

    def close_port(self) -> None:
        """
        Close the serial port.

        Check and deactivate single cycle send and multi cycle send if active.
        Stop the file send timer and trigger the serial close function in the receive thread.

        Args:
            None

        Returns:
            None
        """
        # Check and deactivate single cycle send if active
        if self.ui.checkBox_sCycle.isChecked():
            self.ui.checkBox_sCycle.click()

        # Check and deactivate multi cycle send if active
        if self.ui.checkBox_mCycle.isChecked():
            self.ui.checkBox_mCycle.click()

        # Stop the file send timer
        self.fsend_timer.stop()

        # Check if the serial instance is open
        if self.ser_instance.isOpen():
            # Trigger the serial close function in receive thread
            self.recthread.port_close_flag = True
            # Note: Closing the serial directly here may cause a crash
            # self.ser_instance.close()

    def post_close_port(self) -> None:
        """
        Post close the serial port.

        This function takes no arguments and returns no value.

        Args:
            None

        Returns:
            None
        """
        if not self.ser_instance.isOpen():
            self.ui.pushButton_Open.setEnabled(True)
            self.ui.pushButton_Close.setEnabled(False)

########################## single and multi send function ############################

    def data_send(self) -> bool:
        """
        Send data to the serial port.

        Checks if single cycle send or multi cycle send is activated, and calls
        the corresponding function to send the data.

        If both single cycle send and multi cycle send are activated, deactivates
        them all, logs an error, and shows a warning message.

        Args:
            None

        Returns:
            bool: True if the data is sent successfully, False otherwise
        """
        # Check if both single and multi cycle sends are activated
        if self.ui.checkBox_sCycle.isChecked() and self.ui.checkBox_mCycle.isChecked():
            # Deactivate both cycle sends
            self.ui.checkBox_sCycle.click()
            self.ui.checkBox_mCycle.click()
            msg: str = "Both single cycle send and multi cycle send are activated\nDeactivate them all, please try again"
            self.log.error(msg)
            self.msgbox.warning(self, "Warning", msg)
            return False

        # Check if single cycle send is activated
        if self.ui.checkBox_sCycle.isChecked():
            return self.single_data_send()
        # Check if multi cycle send is activated
        elif self.ui.checkBox_mCycle.isChecked():
            return self.multi_cycle_send()

    def is_send_hex_mode(self, text: str) -> bool:
        """
        Check if the given text string is a valid hex string.

        A valid hex string should have an even number of characters, and all
        characters should be hex digits.

        Args:
            text (str): the text string to be checked

        Returns:
            bool: True if the text string is a valid hex string, False otherwise
        """
        post_text: str = text.replace(" ", "")
        if not len(post_text) % 2 == 0:
            return False
        if not all(item in string.hexdigits for item in post_text):
            return False
        return True

########################## single send function ############################

    def send_clear(self) -> None:
        """
        Clear the send text edit widget.

        This function takes no arguments and returns nothing.

        Args:
            None

        Returns:
            None
        """
        self.ui.textEdit_sSend.clear()
        self.total_sendsize = 0
        self.update_rwsize_status(self.total_sendsize, self.total_recsize)

    def single_data_send(self) -> bool:
        """
        Send single data from the text edit widget.

        Read the data from the text edit widget, convert it to bytes and send it
        to the serial port. If the checkbox is checked, send the data in hexadecimal
        format with the newline character.

        Args:
            None

        Returns:
            bool: False if the serial port is not open, otherwise returns nothing.
        """
        int_list: list[int] = []
        newline_state: bool = self.ui.checkBox_sNewline.isChecked()
        text: str = self.ui.textEdit_sSend.toPlainText()

        if not self.ser_instance.isOpen():
            self.msgbox.information(self, "Info", "Please open a serial port first")
            return False
        if not text and not newline_state:
            return False

        if self.ui.checkBox_sHexmode.isChecked():
            if text:
                if not self.is_send_hex_mode(text):
                    if self.ui.checkBox_sCycle.isChecked():
                        self.ui.checkBox_sCycle.click()
                    msg: str = "Not correct hex format datas"
                    self.log.warning(msg)
                    self.msgbox.warning(self, "Warning", msg)
                    return False
                text_list: list[str] = re.findall(".{2}", text.replace(" ", ""))
                str_text: str = " ".join(text_list)
                if not str_text == text:
                    self.ui.textEdit_sSend.clear()
                    self.ui.textEdit_sSend.insertPlainText(str_text)
                int_list = [int(item, 16) for item in text_list]
            if newline_state:
                int_list.extend([13, 10])
            bytes_text: bytes = bytes(int_list)
        else:
            if newline_state:
                text = text + '\r\n'
            bytes_text: bytes = text.encode(self.encode_info, "replace")

        sendsize: int = self.ser_instance.write(bytes_text)
        self.total_sendsize += sendsize
        self.update_rwsize_status(self.total_sendsize, self.total_recsize)

    def send_set_cyclemode(self) -> bool:
        """
        Set the cycle mode of the single send feature.

        If the cycle mode checkbox is checked, start the timer with the cycle time
        set in the line edit widget. Otherwise, stop the timer. If the conditions
        are not met, show an information message box and return False.

        Args:
            None

        Returns:
            bool: False if the conditions are not met, otherwise returns True
        """
        if self.ui.checkBox_sCycle.isChecked():
            msg: str = ""
            cycle_text = self.ui.lineEdit_sCycle.text()
            send_text = self.ui.textEdit_sSend.toPlainText()
            if not self.ser_instance.isOpen():
                msg = "Please open a port first"
            elif not cycle_text:
                msg = "Please set cycle time first"
            elif cycle_text == "0":
                msg = "Cycle send time should be greater than 0"
            elif not send_text:
                msg = "Please fill send datas first"
            if msg:
                self.msgbox.information(self, "Info", msg)
                self.ui.checkBox_sCycle.setChecked(False)
                return False
            self.send_timer.start(int(cycle_text.strip()))
            self.ui.lineEdit_sCycle.setEnabled(False)
        else:
            self.send_timer.stop()
            self.ui.lineEdit_sCycle.setEnabled(True)
        return True

    def send_set_hexmode(self) -> None:
        """
        Toggle the hex mode for the send text edit widget.

        Converts the text to hexadecimal format if the hex mode is enabled,
        otherwise converts it back to text format.

        Args:
            None

        Returns:
            None
        """
        hexmode_state: bool = self.ui.checkBox_sHexmode.isChecked()
        text: str = self.ui.textEdit_sSend.toPlainText()

        if not text:
            return

        if hexmode_state:
            str_text: str = text.encode(self.encode_info, "replace").hex(" ")
        else:
            if not self.is_send_hex_mode(text):
                self.msgbox.warning(self, "Warning", "Incorrect hex format data, can't convert to text format")
                self.ui.checkBox_sHexmode.setChecked(True)
                return  # incorrect hex format
            str_text: str = bytes.fromhex(text.replace(" ", "")).decode(self.encode_info, "replace")

        self.ui.textEdit_sSend.clear()
        self.ui.textEdit_sSend.insertPlainText(str_text)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Override the event filter function to intercept key press events on the send text edit widget when the hex mode is enabled.

        If the hex mode is enabled and the key pressed is not a valid hexadecimal digit (0-9, a-f, A-F) or Ctrl+V, show a warning message box and return True to intercept the event.

        Args:
            obj (QObject): The object that triggered the event.
            event (QEvent): The event object containing information about the event.

        Returns:
            bool: True if the event is intercepted, False otherwise.
        """
        if event.type() == QEvent.KeyPress and obj is self.ui.textEdit_sSend and self.ui.checkBox_sHexmode.isChecked():
            if not event.key() in self.key_limits and not (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V):
                self.msgbox.warning(self, "Warning", "Hex mode now!\nPlease input 0-9, a-f, A-F")
                return True
        return super().eventFilter(obj, event)

########################## multi send function ############################

    def multi_send_m1(self):
        self.mx_common_send("1", self.ui.lineEdit_m1)

    def multi_send_m2(self):
        self.mx_common_send("2", self.ui.lineEdit_m2)

    def multi_send_m3(self):
        self.mx_common_send("3", self.ui.lineEdit_m3)

    def multi_send_m4(self):
        self.mx_common_send("4", self.ui.lineEdit_m4)

    def multi_send_m5(self):
        self.mx_common_send("5", self.ui.lineEdit_m5)

    def multi_send_m6(self):
        self.mx_common_send("6", self.ui.lineEdit_m6)

    def mx_common_send(self, seq: str, line_edit: QLineEdit) -> bool:
        """
        Set the checked status of the send buttons and text edits to the
        dictionary, and send the data if the button is checked and the text
        edit is not empty.

        Args:
            seq (str): Sequence number of the text edit.
            line_edit (QLineEdit): The text edit to read the data from.

        Returns:
            bool: True if the data is sent successfully, False otherwise.
        """
        int_list: list[int] = []
        text = line_edit.text()
        newline_state = self.ui.checkBox_mNewLine.isChecked()

        if not self.ser_instance.isOpen():
            self.msgbox.information(self, "Info", "Please open a serial port first")
            return False
        if not text and not newline_state:
            return False

        if self.ui.checkBox_mHexMode.isChecked():
            if text:
                if not self.is_send_hex_mode(text):
                    if self.ui.checkBox_mCycle.isChecked():
                        self.ui.checkBox_mCycle.click()
                    self.msgbox.warning(self, "Warning", f"Not correct hex format in Edit {seq}")
                    return False
                text_list: list[str] = re.findall(".{2}", text.replace(" ", ""))
                str_text: str = " ".join(text_list)
                if not str_text == text:
                    line_edit.clear()
                    line_edit.insert(str_text)
                int_list = [int(item, 16) for item in text_list]
            if newline_state:
                int_list.extend([13, 10])
            bytes_text = bytes(int_list)
        else:
            if newline_state:
                text = text+'\r\n'
            bytes_text = text.encode(self.encode_info, "replace")

        sendsize: int = self.ser_instance.write(bytes_text)
        self.total_sendsize += sendsize
        self.update_rwsize_status(self.total_sendsize, self.total_recsize)

    def multi_cycle_send(self) -> None:
        """
        Set the checked status of the send buttons and text edits to the
        dictionary, and send the data if the button is checked and the text
        edit is not empty.

        Args:
            None

        Returns:
            None
        """
        self.multi_dict["m1"][0] = 1 if self.ui.checkBox_m1.isChecked() and self.ui.lineEdit_m1.text() else 0
        self.multi_dict["m2"][0] = 1 if self.ui.checkBox_m2.isChecked() and self.ui.lineEdit_m2.text() else 0
        self.multi_dict["m3"][0] = 1 if self.ui.checkBox_m3.isChecked() and self.ui.lineEdit_m3.text() else 0
        self.multi_dict["m4"][0] = 1 if self.ui.checkBox_m4.isChecked() and self.ui.lineEdit_m4.text() else 0
        self.multi_dict["m5"][0] = 1 if self.ui.checkBox_m5.isChecked() and self.ui.lineEdit_m5.text() else 0
        self.multi_dict["m6"][0] = 1 if self.ui.checkBox_m6.isChecked() and self.ui.lineEdit_m6.text() else 0

        for item in self.multi_dict:
            if self.multi_dict[item][0] == 1 and self.multi_dict[item][1] == 0:
                self.multi_send_m1() if item == "m1" else 0
                self.multi_send_m2() if item == "m2" else 0
                self.multi_send_m3() if item == "m3" else 0
                self.multi_send_m4() if item == "m4" else 0
                self.multi_send_m5() if item == "m5" else 0
                self.multi_send_m6() if item == "m6" else 0
                self.multi_dict[item][1] = 1
                break

        if all(self.multi_dict[item][1] for item in self.multi_dict if self.multi_dict[item][0]):
            for item in self.multi_dict:
                self.multi_dict[item][1] = 0

    def multi_send_set_cyclemode(self) -> bool:
        """
        If the check box is checked, set the timer to send the data with
        the cycle time. If the check box is unchecked, stop the timer.

        Args:
            None

        Returns:
            bool: False if any validation fails, otherwise returns nothing
        """
        if self.ui.checkBox_mCycle.isChecked():
            msg: str = ""
            cycle_text = self.ui.lineEdit_mCycle.text()
            if not self.ser_instance.isOpen():
                msg = "Please open a port first"
            elif not cycle_text:
                msg = "Please set cycle time first"
            if msg:
                self.msgbox.information(self, "Info", msg)
                self.ui.checkBox_mCycle.setChecked(False)
                return False
            # [0,0] first 0 means checked status, second 0 means send status
            self.multi_dict = {f"m{i+1}": [0, 0] for i in range(6)}
            self.send_timer.start(int(cycle_text.strip()))
            self.ui.lineEdit_mCycle.setEnabled(False)
        else:
            self.send_timer.stop()
            self.ui.lineEdit_mCycle.setEnabled(True)

########################## file send function ############################

    def file_send_select(self) -> bool:
        """
        This function takes no arguments and returns a boolean indicating success or failure.

        Args:
            None

        Returns:
            bool: True if a file is selected successfully, False otherwise

        """
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setWindowTitle('Open File')
        dialog.setNameFilter("TXT File(*.txt *.json)")
        if not dialog.exec():
            return False
        file_name: str = dialog.selectedFiles()[0]
        # file_name,_ = self.dialog.getOpenFileName(
        #     self, 'Open File', '', 'TXT File(*.txt *.json)', '', QFileDialog.DontUseNativeDialog)
        if not file_name:
            return False
        self.log.info(f"send file: {file_name}")
        self.ui.lineEdit_fFile.setText(file_name)

    def predict_encoding(self, file: str) -> str:
        """
        Predict the encoding of a given file.

        Args:
            file (str): The path to the file for which encoding needs to be determined.

        Returns:
            str: The predicted encoding of the file.
        """
        with open(file, 'rb') as f:
            encodeinfo = chardet.detect(f.read())
        return encodeinfo['encoding']

    def file_send(self) -> bool:
        """
        This function takes no arguments and returns a boolean indicating success or failure.

        Args:
            None

        Returns:
            bool: True if the file is sent successfully, False otherwise
        """
        if not self.ser_instance.isOpen():
            self.msgbox.information(self, "Info", "Please open serial port first")
            return False

        sfile: str = self.ui.lineEdit_fFile.text()
        if not sfile or not os.path.exists(sfile):
            self.msgbox.information(self, "Info", "the file is not existed")
            return False
        encode: str = self.predict_encoding(sfile)

        basename: str = os.path.basename(sfile)
        self.js_send_list.clear()
        if "json" in basename:
            # for json file
            jsparser: JsonParser = JsonParser(sfile)
            ret: tuple[JsonFlag, dict] = jsparser.file_read(encode)
            if not ret[0].value == JsonFlag.SUCCESS.value:
                msgtext: str = f'Error of reading json fie, err: {ret[0].name}'
                self.log.error(msgtext)
                self.msgbox.critical(self, "Error", msgtext)
                return False
            js_dict: dict = ret[1]
            cycle_time: int = js_dict["cycle_ms"]
            hex_mode: int = js_dict["hexmode"]
            if hex_mode:
                for i in range(len(js_dict["datas"])):
                    str_data: str = js_dict["datas"][i]["data"].replace(" ", "")
                    if not all(item in string.hexdigits for item in str_data):
                        self.msgbox.critical(self, "Error", "Not every item is hex digit, please check.")
                        return False
                    text_lst: list[str] = re.findall(".{2}", str_data)
                    int_lst: list[int] = [int(item, 16) for item in text_lst]
                    js_dict["datas"][i]["data"] = bytes(int_lst)
                self.js_send_list = [[js_dict["datas"][i]["select"], 1, 0, js_dict["datas"][i]["data"]]
                                     for i in range(len(js_dict["datas"]))]
            else:
                # self.js_send_list[[is_select, is_hexmode, is_sent, data]...]
                self.js_send_list = [[js_dict["datas"][i]["select"], 0, 0, js_dict["datas"][i]["data"]]
                                     for i in range(len(js_dict["datas"]))]
            if cycle_time > 0:
                self.fsend_timer.start(cycle_time)
            else:
                for item in self.js_send_list:
                    if item[0] == 1:  # selected
                        if item[1] == 1:  # hex mode
                            sendsize: int = self.ser_instance.write(item[3])
                        else:
                            sendsize: int = self.ser_instance.write(item[3].encode(self.encode_info, "ignore"))
                        self.total_sendsize += sendsize
                        self.update_rwsize_status(self.total_sendsize, self.total_recsize)
        else:
            # for txt file
            try:
                with open(sfile, mode='r', encoding=encode, newline='') as fp:
                    send_text: str = fp.read()
            except Exception as e:
                msgtext: str = "Error of opening file"
                self.log.error(f'{msgtext}, err: {e}')
                self.msgbox.critical(self, "Error", msgtext)
                return False
            if self.ser_instance.isOpen():
                sendsize: int = self.ser_instance.write(send_text.encode(self.encode_info, "ignore"))
                self.total_sendsize += sendsize
                self.update_rwsize_status(self.total_sendsize, self.total_recsize)

    def jsfile_data_send(self) -> None:
        """
        This function iterates through the json send list and sends the selected data
        through the serial instance. It updates the send status of each data item and
        the total send size. If all selected data items have been sent, it stops the 
        file send timer.

        Args:
            None

        Returns:
            None
        """
        for item in self.js_send_list:
            if item[0] == 1 and item[2] == 0:  # selected and not sent
                if item[1] == 1:  # hex mode
                    sendsize: int = self.ser_instance.write(item[3])
                else:
                    sendsize: int = self.ser_instance.write(item[3].encode(self.encode_info, "ignore"))
                item[2] = 1  # mark as sent
                self.total_sendsize += sendsize
                self.update_rwsize_status(self.total_sendsize, self.total_recsize)
                break
        if all(item[2] == 1 for item in self.js_send_list if item[0] == 1):
            self.fsend_timer.stop()

########################## receive function ############################

    def receive_set_hexmode(self) -> bool:
        """
        This function checks the state of the hex mode checkbox and converts
        the text in the receive text edit to the appropriate format. If the 
        text is empty, it unlocks the mutex and returns False.

        Args:
            None

        Returns:
            bool: False if the text is empty, otherwise performs the conversion.
        """
        self.mutex.lock()
        hexmode_state: bool = self.ui.checkBox_RHexmode.isChecked()
        text: str = self.ui.textEdit_Receive.toPlainText()
        if not text:
            self.mutex.unlock()
            return False
        if hexmode_state:
            str_text: str = text.encode(self.encode_info, "replace").hex(" ") + " "
        else:
            str_text: str = bytes.fromhex(text).decode(self.encode_info, "replace")
        self.ui.textEdit_Receive.clear()
        self.ui.textEdit_Receive.insertPlainText(str_text)
        self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
        self.mutex.unlock()
        return True

    def update_receive_ui(self) -> None:
        """
        This function updates the UI with received data from the queue. It 
        checks the hex mode status and formats the received data accordingly, 
        then updates the text edit and receive size status.

        Args:
            None

        Returns:
            None
        """
        self.mutex.lock()
        if not self.recthread.recqueue.empty():
            recdatas: bytes = self.recthread.recqueue.get_nowait()
            recsize: int = len(recdatas)
            hex_status: bool = self.ui.checkBox_RHexmode.isChecked()
            if hex_status:
                recdatas = recdatas.hex(" ")
            else:
                recdatas = recdatas.decode(self.encode_info, "replace")
            self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
            self.ui.textEdit_Receive.insertPlainText(recdatas)
            if hex_status:
                self.ui.textEdit_Receive.insertPlainText(" ")
            self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
            self.total_recsize += recsize
            self.update_rwsize_status(self.total_sendsize, self.total_recsize)
        self.mutex.unlock()

    def receive_save(self) -> bool:
        """
        This function opens a file dialog to save the received data into a
        text file. The file name and path are stored in the class variable
        `recdatas_file` and the text is written to the file using the UTF-8
        encoding.

        Args:
            None

        Returns:
            bool: True if the file is saved successfully, False otherwise
        """
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setNameFilter("TXT File(*.txt)")
        if not dialog.exec():
            return False
        self.recdatas_file = dialog.selectedFiles()[0]
        if not self.recdatas_file:
            self.log.info("No file be selected to save the received datas")
            return False
        self.log.info(f"file: {self.recdatas_file}")
        text: str = self.ui.textEdit_Receive.toPlainText()
        try:
            with open(self.recdatas_file, "w+", encoding="utf-8") as fp:
                fp.write(text)
        except Exception:
            self.log.error("Error of writing datas into file.")
            self.msgbox.critical(self, "Error", "Error of writing datas into file")
            return False

    def receive_clear(self) -> None:
        """
        This function clears the receive text edit and resets the total receive size
        to 0.

        Args:
            None

        Returns:
            None
        """
        self.ui.textEdit_Receive.clear()
        self.total_recsize = 0
        self.update_rwsize_status(self.total_sendsize, self.total_recsize)

    def update_rwsize_status(self, send_sz: int, rec_sz: int) -> None:
        """
        Update receive and send size status.

        Args:
            send_sz (int): The total send size.
            rec_sz (int): The total receive size.

        Returns:
            None

        """
        self.datasize_text = f"  Send: {send_sz}  |  Receive: {rec_sz}  "
        self.label_rwsize.setText(self.datasize_text)

########################## menu function ############################

    def action_open_file(self) -> bool:
        """
        This function checks if the receive data file exists and opens its
        directory. Displays an information message if the file does not exist.

        Args:
            None

        Returns:
            bool: False if the file does not exist, True otherwise
        """
        if not os.path.exists(self.recdatas_file):
            self.msgbox.information(self, "Info", "Please save a receive datas file first")
            return False
        if "nt" in os.name:
            os.startfile(os.path.dirname(self.recdatas_file))
        else:
            os.system(f'xdg-open {os.path.dirname(self.recdatas_file)}')
        return True

    def action_exit(self) -> None:
        """
        This function will stop the receive thread if it is running, and then
        exit the application.

        Args:
            None

        Returns:
            None
        """
        if self.recthread.isRunning():
            self.recthread.requestInterruption()
            self.recthread.quit()
            self.recthread.wait()
        sys.exit()

    def action_about(self):
        # self.msgbox.information(self, "About", gl.AboutInfo)
        self.about.show()

    def action_encoding_ascii(self):
        self.set_encoding("ascii")

    def action_encoding_utf8(self):
        self.set_encoding("utf-8")

    def action_encoding_utf16(self):
        self.set_encoding("utf-16")

    def action_encoding_utf32(self):
        self.set_encoding("utf-32")

    def action_encoding_gbk(self):
        self.set_encoding("gbk")

    def set_encoding(self, encode: str) -> None:
        """
        Set the encoding of the application.

        Parameters:
            encode (str): The encoding to set, can be "ascii", "utf-8", "utf-16", "utf-32", or "gbk"

        Returns:
            None
        """
        self.ui.actionASCII.setChecked(True if encode == "ascii" else False)
        self.ui.actionUTF_8.setChecked(True if encode == "utf-8" else False)
        self.ui.actionUTF_16.setChecked(True if encode == "utf-16" else False)
        self.ui.actionUTF_32.setChecked(True if encode == "utf-32" else False)
        self.ui.actionGBK_GB2312.setChecked(True if encode == "gbk" else False)
        self.encode_info = encode

    def closeEvent(self, event: QEvent) -> None:
        """
        Handle the close event of the MainWindow.

        Interrupts and stops the running receive thread 
        and performs cleanup before closing the window.

        Args:
            event (QEvent): The close event.

        Returns:
            None
        """
        if self.recthread.isRunning():
            self.recthread.requestInterruption()
            self.recthread.quit()
            self.recthread.wait()
        self.recthread.deleteLater()
        super(MainWindow, self).closeEvent(event)

########################## Sub-thread for receiving data ############################


class WorkThread(QThread):
    rec_signal: Signal = Signal()
    close_signal: Signal = Signal()

    def __init__(self, ser: serial.Serial, parent=None) -> None:
        """
        Initialize the work thread.

        Args:
            ser (serial.Serial): The serial port instance.
            parent (QObject, optional): The parent QObject. Defaults to None.
        """
        super(WorkThread, self).__init__(parent)
        self.ser: serial.Serial = ser
        self.port_close_flag: bool = False
        self.recqueue: queue.Queue[bytes] = queue.Queue(50)

    def run(self) -> None:
        """
        Run the work thread.

        Continuously read data from the serial port and put it into the
        receive queue. If the receive queue is not empty, emit a signal to
        notify the main window to update the receive text edit widget.

        If the port close flag is set to True, close the serial port and
        emit a signal to notify the main window that the port is closed.

        Args:
            None

        Returns:
            None
        """
        while True:
            if self.ser.isOpen():
                datas: bytes = self.ser.readall()
                if datas:
                    self.recqueue.put_nowait(datas)
            if self.isInterruptionRequested():
                break
            if not self.recqueue.empty():
                self.rec_signal.emit()
            if self.port_close_flag:
                self.ser.close()
                self.port_close_flag = False
                self.close_signal.emit()
            time.sleep(0.01)


def main() -> int:
    """
    Entry point of the application.

    Create a QApplication object, a MainWindow object, show the main window, and
    run the event loop.

    Args:
        None

    Returns:
        int: The exit code of the application.
    """
    app: QApplication = QApplication(sys.argv)  # create a QApplication object
    window: MainWindow = MainWindow()  # create a MainWindow object
    window.show()  # show the main window
    return app.exec()  # run the event loop and exit with the app's exit code


if __name__ == "__main__":
    main()
