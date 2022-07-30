import os
import re
import sys
import time
import queue
import string
import chardet
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
        self.encode_info = "gbk"
        self.multi_dict = {}
        self.mutex = QMutex()
        self.msgbox = QMessageBox()
        self.dialog = QFileDialog()
        self.ser_instance = serial.Serial()
        self.send_timer = QTimer()
        self.send_timer.timeout.connect(self.data_send)

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
        self.ui.textEdit_sSend.setStyleSheet(u"background-color: rgb(199, 237, 204);")
        self.ui.textEdit_Receive.setStyleSheet(u"background-color: rgb(199, 237, 204);")

        # menu set up
        self.ui.actionOpen_File.triggered.connect(self.action_open_file)
        self.ui.actionExit.triggered.connect(self.action_exit)
        self.ui.actionUTF_8.triggered.connect(self.action_utf_8)
        self.ui.actionGBK.triggered.connect(self.action_gbk)
        self.ui.actionAbout.triggered.connect(self.action_about)

        # serial port set up
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
        self.ui.pushButton_Open.setEnabled(True)
        self.ui.pushButton_Close.setEnabled(False)

        # single send set up
        self.ui.pushButton_sSend.clicked.connect(self.single_data_send)
        self.ui.pushButton_sClear.clicked.connect(self.send_clear)
        self.ui.pushButton_RClear.clicked.connect(self.receive_clear)
        self.ui.pushButton_RSave.clicked.connect(self.receive_save)
        self.ui.checkBox_sHexmode.clicked.connect(self.send_set_hexmode)
        self.ui.checkBox_RHexmode.clicked.connect(self.receive_set_hexmode)
        self.ui.checkBox_sCycle.clicked.connect(self.send_set_cyclemode)
        self.ui.textEdit_sSend.installEventFilter(self)
        self.ui.lineEdit_sCycle.setValidator(QIntValidator())

        # multi-send set up
        self.ui.pushButton_m1.clicked.connect(self.multi_send_m1)
        self.ui.pushButton_m2.clicked.connect(self.multi_send_m2)
        self.ui.pushButton_m3.clicked.connect(self.multi_send_m3)
        self.ui.pushButton_m4.clicked.connect(self.multi_send_m4)
        self.ui.pushButton_m5.clicked.connect(self.multi_send_m5)
        self.ui.pushButton_m6.clicked.connect(self.multi_send_m6)
        self.ui.checkBox_mCycle.clicked.connect(self.multi_send_set_cyclemode)
        self.ui.lineEdit_mCycle.setValidator(QIntValidator())

        # file send set up
        self.ui.pushButton_fSelect.clicked.connect(self.file_send_select)
        self.ui.pushButton_fSend.clicked.connect(self.file_send)

        # statusbar set up
        self.datasize_text = "  Send: 0  |  Receive: 0  "
        self.label_datasize = QLabel(self.datasize_text)
        self.label_datasize.setStyleSheet("color:blue")
        self.ui.statusbar.addPermanentWidget(self.label_datasize, stretch=0)

########################## port function ############################

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
        if self.ui.checkBox_sCycle.isChecked():
            self.ui.checkBox_sCycle.click()
        if self.ui.checkBox_mCycle.isChecked():
            self.ui.checkBox_mCycle.click()
        if self.ser_instance.isOpen():
            self.recthread.close_flag = True  # triger the serial close function in receive thread
            # self.ser_instance.close()  # the serial readall function in receive thread may crash

    def post_close_port(self):
        if not self.ser_instance.isOpen():
            self.ui.pushButton_Open.setEnabled(True)
            self.ui.pushButton_Close.setEnabled(False)

########################## single and multi send function ############################

    def data_send(self):
        if self.ui.checkBox_sCycle.isChecked() and self.ui.checkBox_mCycle.isChecked():
            self.ui.checkBox_sCycle.click()
            self.ui.checkBox_mCycle.click()
            self.msgbox.warning(
                self, "Warning", "Both single cycle send and multi cycle send are activated\nDeactivate them all, please try again")
            return False
        if self.ui.checkBox_sCycle.isChecked():
            self.single_data_send()
        elif self.ui.checkBox_mCycle.isChecked():
            self.multi_cycle_send()

    def is_send_hex_mode(self, text):
        post_text = text.replace(" ", "")
        if not len(post_text) % 2 == 0:
            return False
        if not all(item in string.hexdigits for item in post_text):
            return False
        return True

########################## single send function ############################

    def send_clear(self):
        self.ui.textEdit_sSend.clear()
        self.total_sendsize = 0
        self.datasize_text = f"  Send: 0  |  Receive: {self.total_recsize}  "
        self.label_datasize.setText(self.datasize_text)

    def single_data_send(self):
        int_list = []
        newline_state = self.ui.checkBox_sNewline.isChecked()
        text = self.ui.textEdit_sSend.toPlainText()

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
                    self.msgbox.warning(self, "Warning", "Not correct hex format")
                    return False
                text_list = re.findall(".{2}", text.replace(" ", ""))
                str_text = " ".join(text_list)
                if not str_text == text:
                    self.ui.textEdit_sSend.clear()
                    self.ui.textEdit_sSend.insertPlainText(str_text)
                int_list = [int(item, 16) for item in text_list]
            if newline_state:
                int_list.extend([13, 10])
            bytes_text = bytes(int_list)
        else:
            if newline_state:
                text = text+'\r\n'
            bytes_text = text.encode(self.encode_info, "replace")

        sendsize = self.ser_instance.write(bytes_text)
        self.total_sendsize = self.total_sendsize+sendsize
        self.datasize_text = f"  Send: {self.total_sendsize}  |  Receive: {self.total_recsize}  "
        self.label_datasize.setText(self.datasize_text)

    def send_set_cyclemode(self):
        if self.ui.checkBox_sCycle.isChecked():
            msg = ""
            cycle_text = self.ui.lineEdit_sCycle.text()
            send_text = self.ui.textEdit_sSend.toPlainText()
            if not self.ser_instance.isOpen():
                msg = "Please open a port first"
            if not cycle_text:
                msg = "Please set cycle time first"
            if not send_text:
                msg = "Please fill send datas first"
            if msg:
                self.log.info(f"Info: {msg}")
                self.msgbox.information(self, "Info", msg)
                self.ui.checkBox_sCycle.setChecked(False)
                return False
            self.send_timer.start(int(cycle_text.strip()))
            self.ui.lineEdit_sCycle.setEnabled(False)
        else:
            self.send_timer.stop()
            self.ui.lineEdit_sCycle.setEnabled(True)

    def send_set_hexmode(self):
        hexmode_state = self.ui.checkBox_sHexmode.isChecked()
        text = self.ui.textEdit_sSend.toPlainText()
        if not text:
            return False
        if hexmode_state:
            str_text = text.encode(self.encode_info, "replace").hex(" ")
        else:
            if not self.is_send_hex_mode(text):
                self.msgbox.warning(self, "Warning", "Not correct hex format")
                self.ui.checkBox_sHexmode.setChecked(True)
                return False
            str_text = bytes.fromhex(text.replace(" ", "")).decode(self.encode_info, "replace")
        self.ui.textEdit_sSend.clear()
        self.ui.textEdit_sSend.insertPlainText(str_text)

    def eventFilter(self, obj, event):
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

    def mx_common_send(self, seq, line_edit):
        int_list = []
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
                text_list = re.findall(".{2}", text.replace(" ", ""))
                str_text = " ".join(text_list)
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

        sendsize = self.ser_instance.write(bytes_text)
        self.total_sendsize = self.total_sendsize+sendsize
        self.datasize_text = f"  Send: {self.total_sendsize}  |  Receive: {self.total_recsize}  "
        self.label_datasize.setText(self.datasize_text)

    def multi_cycle_send(self):
        if self.ui.checkBox_m1.isChecked():
            self.multi_dict["m1"][0] = 1
            if not self.ui.lineEdit_m1.text() and not self.ui.checkBox_mNewLine.isChecked():
                self.multi_dict["m1"][0] = 0
        if self.ui.checkBox_m2.isChecked():
            self.multi_dict["m2"][0] = 1
            if not self.ui.lineEdit_m2.text() and not self.ui.checkBox_mNewLine.isChecked():
                self.multi_dict["m2"][0] = 0
        if self.ui.checkBox_m3.isChecked():
            self.multi_dict["m3"][0] = 1
            if not self.ui.lineEdit_m3.text() and not self.ui.checkBox_mNewLine.isChecked():
                self.multi_dict["m3"][0] = 0
        if self.ui.checkBox_m4.isChecked():
            self.multi_dict["m4"][0] = 1
            if not self.ui.lineEdit_m4.text() and not self.ui.checkBox_mNewLine.isChecked():
                self.multi_dict["m4"][0] = 0
        if self.ui.checkBox_m5.isChecked():
            self.multi_dict["m5"][0] = 1
            if not self.ui.lineEdit_m5.text() and not self.ui.checkBox_mNewLine.isChecked():
                self.multi_dict["m5"][0] = 0
        if self.ui.checkBox_m6.isChecked():
            self.multi_dict["m6"][0] = 1
            if not self.ui.lineEdit_m6.text() and not self.ui.checkBox_mNewLine.isChecked():
                self.multi_dict["m6"][0] = 0

        for item in self.multi_dict:
            if self.multi_dict[item][0] == 1 and self.multi_dict[item][1] == 0:
                if item == "m1":
                    self.multi_send_m1()
                elif item == "m2":
                    self.multi_send_m2()
                elif item == "m3":
                    self.multi_send_m3()
                elif item == "m4":
                    self.multi_send_m4()
                elif item == "m5":
                    self.multi_send_m5()
                elif item == "m6":
                    self.multi_send_m6()
                self.multi_dict[item][1] = 1
                break

        if all(self.multi_dict[item][1] for item in self.multi_dict if self.multi_dict[item][0]):
            for item in self.multi_dict:
                self.multi_dict[item][1] = 0

    def multi_send_set_cyclemode(self):
        if self.ui.checkBox_mCycle.isChecked():
            msg = ""
            cycle_text = self.ui.lineEdit_mCycle.text()
            if not self.ser_instance.isOpen():
                msg = "Please open a port first"
            if not cycle_text:
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

########################## receive function ############################

    def receive_set_hexmode(self):
        self.mutex.lock()
        hexmode_state = self.ui.checkBox_RHexmode.isChecked()
        text = self.ui.textEdit_Receive.toPlainText()
        if not text:
            self.mutex.unlock()
            return False
        if hexmode_state:
            str_text = text.encode(self.encode_info, "replace").hex(" ")+" "
        else:
            str_text = bytes.fromhex(text).decode(self.encode_info, "replace")
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
                recdatas = recdatas.decode(self.encode_info, "replace")
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

    def receive_clear(self):
        self.ui.textEdit_Receive.clear()
        self.total_recsize = 0
        self.datasize_text = f"  Send: {self.total_sendsize}  |  Receive: 0  "
        self.label_datasize.setText(self.datasize_text)

########################## file send function ############################

    def file_send_select(self):
        self.dialog.setFileMode(QFileDialog.AnyFile)
        self.dialog.setViewMode(QFileDialog.Detail)
        if not self.dialog.exec():
            return False
        file_name = self.dialog.selectedFiles()[0]
        if not file_name:
            return False
        self.log.info(f"send file: {file_name}")
        self.ui.lineEdit_fFile.setText(file_name)

    def predict_encoding(self, file):
        with open(file, 'rb') as f:
            encodeinfo = chardet.detect(f.read())
        # print(encodeinfo['encoding'])
        return encodeinfo['encoding']

    def file_send(self):
        sfile = self.ui.lineEdit_fFile.text()
        if not sfile or not os.path.exists(sfile):
            self.msgbox.information(self, "Info", "the file is not existed")
            return False

        encode = self.predict_encoding(sfile)
        try:
            with open(sfile, mode='r', encoding=encode) as fp:
                send_text = fp.read()
        except Exception as e:
            msgtext = "Error of opening file"
            self.log.error(f'{msgtext}: {e}')
            self.msgbox.critical(self, "Error", msgtext)
            return False
        if self.ser_instance.isOpen():
            self.ser_instance.write(send_text.encode(self.encode_info, "ignore"))

########################## menu function ############################

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

    def action_utf_8(self):
        self.ui.actionUTF_8.setChecked(True)
        self.ui.actionGBK.setChecked(False)
        self.encode_info = "utf-8"

    def action_gbk(self):
        self.ui.actionUTF_8.setChecked(False)
        self.ui.actionGBK.setChecked(True)
        self.encode_info = "gbk"

    def closeEvent(self, event):
        if self.recthread.isRunning():
            self.recthread.run_flag = False
            self.recthread.quit()


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
