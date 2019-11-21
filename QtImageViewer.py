import os.path
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QScreen
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, \
    qApp, QFileDialog


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

        #QtWidgets.QMessageBox.warning(self, 'MDI', 'keyPressEvent')
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

        #self.printer = QPrinter()
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
            self.updateActions()

            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()

    def print_(self):
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

    def remove(self):
        if os.path.isfile(self.filePath):
            # os.remove(self.filePath)
            self.showMessageDialog("The file was removed!!!!")
            pass
        pass

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def about(self):
        QMessageBox.about(self, "About Image Viewer", "")

    def showMessageDialog(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        #msg.setInformativeText("This is additional information")
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()

    def createActions(self):
        self.openAct = QAction(
            "&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.printAct = QAction(
            "&Print...", self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.removeAct = QAction(
            "&Remove...", self, shortcut="Ctrl+R", enabled=False, triggered=self.remove)
        self.exitAct = QAction(
            "E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoomInAct = QAction(
            "Zoom &In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction(
            "Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction(
            "&Normal Size", self, shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)
        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False, checkable=True, shortcut="Ctrl+F",
                                      triggered=self.fitToWindow)
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)

    def createMenus(self):
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

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(
            self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
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
