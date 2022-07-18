import sys
import time
import queue
import serial
import serial.tools.list_ports
import logwrapper as log
import globalvar as gl
import resrc.resource as res
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QTextCursor
from PySide6.QtCore import Signal, QThread
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
        self.msgbox = QMessageBox()
        self.ser_instance = serial.Serial()

        self.workthread = WorkThread(self.ser_instance)
        self.workthread.rec_signal.connect(self.update_receive_ui)
        self.workthread.close_signal.connect(self.post_close_port)
        self.workthread.start()

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
        self.ui.checkBox_SHexmode.clicked.connect(self.send_hexmode)
        self.ui.pushButton_RClear.clicked.connect(self.receive_clear)
        self.ui.checkBox_RHexmode.clicked.connect(self.receive_hexmode)

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
            self.workthread.close_flag = True
            # self.ser_instance.close()

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

    def send_hexmode(self):
        hexmode_state = self.ui.checkBox_SHexmode.isChecked()
        if hexmode_state:
            print("to be done")

    def receive_hexmode(self):
        hexmode_state = self.ui.checkBox_RHexmode.isChecked()
        if hexmode_state:
            print("to be done")

    def update_receive_ui(self):
        if not self.workthread.recqueue.empty():
            recdatas = self.workthread.recqueue.get_nowait()
            self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
            self.ui.textEdit_Receive.insertPlainText(recdatas.decode('gb2312', "ignore"))
            self.ui.textEdit_Receive.moveCursor(QTextCursor.End)
            self.total_recsize = self.total_recsize+len(recdatas)
            self.ui.label_Recsize.setText(f"R: {self.total_recsize}")

    def action_about(self):
        self.msgbox.information(self, "About", gl.AboutInfo)

    def closeEvent(self, event):
        if self.workthread.isRunning():
            self.workthread.run_flag = False
            self.workthread.quit()


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
