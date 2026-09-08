# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
    QStatusBar, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(900, 700)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.mainLayout = QVBoxLayout(self.centralwidget)
        self.mainLayout.setSpacing(6)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(8, 8, 8, 8)
        self.daysContainer = QWidget(self.centralwidget)
        self.daysContainer.setObjectName(u"daysContainer")
        self.daysContainer.setMaximumHeight(42)
        self.daysLayout = QHBoxLayout(self.daysContainer)
        self.daysLayout.setSpacing(5)
        self.daysLayout.setObjectName(u"daysLayout")
        self.daysLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout.addWidget(self.daysContainer)

        self.contentLayout = QHBoxLayout()
        self.contentLayout.setSpacing(6)
        self.contentLayout.setObjectName(u"contentLayout")
        self.controlsFrame = QFrame(self.centralwidget)
        self.controlsFrame.setObjectName(u"controlsFrame")
        self.controlsFrame.setMinimumWidth(150)
        self.controlsFrame.setMaximumWidth(150)
        self.controlsLayout = QVBoxLayout(self.controlsFrame)
        self.controlsLayout.setSpacing(6)
        self.controlsLayout.setObjectName(u"controlsLayout")
        self.editBtn = QPushButton(self.controlsFrame)
        self.editBtn.setObjectName(u"editBtn")
        self.editBtn.setMinimumHeight(30)

        self.controlsLayout.addWidget(self.editBtn)

        self.todayBtn = QPushButton(self.controlsFrame)
        self.todayBtn.setObjectName(u"todayBtn")
        self.todayBtn.setMinimumHeight(30)

        self.controlsLayout.addWidget(self.todayBtn)

        self.controlsSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.controlsLayout.addItem(self.controlsSpacer)


        self.contentLayout.addWidget(self.controlsFrame)

        self.scheduleTable = QTableWidget(self.centralwidget)
        if (self.scheduleTable.columnCount() < 3):
            self.scheduleTable.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.scheduleTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.scheduleTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.scheduleTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.scheduleTable.setObjectName(u"scheduleTable")
        self.scheduleTable.setMinimumWidth(300)
        self.scheduleTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.scheduleTable.setSelectionMode(QAbstractItemView.NoSelection)
        self.scheduleTable.setAlternatingRowColors(True)

        self.contentLayout.addWidget(self.scheduleTable)


        self.mainLayout.addLayout(self.contentLayout)

        self.volumeGroup = QGroupBox(self.centralwidget)
        self.volumeGroup.setObjectName(u"volumeGroup")
        self.volumeGroup.setMaximumHeight(185)
        self.volumeLayout = QHBoxLayout(self.volumeGroup)
        self.volumeLayout.setSpacing(12)
        self.volumeLayout.setObjectName(u"volumeLayout")

        self.mainLayout.addWidget(self.volumeGroup)

        self.buttonsFrame = QFrame(self.centralwidget)
        self.buttonsFrame.setObjectName(u"buttonsFrame")
        self.bottomLayout = QHBoxLayout(self.buttonsFrame)
        self.bottomLayout.setSpacing(8)
        self.bottomLayout.setObjectName(u"bottomLayout")
        self.bellBtn = QPushButton(self.buttonsFrame)
        self.bellBtn.setObjectName(u"bellBtn")
        self.bellBtn.setMinimumHeight(34)

        self.bottomLayout.addWidget(self.bellBtn)

        self.musicBtn = QPushButton(self.buttonsFrame)
        self.musicBtn.setObjectName(u"musicBtn")
        self.musicBtn.setMinimumHeight(34)

        self.bottomLayout.addWidget(self.musicBtn)

        self.anthemBtn = QPushButton(self.buttonsFrame)
        self.anthemBtn.setObjectName(u"anthemBtn")
        self.anthemBtn.setMinimumHeight(34)

        self.bottomLayout.addWidget(self.anthemBtn)

        self.announcementBtn = QPushButton(self.buttonsFrame)
        self.announcementBtn.setObjectName(u"announcementBtn")
        self.announcementBtn.setMinimumHeight(34)

        self.bottomLayout.addWidget(self.announcementBtn)

        self.stopBtn = QPushButton(self.buttonsFrame)
        self.stopBtn.setObjectName(u"stopBtn")
        self.stopBtn.setMinimumHeight(34)
        self.stopBtn.setStyleSheet(u"background-color: #ff6b6b; color: white;")

        self.bottomLayout.addWidget(self.stopBtn)


        self.mainLayout.addWidget(self.buttonsFrame)

        self.trackLabel = QLabel(self.centralwidget)
        self.trackLabel.setObjectName(u"trackLabel")
        self.trackLabel.setMinimumHeight(20)
        self.trackLabel.setStyleSheet(u"color: #1565c0; font-size: 11px; padding: 2px 8px;")

        self.mainLayout.addWidget(self.trackLabel)

        self.statusLabel = QLabel(self.centralwidget)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setMinimumHeight(50)
        self.statusLabel.setStyleSheet(u"background-color: #f5f5f5; padding: 8px; border-radius: 4px;")
        self.statusLabel.setWordWrap(True)

        self.mainLayout.addWidget(self.statusLabel)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 900, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"School Bell", None))
        self.editBtn.setText(QCoreApplication.translate("MainWindow", u"Edit", None))
#if QT_CONFIG(tooltip)
        self.todayBtn.setToolTip(QCoreApplication.translate("MainWindow", u"Navigate to current day", None))
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem = self.scheduleTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        ___qtablewidgetitem1 = self.scheduleTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"End", None))
        ___qtablewidgetitem2 = self.scheduleTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Break", None))
        self.volumeGroup.setTitle(QCoreApplication.translate("MainWindow", u"Volume", None))
        self.trackLabel.setText("")
        self.statusLabel.setText(QCoreApplication.translate("MainWindow", u"Ready", None))
    # retranslateUi

