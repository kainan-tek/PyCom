import os
import re
import string
import sys
import time
import queue
import serial
import serial.tools.list_ports
import logwrapper as log
import globalvar as gl
import resrc.resource as res
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QLabel
from PySide6.QtGui import QIcon, QPixmap, QTextCursor, Qt, QIntValidator
from PySide6.QtCore import QThread, QTimer, Signal, QMutex, QEvent
from ui.ui_mainwindow import Ui_MainWindow
from about import About


class MainWindow(QMainWindow):
    def __init__(self, log):
        super(MainWindow, self).__init__()
        self.log = log
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.about = About()
        self.var_init()
        self.gui_init()
        self.parse_ports()

    def var_init(self):
        self.total_sendsize = 0
        self.total_recsize = 0
        self.datasize_text = ""
        self.recdatas_file = ""
        self.mutex = QMutex()
        self.msgbox = QMessageBox()
        self.dialog = QFileDialog()
        self.ser_instance = serial.Serial()
        self.send_timer = QTimer()
        self.send_timer.timeout.connect(self.single_data_send)

        self.recthread = WorkThread(self.ser_instance)
        self.recthread.rec_signal.connect(self.update_receive_ui)
        self.recthread.close_signal.connect(self.post_close_port)
        self.recthread.start()

        self.key_limits = [Qt.Key_0, Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5, Qt.Key_6, Qt.Key_7, Qt.Key_8,
                           Qt.Key_9, Qt.Key_A, Qt.Key_B, Qt.Key_C, Qt.Key_D, Qt.Key_E, Qt.Key_F, Qt.Key_Space,
                           Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Right, Qt.Key_Left, Qt.Key_Up, Qt.Key_Down,
                           Qt.Key_Control, Qt.Key_Shift, Qt.Key_Copy, Qt.Key_Paste]

    def gui_init(self):
        self.setWindowTitle(f'{gl.GuiInfo["proj"]} {gl.GuiInfo["version"]}')
        self.setWindowIcon(QIcon(QPixmap(":/icon/pycom")))

        self.ui.textEdit_SSend.setStyleSheet(u"background-color: rgb(199, 237, 204);")
        self.ui.textEdit_Receive.setStyleSheet(u"background-color: rgb(199, 237, 204);")
        self.ui.textEdit_SSend.installEventFilter(self)
        self.ui.lineEdit_Cycle.setValidator(QIntValidator())

        self.ui.comboBox_BRate.addItems(gl.SerialInfo["baudrate"])
        self.ui.comboBox_BRate.setCurrentText('115200')
        self.ui.comboBox_BSize.addItems(gl.SerialInfo["bytesize"])
        self.ui.comboBox_BSize.setCurrentText('8')
        self.ui.comboBox_SBit.addItems(gl.SerialInfo["stopbit"])
        self.ui.comboBox_SBit.setCurrentText('1')
        self.ui.comboBox_PBit.addItems(gl.SerialInfo["paritybit"])
        self.ui.comboBox_PBit.setCurrentText('None')

        self.ui.pushButton_Check.clicked.connect(self.parse_ports)
        self.ui.pushButton_Open.clicked.connect(self.open_port)
        self.ui.pushButton_Close.clicked.connect(self.close_port)

        self.ui.pushButton_Send.clicked.connect(self.single_data_send)
        self.ui.pushButton_SClear.clicked.connect(self.send_clear)
        self.ui.pushButton_RClear.clicked.connect(self.receive_clear)
        self.ui.pushButton_RSave.clicked.connect(self.receive_save)
        self.ui.checkBox_SHexmode.clicked.connect(self.send_set_format)
        self.ui.checkBox_RHexmode.clicked.connect(self.receive_set_format)
        self.ui.checkBox_Cycle.clicked.connect(self.send_set_cyclemode)

        self.ui.actionOpen_File.triggered.connect(self.action_open_file)
        self.ui.actionExit.triggered.connect(self.action_exit)
        self.ui.actionAbout.triggered.connect(self.action_about)

        self.datasize_text = "  Send: 0  |  Receive: 0  "
        self.label_datasize = QLabel(self.datasize_text)
        self.label_datasize.setStyleSheet("color:blue")
        self.ui.statusbar.addPermanentWidget(self.label_datasize, stretch=0)
        self.ui.pushButton_Open.setEnabled(True)
        self.ui.pushButton_Close.setEnabled(False)

    def parse_ports(self):
        if self.ser_instance.isOpen():
            self.msgbox.information(self, "Info", "Please close port first")
            return False
        self.ui.comboBox_SPort.clear()
        port_list = list(serial.tools.list_ports.comports())
        ports_list = [port[0] for port in port_list]
        self.ui.comboBox_SPort.addItems(ports_list)

    def open_port(self):
        self.ser_instance.port = self.ui.comboBox_SPort.currentText().strip()
        self.ser_instance.baudrate = int(self.ui.comboBox_BRate.currentText().strip())
        self.ser_instance.bytesize = int(self.ui.comboBox_BSize.currentText().strip())
        self.ser_instance.stopbits = int(self.ui.comboBox_SBit.currentText().strip())
        self.ser_instance.parity = self.ui.comboBox_PBit.currentText().strip()[0]
        self.ser_instance.timeout = gl.SerialInfo["timeout"]

        if not self.ser_instance.port:
            self.log.info("No port be selected")
            self.msgbox.information(self, "Info", "No port be selected")
            return False

        if not self.ser_instance.isOpen():
            try:
                self.ser_instance.open()
            except Exception as err:
                self.log.error(f"Error: {str(err)}")
                if "PermissionError" in str(err):
                    self.msgbox.critical(self, "PermissionError", "The selected port may be occupied!")
                else:
                    self.msgbox.critical(self, "Error", "Can not open the port with these params")
                return False
        if self.ser_instance.isOpen():
            self.ui.pushButton_Open.setEnabled(False)
            self.ui.pushButton_Close.setEnabled(True)

    def close_port(self):
        if self.ser_instance.isOpen():
            if self.ui.checkBox_Cycle.isChecked():
                self.ui.checkBox_Cycle.click()
            self.recthread.close_flag = True  # triger the serial close function in receive thread
            # self.ser_instance.close()  # the serial readall function in receive thread may crash

    def post_close_port(self):
        if not self.ser_instance.isOpen():
            self.ui.pushButton_Open.setEnabled(True)
            self.ui.pushButton_Close.setEnabled(False)

    def single_data_send(self):
        newline_state = self.ui.checkBox_Newline.isChecked()
        text = self.ui.textEdit_SSend.toPlainText()
        if not text:
            return False
        if not self.ser_instance.isOpen():
            self.msgbox.information(self, "Info", "Please open a serial port first")
            return False
        if self.ui.checkBox_SHexmode.isChecked():
            if not self.is_send_hex_mode(text):
                if self.ui.checkBox_Cycle.isChecked():
                    self.ui.checkBox_Cycle.click()
                self.msgbox.warning(self, "Warning", "Not correct hex format")
                return False
            text_list = re.findall(".{2}", text.replace(" ", ""))
            str_text = " ".join(text_list)
            if not str_text == text:
                self.ui.textEdit_SSend.clear()
                self.ui.textEdit_SSend.insertPlainText(str_text)
            int_list = [int(item, 16) for item in text_list]
            if newline_state:
                int_list.extend([13, 10])
            bytes_text = bytes(int_list)
        else:
            if newline_state:
                text = text+'\r\n'
            bytes_text = text.encode("gbk", "replace")

        sendsize = self.ser_instance.write(bytes_text)
        self.total_sendsize = self.total_sendsize+sendsize
        self.datasize_text = f"  Send: {self.total_sendsize}  |  Receive: {self.total_recsize}  "
        self.label_datasize.setText(self.datasize_text)

    def send_clear(self):
        self.ui.textEdit_SSend.clear()
        self.total_sendsize = 0
        self.datasize_text = f"  Send: 0  |  Receive: {self.total_recsize}  "
        self.label_datasize.setText(self.datasize_text)

    def receive_clear(self):
        self.ui.textEdit_Receive.clear()
        self.total_recsize = 0
        self.datasize_text = f"  Send: {self.total_sendsize}  |  Receive: 0  "
        self.label_datasize.setText(self.datasize_text)

    def send_set_cyclemode(self):
        if self.ui.checkBox_Cycle.isChecked():
            cycle_text = self.ui.lineEdit_Cycle.text()
            send_text = self.ui.textEdit_SSend.toPlainText()
            msg = ""
            if not self.ser_instance.isOpen():
                msg = "Please open a port first"
            if not cycle_text:
                msg = "Please set cycle time first"
            if not send_text:
                msg = "Please fill send datas first"
            if msg:
                self.log.info(f"Info: {msg}")
                self.msgbox.information(self, "Info", msg)
                self.ui.checkBox_Cycle.setChecked(False)
                return False
            self.send_timer.start(int(cycle_text.strip()))
            self.ui.lineEdit_Cycle.setEnabled(False)
        else:
            self.send_timer.stop()
            self.ui.lineEdit_Cycle.setEnabled(True)

    def send_set_format(self):
        hexmode_state = self.ui.checkBox_SHexmode.isChecked()
        text = self.ui.textEdit_SSend.toPlainText()
        if not text:
            return False
        if hexmode_state:
            str_text = text.encode("gbk", "replace").hex(" ")
        else:
            if not self.is_send_hex_mode(text):
                self.msgbox.warning(self, "Warning", "Not correct hex format")
                self.ui.checkBox_SHexmode.setChecked(True)
                return False
            str_text = bytes.fromhex(text.replace(" ", "")).decode("gbk", "replace")
        self.ui.textEdit_SSend.clear()
        self.ui.textEdit_SSend.insertPlainText(str_text)

    def is_send_hex_mode(self, text):
        post_text = text.replace(" ", "")
        if not len(post_text) % 2 == 0:
            return False
        if not all(item in string.hexdigits for item in post_text):
            return False
        return True

    def receive_set_format(self):
        self.mutex.lock()
        hexmode_state = self.ui.checkBox_RHexmode.isChecked()
        text = self.ui.textEdit_Receive.toPlainText()
        if not text:
            self.mutex.unlock()
            return False
        if hexmode_state:
            str_text = text.encode("gbk", "replace").hex(" ")+" "
        else:
            str_text = bytes.fromhex(text).decode("gbk", "replace")
        self.ui.textEdit_Receive.clear()
        self.ui.textEdit_Receive.insertPlainText(str_text)
        self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
        self.mutex.unlock()

    def update_receive_ui(self):
        self.mutex.lock()
        if not self.recthread.recqueue.empty():
            recdatas = self.recthread.recqueue.get_nowait()
            recsize = len(recdatas)
            hex_status = self.ui.checkBox_RHexmode.isChecked()
            if hex_status:
                recdatas = recdatas.hex(" ")
            else:
                recdatas = recdatas.decode("gbk", "replace")
            self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
            self.ui.textEdit_Receive.insertPlainText(recdatas)
            if hex_status:
                self.ui.textEdit_Receive.insertPlainText(" ")
            self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
            self.total_recsize = self.total_recsize+recsize
            self.datasize_text = f"  Send: {self.total_sendsize}  |  Receive: {self.total_recsize}  "
            self.label_datasize.setText(self.datasize_text)
        self.mutex.unlock()

    def receive_save(self):
        self.dialog.setFileMode(QFileDialog.ExistingFile)
        self.dialog.setNameFilter("TXT File(*.txt)")
        self.dialog.setViewMode(QFileDialog.Detail)
        if not self.dialog.exec():
            return False
        self.recdatas_file = self.dialog.selectedFiles()[0]
        if not self.recdatas_file:
            self.log.info("No file be selected to save the received datas")
            return False
        self.log.info(f"file: {self.recdatas_file}")
        text = self.ui.textEdit_Receive.toPlainText()
        try:
            with open(self.recdatas_file, "w+", encoding="utf-8") as fp:
                fp.write(text)
        except Exception:
            self.log.error("Error of writing datas into file.")
            self.msgbox.critical(self, "Error", "Error of writing datas into file")
            return False

    def action_open_file(self):
        if not os.path.exists(self.recdatas_file):
            self.msgbox.information(self, "Info", "Please save a receive datas file first")
            return False
        dir_name = os.path.dirname(self.recdatas_file)
        if "nt" in os.name:
            os.startfile(dir_name)
        else:
            os.system(f'xdg-open {dir_name}')

    def action_exit(self):
        if self.recthread.isRunning():
            self.recthread.run_flag = False
            self.recthread.quit()
        sys.exit()

    def action_about(self):
        # self.msgbox.information(self, "About", gl.AboutInfo)
        self.about.show()

    def closeEvent(self, event):
        if self.recthread.isRunning():
            self.recthread.run_flag = False
            self.recthread.quit()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and obj is self.ui.textEdit_SSend and self.ui.checkBox_SHexmode.isChecked():
            if not event.key() in self.key_limits and not (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V):
                self.msgbox.warning(self, "Warning", "Hex mode now!\nPlease input 0-9, a-f, A-F")
                return True
        return False  # super().eventFilter(obj, event)


class WorkThread(QThread):
    rec_signal = Signal()
    close_signal = Signal()

    def __init__(self, ser, parent=None):
        super(WorkThread, self).__init__(parent)
        self.run_flag = True
        self.ser = ser
        self.close_flag = False
        self.recqueue = queue.Queue(50)

    def run(self):
        while self.run_flag:
            if self.ser.isOpen():
                datas = self.ser.readall()
                if datas:
                    self.recqueue.put_nowait(datas)
            if not self.recqueue.empty():
                self.rec_signal.emit()
            if self.close_flag:
                self.ser.close()
                self.close_flag = False
                self.close_signal.emit()
            time.sleep(0.01)


if __name__ == "__main__":
    logwrap = log.Log()
    app = QApplication(sys.argv)
    window = MainWindow(logwrap)
    window.show()
    sys.exit(app.exec())
