import os.path
from storages import *
from models import *
from helpers import *
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QScreen
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, \
    qApp, QFileDialog, QScrollBar


class KpeWindow(QLabel):
    def __init__(self, parent=None):
        QtWidgets.QLabel.__init__(self, parent)
        main = QtWidgets.QVBoxLayout(self)
        self.selection = QtWidgets.QRubberBand(
            QtWidgets.QRubberBand.Rectangle, self)

    def keyPressEvent(self, event):
        print(event.key())
        if event.key() == QtCore.Qt.Key_Return:
            print('yay')

        # QtWidgets.QMessageBox.warning(self, 'MDI', 'keyPressEvent')
        self.parent().keyPressEvent(event)

    def mousePressEvent(self, event):
        '''
            Mouse is pressed. If selection is visible either set dragging mode (if close to border) or hide selection.
            If selection is not visible make it visible and start at this point.
        '''
        print(event)
        if event.button() == QtCore.Qt.LeftButton:

            position = QtCore.QPoint(event.pos())
            if self.selection.isVisible():
                # visible selection
                if (self.upper_left - position).manhattanLength() < 20:
                    # close to upper left corner, drag it
                    self.mode = "drag_upper_left"
                elif (self.lower_right - position).manhattanLength() < 20:
                    # close to lower right corner, drag it
                    self.mode = "drag_lower_right"
                else:
                    # clicked somewhere else, hide selection
                    self.selection.hide()
            else:
                # no visible selection, start new selection
                self.upper_left = position
                self.lower_right = position
                self.mode = "drag_lower_right"
                self.selection.show()

    def mouseMoveEvent(self, event):
        '''
            Mouse moved. If selection is visible, drag it according to drag mode.
        '''

        if self.selection.isVisible():
            # visible selection
            if self.mode is "drag_lower_right":
                self.lower_right = QtCore.QPoint(event.pos())
            elif self.mode is "drag_upper_left":
                self.upper_left = QtCore.QPoint(event.pos())
            # update geometry
            self.selection.setGeometry(QtCore.QRect(
                self.upper_left, self.lower_right).normalized())


class QImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.storage = JsonStorage()
        # self.printer = QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = KpeWindow(self)
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)
        self.setCentralWidget(self.scrollArea)
        self.createActions()
        self.createMenus()

        layout = QtWidgets.QVBoxLayout(self)
        pixmap = QScreen.grabWindow(app.primaryScreen(), app.desktop().winId())
        self.imageLabel.setPixmap(pixmap)
        layout.addWidget(self.imageLabel)
        # new
        self.imageLabel.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.imageLabel)
        self.imageLabel.setFocus(True)
        self.setLayout(layout)

        geometry = app.desktop().availableGeometry()
        self.setFixedSize(geometry.width(), geometry.height())

        self.setWindowTitle("Image Viewer")
        self.resize(800, 600)

    def open(self):
        '''
            Open a file dialog and give the ability to select a file.
            Returns None
        '''
        options = QFileDialog.Options()
        # fileName = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())
        self.filePath, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                       'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if self.filePath:
            image = QImage(self.filePath)
            if image.isNull():
                QMessageBox.information(
                    self, "Image Viewer", "Cannot load %s." % self.filePath)
                return

            self.imageLabel.setPixmap(QPixmap.fromImage(image))
            self.scaleFactor = 1.0

            self.scrollArea.setVisible(True)
            self.printAct.setEnabled(True)
            self.removeAct.setEnabled(True)
            self.fitToWindowAct.setEnabled(True)
            self.saveSelectedAreaAct.setEnabled(True)
            self.copyToDataDirectoryAndRemoveSourceAct.setEnabled(True)

            self.updateActions()

            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()

    def print_(self):
        '''
            Can be used for printing selected file.
            Returns None
        '''
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(),
                                size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def zoomIn(self):
        '''
            Zooming the opened file by a factor 1.25.
            Returns None
        '''
        self.scaleImage(1.25)

    def zoomOut(self):
        '''
            Zooming the opened file by a factor 0.8.
        '''
        self.scaleImage(0.8)

    def normalSize(self):
        '''
            Normalize zooming state for the opened file.
            Returns None
        '''
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        '''
            Normalize zoom factor for the current screen
            Returns None
        '''
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def about(self):
        '''
            Show a message about the app.
            Returns None
        '''
        QMessageBox.about(self, "About Image Viewer", "")

    def showMessageDialog(self, message):
        '''Takes a message string and shows popup within the message

        message | string | this string will be used for showing into popup

        Returns None
        '''
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()

    def saveSelectedArea(self):
        '''Saves selected area into json file in data folder.
        Returns None
        '''
        upperLeft = (self.imageLabel.upper_left.x(),
                     self.imageLabel.upper_left.y())

        lowerLeft = (self.imageLabel.upper_left.x(),
                     self.imageLabel.lower_right.y())

        upperRight = (self.imageLabel.lower_right.x(),
                      self.imageLabel.upper_left.y())

        lowerRight = (self.imageLabel.lower_right.x(),
                      self.imageLabel.lower_right.y())

        self.storage.insert(
            Annotation(
                os.path.basename(self.filePath),
                100, 100,
                [Box(lowerRight[0], lowerRight[1], upperLeft[0], upperLeft[1])]))
        QMessageBox.about(self, "ImageViewer", "Image was saved")

    def moveFileToDataDirectory(self, filePathFrom):
        '''Takes a file path and copy it into data directory

        filePathFrom | string | this string will be used for moving file into data directory

        Returns None
        '''
        currentDirectory = os.getcwd()
        fileFromName = os.path.basename(filePathFrom)
        separator = '\\' if OSExtensions.isWindows() else '/'
        filePathTo = f'{currentDirectory}{separator}data{separator}{fileFromName}'
        FileExtensions.moveFileFromTo(filePathFrom, filePathTo)

    def copyToDataDirectoryAndRemoveSource(self):
        '''Copy a file into data folder and remover the source file.
        Returns None
        '''
        self.moveFileToDataDirectory(self.filePath)
        FileExtensions.removeFile(self.filePath)
        QMessageBox.about(self, "ImageViewer",
                          "Image was moved to data directory and removed")

    def removeFile(self):
        '''Remove selected file.
        Returns None
        '''
        FileExtensions.removeFile(self.filepath)

    def createActions(self):
        ''' Handlers for actions.
        Returns None
        '''
        self.openAct = QAction(
            "&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.printAct = QAction(
            "&Print...", self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.removeAct = QAction(
            "&Remove...", self, enabled=False, triggered=self.removeFile)
        self.exitAct = QAction(
            "E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoomInAct = QAction(
            "Zoom &In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction(
            "Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction(
            "&Normal Size", self, shortcut="Ctrl+N", enabled=False, triggered=self.normalSize)
        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False, checkable=True, shortcut="Ctrl+F",
                                      triggered=self.fitToWindow)
        self.saveSelectedAreaAct = QAction(
            "&Save selected area...",
            self,
            shortcut="Ctrl+S",
            enabled=False,
            triggered=self.saveSelectedArea)
        self.copyToDataDirectoryAndRemoveSourceAct = QAction(
            "&copy to data directory and remove the source...",
            self,
            shortcut="Ctrl+R",
            enabled=False,
            triggered=self.copyToDataDirectoryAndRemoveSource)
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)

    def createMenus(self):
        '''Creates menu for actions.
        Returns None
        '''
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addAction(self.removeAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.shortcutsMenu = QMenu("&Shortcuts", self)
        self.shortcutsMenu.addAction(
            self.copyToDataDirectoryAndRemoveSourceAct)
        self.shortcutsMenu.addAction(self.saveSelectedAreaAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.shortcutsMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        '''Update buttons states from enable to disable.
        Returns None
        '''
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor: float):
        '''Takes a factor as float and resizes bars, windows, scrolls

        factor | float | this number will be used for calculating the proportionality

        Returns None
        '''
        self.scaleFactor *= factor
        self.imageLabel.resize(
            self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar: QScrollBar, factor: float):
        '''Takes a message string and shows popup within the message

        scrollBar | QScrollBar | this scrollBar object will be used for resizing by a factor
        factor | float | this number will be used for calculating the proportionality of scrollbars

        Returns None
        '''
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imageViewer = QImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
    # TODO QScrollArea support mouse
