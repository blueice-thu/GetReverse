from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import sys, os, requests

from style import Ui_MainWindow
from utils import get_book_info, prepareFolders, get_chapter_info, downloadChapter

class GetInfoThread(QObject):
    overSignal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    @pyqtSlot(str, str, str)
    def startGetInfo(self, USERID, PASSWORD, BOOKID):        
        try:
            result = get_book_info(USERID, PASSWORD, BOOKID)
            self.overSignal.emit(result)
        except Exception as ex:
            if True:
                print(str(ex))
            self.overSignal.emit({})

class DownloadThread(QObject):
    overSignal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
    
    @pyqtSlot(dict)
    def startDownload(self, bookInfo):
        prepareFolders(bookInfo)
        try:
            for link, chapter in zip(bookInfo['links'], bookInfo['chapters']):
                page, url = get_chapter_info(link)
                url = url.replace(r'1.', r'{}.')
                downloadChapter(page, url, chapter)
            self.overSignal.emit(True)
        except Exception as ex:
            if True:
                print(str(ex))
            self.overSignal.emit(False)

class MainWindow(QMainWindow, Ui_MainWindow):
    getInfoSignal = pyqtSignal(str, str, str)
    downloadSignal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._moveCenter()
        self.buttonGetInfo.clicked.connect(self.buttonGetInfoClicked)
        self.buttonDownload.clicked.connect(self.buttonDownloadClicked)

        self.getInfoThread = QThread()
        self.innerGetInfoThread = GetInfoThread()
        self.getInfoSignal.connect(self.innerGetInfoThread.startGetInfo)
        self.innerGetInfoThread.overSignal.connect(self.overGetInfo)
        self.innerGetInfoThread.moveToThread(self.getInfoThread)
        self.getInfoThread.start()

        self.downloadThread = QThread()
        self.innerDownloadThread = DownloadThread()
        self.downloadSignal.connect(self.innerDownloadThread.startDownload)
        self.innerDownloadThread.overSignal.connect(self.overDownload)
        self.innerDownloadThread.moveToThread(self.downloadThread)
        self.downloadThread.start()

        self.bookInfo = None
    
    def checkInput(self):
        if self.inputUserid.text() == '' \
                or self.inputPassword.text() == '' \
                or self.inputBookId.text() == '' \
                or len(str(self.inputUserid.text())) != 10:
            self.labelStatus.setText('输入错误！')
            return False
        return True
    
    def buttonGetInfoClicked(self):
        if not self.checkInput():
            return
        self.buttonGetInfo.setEnabled(False)
        self.buttonDownload.setEnabled(False)
        self.labelStatus.setText('正在查询……')
        self.getInfoSignal.emit(self.inputUserid.text(), self.inputPassword.text(), self.inputBookId.text())

    def buttonDownloadClicked(self):
        if not self.bookInfo:
            self.labelStatus.setText('尚未查到书籍信息！')
            return
        self.buttonGetInfo.setEnabled(False)
        self.buttonDownload.setEnabled(False)
        self.labelStatus.setText('正在下载……')
        self.downloadSignal.emit(self.bookInfo)
    
    @pyqtSlot(dict)
    def overGetInfo(self, result):
        if not result:
            self.labelBookInfo.setText('输入错误！')
        else:
            self.labelStatus.setText('查询成功！')
            infoText = '题目：{}\n共{}个章节：\n'.format(result['title'], len(result['chapters']))
            for chap in result['chapters']:
                infoText += (' • ' + chap + '\n')
            self.bookInfo = result
            self.labelBookInfo.setText(infoText)
        self.buttonGetInfo.setEnabled(True)
        self.buttonDownload.setEnabled(True)
    
    @pyqtSlot(bool)
    def overDownload(self, result):
        if not result:
            self.labelStatus.setText('下载失败！继续下载可断点续传！')
        else:
            self.labelStatus.setText('下载成功！')
        self.buttonGetInfo.setEnabled(True)
        self.buttonDownload.setEnabled(True)
    
    def _moveCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())