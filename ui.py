from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QWidget, QAction, QGridLayout,
    QListWidget, QStackedWidget, QListWidgetItem, QSizePolicy,
    QPushButton, QLineEdit, QFormLayout, QFrame, QTextEdit, QScrollArea
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
import sqlite3
import datetime
import os

# ------------------------------
# UI Setup
# ------------------------------

class UI():
    def __init__(self, app, available_cameras):
        self.app = app
        self.available_cameras = available_cameras

    def form(self, timeout=False):
        if not hasattr(self, "form_frame"):
            self.form_frame = QFrame()
            self.form_frame.setObjectName("form_frame")

            self.form_lay = QFormLayout()
            self.form_lay.setSpacing(10)

            self.form_frame.setLayout(self.form_lay)
        else:
            self.clear_layout(self.form_lay)
        
        self.picture_hbox = QHBoxLayout()
        self.time_out_hbox = QHBoxLayout()
        self.date_hbox = QHBoxLayout()
        self.form_hbox = QHBoxLayout()
        
        self.first_col = QFormLayout()
        self.second_col = QFormLayout()

        self.app.tag = QLineEdit()
        self.app.name = QLineEdit()
        self.app.address = QLineEdit()
        self.app.purpose = QTextEdit()
        self.app.who_to_meet = QLineEdit()
        self.app.phone = QLineEdit()
        self.app.timeout = QLineEdit()
        self.app.date = QLineEdit()
        self.app.picture = QLabel()

        self.app.tag.setPlaceholderText("001")
        self.app.name.setPlaceholderText("Calvin Ugwoke")
        self.app.address.setPlaceholderText("Dawaki")
        self.app.purpose.setPlaceholderText("To Code")
        self.app.who_to_meet.setPlaceholderText("The manager")
        self.app.phone.setPlaceholderText("09061422818")
        self.app.picture.setStyleSheet("border: 3px solid blue; border-radius:10px")

        self.get_time_btn2 = QPushButton("⏱")
        self.get_time_btn2.setToolTip("Set current time")
        self.get_time_btn2.clicked.connect(self.app.get_current_time)
        self.date_btn = QPushButton("📅")
        self.date_btn.setToolTip("Set current date")
        self.date_btn.clicked.connect(self.app.get_current_date)

        self.app.timeout.setReadOnly(True)
        self.app.date.setReadOnly(True)

        self.picture_hbox.setAlignment(Qt.AlignCenter)
        profile_path = self.app.get_resources("images", "profile.jpg")
        if os.path.exists(profile_path):
            self.app.picture.setPixmap(QPixmap(profile_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.picture_hbox.addWidget(self.app.picture)

        icon_path = self.app.get_resources("images", "camera.svg")
        change_btn = QPushButton(" Change Photo")
        if os.path.exists(icon_path):
            change_btn.setIcon(QIcon(QPixmap(icon_path).scaled(32, 32)))
        camera = self.app.config_data["camera"]
        change_btn.clicked.connect(lambda: self.app.camera.open_camera_dialog(camera if camera in self.available_cameras else 0))
        self.picture_hbox.addWidget(change_btn)

        if timeout:
            self.time_out_hbox.addWidget(self.app.timeout)
            self.time_out_hbox.addWidget(self.get_time_btn2)

        self.date_hbox.addWidget(self.app.date)
        self.date_hbox.addWidget(self.date_btn)
            
        self.form_lay.addRow(self.picture_hbox)

        # ---first column---
        self.first_col.addRow("Tag:", self.app.tag)
        self.first_col.addRow("Name:", self.app.name)
        self.first_col.addRow("Address:", self.app.address)

        # -----second column-----
        self.second_col.addRow("Phone number:", self.app.phone)
        if timeout:
            self.second_col.addRow("Time out:", self.time_out_hbox)
        else:
            self.second_col.addRow("Who to meet:", self.app.who_to_meet)
        self.second_col.addRow("Date:", self.date_hbox)

        self.form_hbox.addLayout(self.first_col)
        self.form_hbox.addSpacing(50)
        self.form_hbox.addLayout(self.second_col)

        self.form_lay.addRow(self.form_hbox)
        if timeout:
            self.form_lay.addRow("Who to meet:", self.app.who_to_meet)
        self.form_lay.addRow("Purpose:", self.app.purpose)

        btn = QPushButton("Submit")
        btn.clicked.connect(self.app.save_record)
        btn.setFont(QFont("Segeo UI", 16, QFont.Bold))

        btn.setFixedWidth(300)
        self.form_lay.addRow(btn)

        return self.form_frame

    def change(self, num):
        self.stack.setCurrentIndex(num)
        self.windows.setCurrentRow(num)
    
    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self.clear_layout(item.layout())

    def dashboard(self):
        if not hasattr(self, 'stack_frame'):
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setObjectName("form_frame")
            
            self.stack_frame = QFrame()
            self.stack_frame.setObjectName("form_frame")

            self.vbox = QVBoxLayout(self.stack_frame)

            lb = QLabel()
            lb.setStyleSheet("font-weight: 500;font-size: 25px")
            self.vbox.addWidget(lb, alignment=Qt.AlignCenter)


            self.search_hbox = QFormLayout()
            self.vbox.addLayout(self.search_hbox)

            self.list_of_visitors = QGridLayout()
            self.vbox.addLayout(self.list_of_visitors)
        else:
           self.clear_layout(self.vbox)

        self.search_box = QLineEdit()
        self.search_hbox.addRow("Search: ", self.search_box)

        def filter_log():
            filter_text = self.search_box.text().strip().lower()    

            self.clear_layout(self.list_of_visitors)
            with self.app.get_resources("db", self.app.db_path) as db:
                cursor = db.cursor()
                current_date = datetime.datetime.now().strftime("%d/%m/%Y")
                conn = cursor.execute("SELECT id, picture, tag, name, address, phone, time_out FROM users WHERE date = ?", (current_date,))
                info = conn.fetchall()
                if info:
                    lb.setText("Visitors Today")
                    for count, i in enumerate(["No", "Picture", "Tag", "Name", "Address", "Phone", "Status"]):
                        lbl = QLabel(text=i, alignment=Qt.AlignCenter)
                        lbl.setStyleSheet("font-weight: 500;border: 1px solid white;")
                        self.list_of_visitors.addWidget(lbl, 0, count, alignment=Qt.AlignTop)
                    
                    for row, j in enumerate(info, start=1):
                        if filter_text in j:
                            for col, k  in enumerate(j):
                                lbl = QLabel(text=str(k), alignment=Qt.AlignCenter)
                                if col==6:
                                    lbl.setText("Active" if j[6] else "Not Active")
                                if col==1:
                                    pix = QPixmap()
                                    if k:
                                        pix.loadFromData(k)
                                    else:
                                        pix = QPixmap(self.app.get_resources("images", "profile.jpg"))
                                    pix = pix.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                    lbl.setPixmap(pix)
                                self.list_of_visitors.addWidget(lbl, row, col, alignment=Qt.AlignCenter)
                        else:
                            pass
                else:                    
                    lb.setText("No Visitors Today")
                    btn = QPushButton("Register")
                    btn.setFixedWidth(200)
                    btn.clicked.connect(lambda: self.change(1))
                    self.vbox.addWidget(btn, alignment=Qt.AlignCenter)
                    self.vbox.setAlignment(Qt.AlignTop)
        
        filter_log()
        self.search_box.textChanged.connect(filter_log)

        self.change(0)
        self.vbox.addStretch(1)
        self.scroll_area.setWidget(self.stack_frame)
        
        return self.scroll_area

    def initUI(self):
        window = QWidget()
        vbox = QVBoxLayout()

        # Title + logo
        hbox = QHBoxLayout()
        self.app.title = QLabel("Visitor Log")
        self.app.title.setFont(QFont("Segoe UI", 30, QFont.Bold))
        logo = QLabel()
        logo_path = self.app.get_resources("images", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pixmap)
        hbox.addWidget(logo, alignment=Qt.AlignLeft)
        hbox.addWidget(self.app.title, alignment=Qt.AlignCenter)
        hbox.addStretch()
        vbox.addLayout(hbox)

        # Menu
        menu = self.app.menuBar()
        file = menu.addMenu("File")
        save = QAction("Save Record", self.app)
        save.setShortcut("Ctrl+S")
        load = QAction("Load Record", self.app)
        load.setShortcut("Ctrl+L")
        new = QAction("New Record", self.app)
        new.setShortcut("Ctrl+N")
        toggle = QAction("Toggle Theme", self.app)
        toggle.setShortcut("Ctrl+T")
        view = QAction("View Table", self.app)
        view.setShortcut("Ctrl+V")
        settings_action = QAction("Sign In / Admin Manager", self.app)
        logout_action = QAction("Logout", self.app)

        file.addAction(save)
        file.addAction(load)
        file.addAction(new)
        file.addAction(toggle)
        file.addAction(view)
        file.addSeparator()
        file.addAction(settings_action)
        file.addAction(logout_action)
        file.triggered.connect(self.app.menu_commands)

        edit = menu.addMenu("Edit")
        edit.addAction("Reset All")
        edit.addAction("Clear Date")
        edit.triggered.connect(self.app.menu_commands)

        # toolbar for quick access to commands
        tb = self.app.addToolBar("File")
        tb.setIconSize(QSize(30, 30))
        tb.setMovable(False)

        def give_space():
            space = QWidget()
            space.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            return space

        tb.addWidget(give_space())
        save_icon = self.app.get_resources("images", "save.svg")
        save = QAction("Save", self.app)
        if os.path.exists(save_icon):
            save.setIcon(QIcon(save_icon))
        tb.addAction(save)

        tb.addWidget(give_space())
        load_icon = self.app.get_resources("images", "folder-open.svg")
        load = QAction("Load", self.app)
        if os.path.exists(load_icon):
            load.setIcon(QIcon(load_icon))
        tb.addAction(load)

        tb.addWidget(give_space())
        register_icon = self.app.get_resources("images", "cash-register.svg")
        reg = QAction("Register", self.app)
        if os.path.exists(register_icon):
            reg.setIcon(QIcon(register_icon))
        tb.addAction(reg)
        
        tb.addWidget(give_space())
        export_icon = self.app.get_resources("images", "file-export.svg")
        export = QAction("Export", self.app)
        if os.path.exists(export_icon):
            export.setIcon(QIcon(export_icon))
        tb.addAction(export)

        tb.addWidget(give_space())
        sign_icon = self.app.get_resources("images", "user-circle.svg")
        sign = QAction("Sign In", self.app)
        if os.path.exists(sign_icon):
            sign.setIcon(QIcon(sign_icon))
        tb.addAction(sign)

        tb.addWidget(give_space())
        tb.actionTriggered.connect(lambda a: self.app.toolbtnpressed(a, self.stack, self.windows))

        #list widget to manage display
        self.windows = QListWidget()
        self.windows.setFixedWidth(200)

        for count, (i, j) in enumerate((("Dashboard", "bar-chart.svg"), ("Form", "file-alt.svg"))):
            img = self.app.get_resources("images", j)
            item = QListWidgetItem(i)
            if os.path.exists(img):
                item.setIcon(QIcon(QPixmap(img).scaled(32, 32)))
            self.windows.insertItem(count, item)

        # stacked widget for the form and the dashboard
        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard())
        self.stack.addWidget(self.form(False))
        
        self.windows.currentRowChanged.connect(lambda e: self.stack.setCurrentIndex(e))
        self.windows.itemClicked.connect(lambda e: self.stack.setCurrentIndex(0 if e.text() == "Dashboard" else 1))

        # hbox to manage list and stacked
        main_hbox = QHBoxLayout()
        main_hbox.addWidget(self.windows)
        main_hbox.addWidget(self.stack)

        vbox.addLayout(main_hbox)
        window.setLayout(vbox)
        self.app.setCentralWidget(window)
