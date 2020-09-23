# encoding: utf-8
"""
@version: 1.0
@author: Jarrrett
@file: app_run.py
@time: 2020/3/27 16:41
"""
import sys, os, shutil, time
import multiprocessing #引入多进程模组，该模组用于对多个图进行并行运算

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QAction, QFileDialog, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QBasicTimer
from get_can_file.run import func

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("init/window.ui", self)
        self.setFixedSize(self.width(), self.height());
        self.setWindowIcon(QIcon('init/cloud.ico'))
        self.setWindowTitle('CAN数据解析__HIRAIN TECH.')

        self.setWindowFlags(Qt.WindowStaysOnTopHint) #强制置顶

        self.new_dbc_file_name = './dbc_file/new/'+'new_dbc_hirain.csv' #更新dbc文件路径
        self.dbc_exist_flag = self.dbc_flag() #重置dbc标志文件，如果文件存在则置1
        self.pushButton_3.setEnabled(False)
        self.statusbar.showMessage('初始化成功', 3000)

        self.pushButton_2.clicked.connect(self.getCANdata)
        self.pushButton.clicked.connect(self.freshDBCfile)
        self.pushButton_3.clicked.connect(self.can_data_parse)
        self.pushButton_4.clicked.connect(self.initDBCfile)

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.pbar.setGeometry(0,186,450,3)
        self.pbar.setFixedHeight(3)  # 设置进度条高度
        self.pbar.setTextVisible(False)  # 不显示进度条文字

        self.timer = QBasicTimer()  # 初始化一个时钟
        self.step = 0

    # 选择要解析的CAN数据
    def getCANdata(self):
        fileName1, filetype = QFileDialog.getOpenFileName(self, "选取文件", "./","Text Files (*.csv);;All Files (*)")  # 设置文件扩展名过滤,注意用双分号间隔
        self.pbar.setValue(0)
        if fileName1:
            self.lineEdit.setText(fileName1)
            self.CAN_data_file = fileName1
            file_path_list = fileName1.split('/')[0:-1] #获取文件路径
            self.filename = fileName1.split('/')[-1]
            self.file_path = '/'.join(file_path_list)
            self.pushButton_3.setEnabled(True)
            self.statusbar.showMessage(f'加载{self.filename}文件成功！')
            return fileName1
        else:
            self.statusbar.showMessage('选择DBC文件！',1000)
    # 按钮更新DBC文件，可以选择新的DBC文件
    def freshDBCfile(self):
        if self.dbc_exist_flag == 1:
            self.initDBCfile()
        fileName1, filetype = QFileDialog.getOpenFileName(self, "选取文件", "./","Text Files (*.csv);;All Files (*)")  # 设置文件扩展名过滤,注意用双分号间隔
        if fileName1:
            oldname = fileName1
            fresh_dbc_file_name = fileName1.split('/')[-1]
            shutil.copyfile(oldname, self.new_dbc_file_name)
            self.dbc_exist_flag = 1;  #如果文件夹里存在新dbc则，将dbc的标志置为1
            self.pushButton_4.setEnabled(True)
            self.statusbar.showMessage(f'更新{fresh_dbc_file_name}文件成功！')
        else:
            pass
    # 按钮可以重置DBC文件，删除用户上传的DBC文件，回到程序内置的DBC文件
    def initDBCfile(self):
        """
        重置dbc文件，删除new文件夹的dbc文件。
        :return:
        """
        if self.dbc_exist_flag == 1:
            os.remove(self.new_dbc_file_name)
            self.pushButton_4.setEnabled(False)
            self.statusbar.showMessage('重置文件成功！')
        else:
            self.pushButton_4.setEnabled(True)
            pass
    # 用于监测文件夹中是否有新的DBC文件
    def dbc_flag(self):
        """
        监测是否有新的dbc文件
        :return:
        """
        if (os.path.exists(self.new_dbc_file_name)):
            return 1
        else:
            self.pushButton_4.setEnabled(False)
            return 0
    # 选择的源数据解析
    def can_data_parse(self):
        """
        采用最新的解析函数
        :return:
        """
        if self.dbc_exist_flag == 1:
            self.CAN_DBC_file_name = self.new_dbc_file_name #如果dbc的文件已经更新则使用最新的dbc文件
        else:
            self.CAN_DBC_file_name = r".\dbc_file\init\DBC_std_v1.0.csv"
        self.CAN_file_name = self.CAN_data_file
        self.save_path = self.file_path + '/result-' + self.filename

        self.lineEdit.setText('')
        self.pushButton_3.setEnabled(False)

        sz = os.path.getsize(self.CAN_file_name)        # 获取文件大小
        if sz < 1_000_000:
            fresh_time = 50
        elif sz < 2_000_000:
            fresh_time = 120
        elif sz < 3_000_000:
            fresh_time = 170
        else:
            fresh_time = int(sz/40000)      # 估计运算时间，40M大约16分钟

        self.timer.start(fresh_time, self)  # 启动QBasicTimer，每100ms调用一次事件回调函数
        self.step = 0

        self.my_cal = MyCal(self.CAN_file_name, self.CAN_DBC_file_name, self.save_path)       # 实例化线程
        self.my_cal.cal_signal.connect(self.cal_callback) # 将线程累中定义的信号连接到本类中的信号接收函数中
        self.my_cal.start()     # 开启进程
    # 计算完毕的回调函数，用于显示计算的结果
    def cal_callback(self, back_msg):
        self.step = 99
        file_window = (self.file_path).replace('/', '\\')
        msg = back_msg[0]
        t_t = back_msg[1]
        if msg == 1:
            os.system("start explorer " + file_window)
            self.pushButton_3.setEnabled(True)
            self.statusbar.showMessage(f'{self.filename}文件解析完成！用时{str(t_t)}秒')
        else:
            self.statusbar.showMessage(f'{self.filename}文件解析失败，请重新提交！')
    # 进度条显示的函数
    def timerEvent(self, *args, **kwargs):  # QBasicTimer的事件回调函数
        # 把进度条每次充值的值赋给进度条
        self.pbar.setValue(self.step)
        if self.step >= 100:
            # 停止进度条
            self.timer.stop()
            self.step = 0
            return
        # 把进度条卡在99，等处理好了再到100
        if self.step < 99:
            self.step += 1
            self.statusbar.showMessage(f'正在解析文件，完成进度{self.step}%')

# 这是一个多线程运行的类，输入CAN、DBC、保存路径即可进行解析
class MyCal(QThread):
    # 自定义一个信号名
    cal_signal = pyqtSignal(list)    # 声明带一个int类型参数的信号
    def __init__(self, CAN_file_name, CAN_DBC_file_name, save_path, parent=None):  # model为传入的模型，img为传入的要处理的图片
        # 传入需要计算的数据
        super(MyCal, self).__init__(parent)
        # 设置工作状态
        self.work = True
        self.CAN_file_name = CAN_file_name
        self.CAN_DBC_file_name = CAN_DBC_file_name
        self.save_path = save_path

    # 析构函数
    def __del__(self):
        self.work = False
        self.wait()

    # 该进程主程序
    def run(self):
        t0 = time.time()
        try:
            func(self.CAN_file_name, self.CAN_DBC_file_name, self.save_path)
            msg = 1
        except Exception:
            raise
            msg = 0
        t1 = time.time()
        total_time = round(t1-t0, 2)
        self.cal_signal.emit([msg, total_time])

#编写一个公共类CommomHelper,用于帮助解读qss文件
class CommonHelper:
    def __init__(self):
        pass

    @staticmethod
    def readQss(style):
        with open(style, 'r',encoding = 'utf-8') as f:
            return f.read()

if __name__ == "__main__":
    # On Windows calling this function is necessary.
    # Pyinstaller 打包多使用该语句
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = MainWindow()

    styleFile = 'init/style.qss'
    qssStyle = CommonHelper.readQss(styleFile)
    window.setStyleSheet(qssStyle)

    window.show()
    sys.exit(app.exec_())