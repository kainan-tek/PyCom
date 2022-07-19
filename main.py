import sys
import time
import queue
import serial
import serial.tools.list_ports
import logwrapper as log
import globalvar as gl
import resrc.resource as res
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtGui import QIcon, QPixmap, QTextCursor
from PySide6.QtCore import QThread, Signal, QMutex
from ui.ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self, log):
        super(MainWindow, self).__init__()
        self.log = log
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.var_init()
        self.gui_init()
        self.parse_ports()

    def var_init(self):
        self.total_sendsize = 0
        self.total_recsize = 0
        self.mutex = QMutex()
        self.msgbox = QMessageBox()
        self.dialog = QFileDialog()
        self.ser_instance = serial.Serial()

        self.recthread = WorkThread(self.ser_instance)
        self.recthread.rec_signal.connect(self.update_receive_ui)
        self.recthread.close_signal.connect(self.post_close_port)
        self.recthread.start()

    def gui_init(self):
        self.setWindowTitle(f'{gl.GuiInfo["proj"]} {gl.GuiInfo["version"]}')
        self.setWindowIcon(QIcon(QPixmap(":/icon/pycom")))

        self.ui.textEdit_SSend.setStyleSheet(u"background-color: rgb(199, 237, 204);")
        self.ui.textEdit_Receive.setStyleSheet(u"background-color: rgb(199, 237, 204);")

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
        self.ui.checkBox_SHexmode.clicked.connect(self.send_set_hexmode)
        self.ui.checkBox_RHexmode.clicked.connect(self.receive_set_hexmode)

        self.ui.actionAbout.triggered.connect(self.action_about)

        self.ui.pushButton_Open.setEnabled(True)
        self.ui.pushButton_Close.setEnabled(False)

    def parse_ports(self):
        if self.ser_instance.isOpen():
            self.msgbox.information(self, 'Info', 'Please close port first')
            return False
        self.ui.comboBox_SPort.clear()
        port_list = list(serial.tools.list_ports.comports())
        ports_list = [port[0] for port in port_list]
        self.ui.comboBox_SPort.addItems(ports_list)

    def open_port(self):
        self.ser_instance.port = self.ui.comboBox_SPort.currentText().strip()
        self.ser_instance.baudrate = int(self.ui.comboBox_BRate.currentText().strip())
        self.ser_instance.bytesize = int(self.ui.comboBox_BSize.currentText().strip())
        self.ser_instance.parity = self.ui.comboBox_PBit.currentText().strip()[0]
        self.ser_instance.timeout = gl.SerialInfo["timeout"]
        if len(self.ui.comboBox_SBit.currentText()) > 1:
            self.ser_instance.stopbits = float(self.ui.comboBox_SBit.currentText().strip())
        else:
            self.ser_instance.stopbits = int(self.ui.comboBox_SBit.currentText().strip())

        if not self.ser_instance.port:
            self.log.info("No port be selected")
            self.msgbox.information(self, 'Info', 'No port be selected')
            return False

        if not self.ser_instance.isOpen():
            try:
                self.ser_instance.open()
            except Exception as err:
                self.log.error(f"Error: {str(err)}")
                if "PermissionError" in str(err):
                    self.msgbox.critical(self, 'PermissionError', 'The selected port may be occupied!')
                else:
                    self.msgbox.critical(self, 'Error', 'Can not open the port with these params')
                return False
        if self.ser_instance.isOpen():
            self.ui.pushButton_Open.setEnabled(False)
            self.ui.pushButton_Close.setEnabled(True)

    def close_port(self):
        if self.ser_instance.isOpen():
            self.recthread.close_flag = True  # triger the close function in receive thread
            # self.ser_instance.close()  # the readall function in receive thread may crash

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
            self.msgbox.information(self, 'Info', 'Please open a serial port first')
            return False
        if self.ui.checkBox_SHexmode.isChecked():
            if not self.is_hex_mode(text):
                self.msgbox.warning(self, 'Warning', 'not correct hex format')
                return False
            text_list = text.strip().split(" ")
            int_list = [int(item, 16) for item in text_list]
            if newline_state:
                int_list.extend([13, 10])  # add \r\n
            text = bytes(int_list)
        else:
            if newline_state:
                text = (text+'\r\n').encode("gb2312")
            else:
                text = text.encode("gb2312")

        sendsize = self.ser_instance.write(text)
        self.total_sendsize = self.total_sendsize+sendsize
        self.ui.label_Sendsize.setText(f"S: {self.total_sendsize}")

    def send_clear(self):
        self.ui.textEdit_SSend.clear()
        self.total_sendsize = 0
        self.ui.label_Sendsize.setText(f"S: {self.total_sendsize}")

    def receive_clear(self):
        self.ui.textEdit_Receive.clear()
        self.total_recsize = 0
        self.ui.label_Recsize.setText(f"R: {self.total_recsize}")

    def send_set_hexmode(self):
        hexmode_state = self.ui.checkBox_SHexmode.isChecked()
        text = self.ui.textEdit_SSend.toPlainText()
        if hexmode_state:
            if not self.is_hex_mode(text):
                text = text.encode("gb2312").hex(" ")
                self.ui.textEdit_SSend.clear()
                self.ui.textEdit_SSend.insertPlainText(text)
        else:
            if self.is_hex_mode(text):
                text = text.replace(" ", "")
                bytes_text = bytes.fromhex(text)
                self.ui.textEdit_SSend.clear()
                self.ui.textEdit_SSend.insertPlainText(bytes_text.decode("gb2312"))

    def receive_set_hexmode(self):
        self.mutex.lock()
        hexmode_state = self.ui.checkBox_RHexmode.isChecked()
        text = self.ui.textEdit_Receive.toPlainText()
        if hexmode_state:
            if not self.is_hex_mode(text):
                text = text.encode("gb2312").hex(" ")
                self.ui.textEdit_Receive.clear()
                self.ui.textEdit_Receive.insertPlainText(text)
                self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
        else:
            if self.is_hex_mode(text):
                text = text.replace(" ", "")
                bytes_text = bytes.fromhex(text)
                self.ui.textEdit_Receive.clear()
                self.ui.textEdit_Receive.insertPlainText(bytes_text.decode("gb2312"))
                self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
        self.mutex.unlock()

    def is_hex_mode(self, text):
        is_hex_flag = True
        text_list = text.strip().split(" ")
        for item in text_list:
            if len(item) > 2:
                if len(item) == 4 and (item.startswith("0x") or item.startswith("0X")):
                    continue
                is_hex_flag = False
                break
        if is_hex_flag:
            for item in text_list:
                try:
                    if int(item, 16) > 255:
                        is_hex_flag = False
                        break
                except ValueError:
                    is_hex_flag = False
                    break
        return is_hex_flag

    def update_receive_ui(self):
        self.mutex.lock()
        if not self.recthread.recqueue.empty():
            recdatas = self.recthread.recqueue.get_nowait()
            recsize = len(recdatas)
            if self.ui.checkBox_RHexmode.isChecked():
                recdatas = recdatas.hex(" ")
                self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
                self.ui.textEdit_Receive.insertPlainText(' ')
            else:
                recdatas = recdatas.decode('gb2312', "ignore")
            self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
            self.ui.textEdit_Receive.insertPlainText(recdatas)
            self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
            self.total_recsize = self.total_recsize+recsize
            self.ui.label_Recsize.setText(f"R: {self.total_recsize}")
        self.mutex.unlock()

    def receive_save(self):
        self.dialog.setFileMode(QFileDialog.ExistingFile)
        self.dialog.setNameFilter("TXT File(*.txt)")
        self.dialog.setViewMode(QFileDialog.Detail)
        if not self.dialog.exec():
            return False
        recdatas_file = self.dialog.selectedFiles()[0]
        if not recdatas_file:
            self.log.info("No file be selected to save the received datas")
            return False
        self.log.info(f"file: {recdatas_file}")
        text = self.ui.textEdit_Receive.toPlainText()
        try:
            with open(recdatas_file, 'w+', encoding="utf-8") as fp:
                fp.write(text)
        except Exception as err:
            print(f"error of writing datas into file.")
            return False

    def action_about(self):
        self.msgbox.information(self, "About", gl.AboutInfo)

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

    def __del__(self):
        self.run_flag = False
        self.wait()

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
