from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QWidget, QAction, QGridLayout,
    QListWidget, QStackedWidget, QListWidgetItem, QSizePolicy,
    QPushButton, QLineEdit, QFormLayout, QFrame, QTextEdit
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
import sqlite3
import datetime
import os

# ------------------------------
# UI Setup
# ------------------------------

def form(app, available_cameras):
    form_frame = QFrame()
    form_frame.setObjectName("form_frame")

    form = QFormLayout()
    form.setSpacing(10)

    app.tag = QLineEdit()
    app.name = QLineEdit()
    app.address = QLineEdit()
    app.purpose = QTextEdit()
    app.who_to_meet = QLineEdit()
    app.phone = QLineEdit()
    app.timeout = QLineEdit()
    app.date = QLineEdit()
    app.picture = QLabel()

    app.tag.setPlaceholderText("001")
    app.name.setPlaceholderText("Calvin Ugwoke")
    app.address.setPlaceholderText("Dawaki")
    app.purpose.setPlaceholderText("To Code")
    app.who_to_meet.setPlaceholderText("The manager")
    app.phone.setPlaceholderText("09061422818")
    app.picture.setStyleSheet("border: 3px solid blue; border-radius:10px")

    get_time_btn2 = QPushButton("⏱")
    get_time_btn2.setToolTip("Set current time")
    get_time_btn2.clicked.connect(app.get_current_time)
    date_btn = QPushButton("📅")
    date_btn.setToolTip("Set current date")
    date_btn.clicked.connect(app.get_current_date)

    app.timeout.setReadOnly(True)
    app.date.setReadOnly(True)

    picture_hbox = QHBoxLayout()
    picture_hbox.setAlignment(Qt.AlignCenter)
    profile_path = os.path.join(app.images_dir, "profile.jpg")
    if os.path.exists(profile_path):
        app.picture.setPixmap(QPixmap(profile_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    picture_hbox.addWidget(app.picture)

    icon_path = os.path.join(app.images_dir, "camera.svg")
    change_btn = QPushButton(" Change Photo")
    if os.path.exists(icon_path):
        change_btn.setIcon(QIcon(QPixmap(icon_path).scaled(32, 32)))
    camera = app.config_data["camera"]
    change_btn.clicked.connect(lambda: app.camera.open_camera_dialog(camera if camera in available_cameras else 0))
    picture_hbox.addWidget(change_btn)

    time_out_hbox = QHBoxLayout()
    time_out_hbox.addWidget(app.timeout)
    time_out_hbox.addWidget(get_time_btn2)

    date_hbox = QHBoxLayout()
    date_hbox.addWidget(app.date)
    date_hbox.addWidget(date_btn)

    form.addRow(picture_hbox)
    form_hbox = QHBoxLayout()

    form.addRow(QLabel(""))

    # ---first column---
    first_col = QFormLayout()
    first_col.addRow("Tag:", app.tag)
    first_col.addRow("Name:", app.name)
    first_col.addRow("Address:", app.address)

    # -----second column-----
    second_col = QFormLayout()
    second_col.addRow("Phone number:", app.phone)
    second_col.addRow("Time out:", time_out_hbox)
    second_col.addRow("Date:", date_hbox)

    form_hbox.addLayout(first_col)
    form_hbox.addSpacing(50)
    form_hbox.addLayout(second_col)

    form.addRow(form_hbox)
    form.addRow("Who to meet:", app.who_to_meet)
    form.addRow("Purpose:", app.purpose)

    btn = QPushButton("Submit")
    btn.clicked.connect(app.save_record)
    btn.setFont(QFont("Segeo UI", 13, QFont.Bold))

    btn.setFixedWidth(300)
    form.addRow(btn)

    form_frame.setLayout(form)
    return form_frame

def dashboard(app, stack, list_):
    frame = QFrame()
    frame.setObjectName("form_frame")

    vbox = QVBoxLayout(frame)
    with sqlite3.connect(app.db_path) as db:
        cursor = db.cursor()
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        conn = cursor.execute("SELECT id, picture, tag, name, address, phone, time_out FROM users WHERE date = ?", (current_date,))
        info = conn.fetchall()
        if info:
            font = QFont("Segeo UI", italic=True, weight=800)
            lb = QLabel("Visitors Today")
            lb.setFont(font)
            vbox.addWidget(lb, alignment=Qt.AlignCenter)
            list_of_visitors = QGridLayout()
            for count, i in enumerate(["No", "Picture", "Tag", "Name", "Address", "Phone", "Status"]):
                lbl = QLabel(text=i, alignment=Qt.AlignCenter)
                lbl.setStyleSheet("font-weight: 500;border: 1px solid white;")
                list_of_visitors.addWidget(lbl, 0, count)
            for c, j in enumerate(info, start=1):
                for d, k in enumerate(j):
                    lbl = QLabel(text=str(k), alignment=Qt.AlignCenter)
                    list_of_visitors.addWidget(lbl, c, d)
                    if d==6:
                        if j[6] != "":
                            lbl.setText("Active")
                        else:
                            lbl.setText("Not Active")
                    if d==1:
                        pix = QPixmap()
                        pix.loadFromData(k)
                        lbl.setPixmap(pix)
                        lbl.setText("")
                        lbl.setFixedSize(100, 100)
            vbox.addLayout(list_of_visitors)
        else:
            def change():
                stack.setCurrentIndex(1)
                list_.setCurrentRow(1)
                
            vbox.addWidget(QLabel("No Visitors Today"), alignment=Qt.AlignCenter)
            btn = QPushButton("Register")
            btn.setFixedWidth(200)
            btn.clicked.connect(change)
            vbox.addWidget(btn)
        vbox.setAlignment(Qt.AlignTop)
    return frame

def initUI(app, available_cameras):
    window = QWidget()
    vbox = QVBoxLayout()

    # Title + logo
    hbox = QHBoxLayout()
    app.title = QLabel("Visitor Log")
    app.title.setFont(QFont("Segoe UI", 30, QFont.Bold))
    logo = QLabel()
    logo_path = os.path.join(app.images_dir, "logo.png")
    if os.path.exists(logo_path):
        pixmap = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
    hbox.addWidget(logo, alignment=Qt.AlignLeft)
    hbox.addWidget(app.title, alignment=Qt.AlignCenter)
    hbox.addStretch()
    vbox.addLayout(hbox)

    # Menu
    menu = app.menuBar()
    file = menu.addMenu("File")
    save = QAction("Save Record", app)
    save.setShortcut("Ctrl+S")
    load = QAction("Load Record", app)
    load.setShortcut("Ctrl+L")
    toggle = QAction("Toggle Theme", app)
    toggle.setShortcut("Ctrl+T")
    view = QAction("View Table", app)
    view.setShortcut("Ctrl+V")
    settings_action = QAction("Sign In / Admin Manager", app)
    logout_action = QAction("Logout", app)
    file.addAction(save)
    file.addAction(load)
    file.addAction(toggle)
    file.addAction(view)
    file.addSeparator()
    file.addAction(settings_action)
    file.addAction(logout_action)
    file.triggered.connect(app.menu_commands)

    edit = menu.addMenu("Edit")
    edit.addAction("Clear All")
    edit.addAction("Clear Date")
    edit.addAction("Clear Timeout")
    edit.triggered.connect(app.menu_commands)

    # toolbar for quick access to commands
    tb = app.addToolBar("File")
    tb.setIconSize(QSize(30, 30))
    tb.setMovable(False)

    def give_space():
        space = QWidget()
        space.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return space

    tb.addWidget(give_space())
    save_icon = os.path.join(app.images_dir, "save.svg")
    save = QAction("Save",app)
    if os.path.exists(save_icon):
        save.setIcon(QIcon(save_icon))
    tb.addAction(save)

    tb.addWidget(give_space())
    load_icon = os.path.join(app.images_dir, "folder-open.svg")
    load = QAction("Load",app)
    if os.path.exists(load_icon):
        load.setIcon(QIcon(load_icon))
    tb.addAction(load)

    tb.addWidget(give_space())
    register_icon = os.path.join(app.images_dir, "cash-register.svg")
    reg = QAction("Register",app)
    if os.path.exists(register_icon):
        reg.setIcon(QIcon(register_icon))
    tb.addAction(reg)
    
    tb.addWidget(give_space())
    export_icon = os.path.join(app.images_dir, "file-export.svg")
    export = QAction("Export",app)
    if os.path.exists(export_icon):
        export.setIcon(QIcon(export_icon))
    tb.addAction(export)

    tb.addWidget(give_space())
    sign_icon = os.path.join(app.images_dir, "user-circle.svg")
    sign = QAction("Sign In",app)
    if os.path.exists(sign_icon):
        sign.setIcon(QIcon(sign_icon))
    tb.addAction(sign)

    tb.addWidget(give_space())
    tb.actionTriggered.connect(lambda a: app.toolbtnpressed(a, stack, windows))

    #list widget to manage display
    windows = QListWidget()
    windows.setFixedWidth(200)

    for count, (i, j) in enumerate((("Dashboard", "bar-chart.svg"), ("Form", "file-alt.svg"))):
        img = os.path.join(app.images_dir, j)
        item = QListWidgetItem(i)
        if os.path.exists(img):
            item.setIcon(QIcon(QPixmap(img).scaled(32, 32)))
        windows.insertItem(count, item)

    windows.setCurrentRow(0)

    # stacked widget for the form and the dashboard
    stack = QStackedWidget()
    stack.addWidget(dashboard(app, stack, windows))
    stack.addWidget(form(app, available_cameras))
    
    windows.currentRowChanged.connect(lambda e: stack.setCurrentIndex(e))
    windows.itemClicked.connect(lambda e: stack.setCurrentIndex(0 if e.text() == "Dashboard" else 1))

    # hbox to manage list and stacked
    main_hbox = QHBoxLayout()
    main_hbox.addWidget(windows)
    main_hbox.addWidget(stack)

    vbox.addLayout(main_hbox)
    window.setLayout(vbox)
    app.setCentralWidget(window)
