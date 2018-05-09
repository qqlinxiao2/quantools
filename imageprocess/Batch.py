# -*- encoding:utf-8 -*-
import sys

import os
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QPushButton, QMessageBox, QMainWindow, QFileDialog, QLabel, QSlider, \
    QLineEdit, QTableWidget


class uiQwidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
    def initUI(self):
        self.setWindowTitle('图片批量压缩工具')
        self.resize(600,500)
        self.setWindowIcon(QIcon('img/logo.ico'))

        btn_add = QPushButton(QIcon('img/add.ico'),'添加文件',self)
        btn_add.resize(115,30)
        btn_add.move(20,10)
        btn_add.clicked.connect(self.showAddFileDialog)

        btn_del = QPushButton('删除任务',self)
        btn_del.setGeometry(490,10, 70, 25)

        horizontalHeader = ['','文件名称','进度']
        self.table = QTableWidget()
        self.table.setColumnCount(3)

        self.label_out_set = QLabel('输出设置',self)
        self.label1 = QLabel('图片质量',self)
        sld = QSlider(Qt.Horizontal, self)
        sld.setFocusPolicy(Qt.NoFocus)
        sld.setGeometry(10,400,150,20)

        self.label_out_pos = QLabel('输出位置',self)
        self.qle_out = QLineEdit(self)
        self.qle_out.setGeometry(10, 430 ,380,25)
        btn_out = QPushButton(QIcon('img/out.ico'),'浏览', self)
        btn_out.setGeometry(405, 430, 70, 25)
        btn_out.clicked.connect(self.showOutputFolderDialog)
        btn_open = QPushButton(QIcon('img/open.ico'),'打开', self)
        btn_open.setGeometry(480, 430, 70, 25)
        btn_open.clicked.connect(self.openOutputFolder)
        self.show()
    def showAddFileDialog(self):
        fname = QFileDialog.getOpenFileNames(self, '添加文件', '','Image Files (*.jpg *.jpeg *.png);;All Files (*)')
        print(fname)
    def showOutputFolderDialog(self):
        fname = QFileDialog.getExistingDirectory(self,'选择目录')
        if fname:
            self.qle_out.setText(fname)
    def openOutputFolder(self):
        pos = self.qle_out.text()
        if pos and os.path.exists(pos):
            if os.path.isdir(pos):
                os.startfile(pos)
    def closeEvent(self, event):
        reply = QMessageBox.question(self,'消息','确认要关闭吗？',QMessageBox.Yes | QMessageBox.No,QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
if __name__  ==  '__main__':
    app = QApplication(sys.argv)
    ui = uiQwidget()
    sys.exit(app.exec())