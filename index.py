# access_control.py
from PyQt5.QtWidgets import (
    QLabel, QMainWindow, QPushButton, QApplication, QFormLayout, QVBoxLayout,
    QHBoxLayout, QWidget, QLineEdit, QMessageBox, QDialog, QFrame, QAction,
    QTableWidget, QTableWidgetItem, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QColor, QFont
import sys, datetime, sqlite3, os, cv2

def list_available_cameras(max_index_to_check=10):
    available_cameras = []
    for i in range(max_index_to_check):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if sys.platform.startswith("win") else 0)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

available_cameras = list_available_cameras()

class AdminLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Login")
        self.setFixedSize(300, 150)

        layout = QFormLayout(self)

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addRow("Username:", self.username_input)
        layout.addRow("Password:", self.password_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.check_credentials)
        layout.addWidget(self.login_btn)

    def check_credentials(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # replace with a real admin check in production
        if username == "admin" and password == "1234":
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.setWindowTitle("Access Control Management System")
        self.setGeometry(100, 100, 600, 400)

        self.db_path = os.path.join(os.path.dirname(__file__), "my_db.db")
        self.create_database()
        self.initUI()
        self.set_dark_theme()

        # state for camera
        self.cap = None
        self.cam_timer = None
        self.current_camera_index = None

    # ------------------------------
    # Database and Utility
    # ------------------------------
    def backup_to_cloud(self, access_token: str = None):
        """
        Upload the DB to Dropbox if access_token is provided.
        NOTE: Do NOT hardcode tokens in code; pass them at runtime or via env var.
        """
        if not access_token:
            QMessageBox.information(self, "Backup Skipped", "No access token provided for cloud backup.")
            return

        try:
            import dropbox
            dbx = dropbox.Dropbox(access_token)
            with open(self.db_path, "rb") as f:
                backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                dbx.files_upload(f.read(), f"/{backup_name}", mode=dropbox.files.WriteMode.overwrite)
            QMessageBox.information(self, "Backup Complete", "Database backup uploaded to Dropbox successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", f"Error uploading to Dropbox:\n{e}")

    def create_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag TEXT,
                    name TEXT,
                    address TEXT,
                    purpose TEXT,
                    time_in TEXT,
                    time_out TEXT,
                    date TEXT,
                    picture BLOB
                )
            """)
            conn.commit()

    def get_current_time(self, mode):
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if mode == 1:
            self.timein.setText(current_time)
        else:
            self.timeout.setText(current_time)

    def get_current_date(self):
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        self.date.setText(current_date)

    def toggle_theme(self):
        if self.dark_mode:
            self.dark_mode = False
            self.set_light_theme()
        else:
            self.dark_mode = True
            self.set_dark_theme()

    def save_record(self):
        tag = self.tag.text().strip()
        name = self.name.text().strip()
        address = self.address.text().strip()
        time_in = self.timein.text().strip()
        purpose = self.purpose.text().strip()
        time_out = self.timeout.text().strip()
        date = self.date.text().strip()

        if not name or not address or not time_in or not date or not purpose:
            QMessageBox.warning(self, "Error", "Please fill all required fields.")
            return

        # Load profile image as bytes (temp.jpg created by camera)
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(images_dir, exist_ok=True)
        profile_path = os.path.join(images_dir, "temp.jpg")
        picture_data = None
        if os.path.exists(profile_path):
            with open(profile_path, "rb") as f:
                picture_data = f.read()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE name=? AND date=?", (name, date))
            record = cursor.fetchone()

            if record:
                reply = QMessageBox.question(self, "Confirm", f"Update time-out for {name}?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    cursor.execute(
                        "UPDATE users SET time_out=?, picture=? WHERE name=? AND date=?",
                        (time_out, picture_data, name, date)
                    )
            else:
                cursor.execute(
                    "INSERT INTO users (tag, name, address, time_in, purpose, time_out, date, picture) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (tag, name, address, time_in, purpose, time_out, date, picture_data)
                )
            conn.commit()

        self.clear()
        QMessageBox.information(self, "Success", "Record saved successfully!")
        # do NOT auto-backup by default; call backup_to_cloud manually if desired

    def clear(self):
        self.tag.clear()
        self.name.clear()
        self.address.clear()
        self.timein.clear()
        self.purpose.clear()
        self.timeout.clear()
        self.date.clear()

        images_dir = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(images_dir, exist_ok=True)
        profile_path = os.path.join(images_dir, "profile.jpg")
        temp_image = os.path.join(images_dir, "temp.jpg")

        if os.path.exists(profile_path):
            pixmap = QPixmap(profile_path).scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.picture.setPixmap(pixmap)
        else:
            self.picture.clear()

        if os.path.exists(temp_image):
            try:
                os.remove(temp_image)
            except Exception:
                pass

    def load_record(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Record")
        layout = QFormLayout(dialog)
        tag_input = QLineEdit()
        tag_input.setPlaceholderText("Enter Tag")
        layout.addRow("Tag:", tag_input)
        submit = QPushButton("Submit")
        layout.addRow(submit)

        def load():
            tag = tag_input.text().strip()
            date = datetime.datetime.now().strftime("%d/%m/%Y")
            if not tag:
                QMessageBox.warning(dialog, "Error", "Please enter a tag.")
                return

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE tag=? AND date=?", (tag, date))
                record = cursor.fetchone()
                if record:
                    # record schema: id, tag, name, address, purpose, time_in, time_out, date, picture
                    # your original mapping used different index; adapt accordingly:
                    # Let's map by column names to be safe
                    # But since we used positional columns earlier, we can rely on positions:
                    # [0]=id, [1]=tag, [2]=name, [3]=address, [4]=purpose, [5]=time_in, [6]=time_out, [7]=date, [8]=picture
                    self.tag.setText(str(record[1] or ""))
                    self.name.setText(str(record[2] or ""))
                    self.address.setText(str(record[3] or ""))
                    self.purpose.setText(str(record[4] or ""))
                    self.timein.setText(str(record[5] or ""))
                    self.timeout.setText(str(record[6] or ""))
                    self.date.setText(str(record[7] or ""))
                    if record[8]:
                        pixmap = QPixmap()
                        pixmap.loadFromData(record[8])
                        self.picture.setPixmap(pixmap.scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    else:
                        path = os.path.join(os.path.dirname(__file__), "images", "profile.jpg")
                        if os.path.exists(path):
                            self.picture.setPixmap(QPixmap(path).scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    QMessageBox.warning(dialog, "Not Found", f"No record found for tag: {tag}")
            dialog.close()

        submit.clicked.connect(load)
        dialog.exec_()

    def view(self):
        dialog = QMainWindow(self)
        dialog.setWindowTitle("View logs for today")
        dialog.resize(self.width() - 30, self.height() - 30)

        win = QWidget()
        vbox = QVBoxLayout()

        table = QTableWidget()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            date = datetime.datetime.now().strftime("%d/%m/%Y")
            cursor.execute("SELECT tag, name, address, time_in, purpose, time_out FROM users WHERE date=?", (date,))
            info = cursor.fetchall()

            rows, columns = len(info), 6

            table.setRowCount(rows)
            table.setColumnCount(columns)

            for row_idx, row_val in enumerate(info):
                for col_idx, cell in enumerate(row_val):
                    text = "" if cell is None else str(cell)
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QColor(200, 200, 255))
                    item.setFont(QFont("Consolas"))
                    table.setItem(row_idx, col_idx, item)

            table.setHorizontalHeaderLabels(["Tag", "Name", "Address", "Time In", "Purpose", "Time out"])

        vbox.addWidget(table)
        win.setLayout(vbox)
        dialog.setCentralWidget(win)
        dialog.show()

    def settings(self):
        admin = AdminLogin()
        if admin.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Access Granted", "Welcome, Admin!")
        else:
            QMessageBox.warning(self, "Access Denied", "Invalid credentials.")

    def menu_commands(self, command: QAction):
        if command.text() == "Load Record":
            self.load_record()
        elif command.text() == "Save Record":
            self.save_record()
        elif command.text() == "Toggle Theme":
            self.toggle_theme()
        elif command.text() == "View Table":
            self.view()
        else:
            self.settings()

    # ------------------------------
    # Camera Integration
    # ------------------------------
    def change_camera(self, index: int):
        """
        Slot connected to QComboBox.currentIndexChanged[int].
        Only reopen camera if index changed.
        """
        if index == self.current_camera_index:
            return
        self.current_camera_index = index
        self.close_camera_dialog()
        self.open_camera_dialog(index)

    def open_camera_dialog(self, index: int = 0):
        # create/open dialog
        self.cam_dialog = QDialog(self)
        self.cam_dialog.setWindowTitle("Camera - Snap Profile Photo")
        self.cam_dialog.setFixedSize(480, 380)
        layout = QVBoxLayout(self.cam_dialog)

        self.cam_label = QLabel()
        self.cam_label.setFixedSize(450, 300)
        self.cam_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cam_label)

        btn_hbox = QHBoxLayout()
        snap_btn = QPushButton("Snap")
        self.combo = QComboBox()
        # Populate combo with available cameras
        cam_items = [str(i) for i in available_cameras] if available_cameras else ["0"]
        self.combo.clear()
        self.combo.addItems(cam_items)
        # ensure index bounds
        if index < 0 or index >= len(cam_items):
            index = 0
        self.combo.setCurrentIndex(index)
        # connect specifically to int overload
        self.combo.currentIndexChanged[int].connect(self.change_camera)

        close_btn = QPushButton("Close")
        btn_hbox.addWidget(snap_btn)
        btn_hbox.addWidget(self.combo)
        btn_hbox.addWidget(close_btn)
        layout.addLayout(btn_hbox)

        snap_btn.clicked.connect(self.take_snapshot)
        close_btn.clicked.connect(self.close_camera_dialog)
        self.cam_dialog.closeEvent = lambda a0: self.close_camera_dialog()

        # open camera
        cam_index = int(self.combo.currentText()) if self.combo.count() > 0 else 0
        api_preference = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
        self.cap = cv2.VideoCapture(cam_index, api_preference)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Camera Error", f"Unable to access the camera (index {cam_index}).")
            return

        # start timer to update frames
        self.cam_timer = QTimer()
        self.cam_timer.timeout.connect(self.update_camera_frame)
        self.cam_timer.start(30)

        self.cam_dialog.exec_()

    def update_camera_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return

        frame_rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled = qimg.scaled(self.cam_label.width(), self.cam_label.height(), Qt.KeepAspectRatio)
        self.cam_label.setPixmap(QPixmap.fromImage(scaled))

    def take_snapshot(self):
        if not self.cap:
            QMessageBox.warning(self, "Error", "Camera is not active.")
            return
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.warning(self, "Error", "Failed to capture image.")
            return

        # naive crop/resize (you can integrate a face detector here later)
        face_crop = cv2.resize(cv2.flip(frame, 1), (200, 200))
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(images_dir, exist_ok=True)
        profile_path = os.path.join(images_dir, "temp.jpg")
        cv2.imwrite(profile_path, face_crop)

        pixmap = QPixmap(profile_path).scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.picture.setPixmap(pixmap)
        QMessageBox.information(self, "Saved", "Profile picture updated.")
        self.close_camera_dialog()

    def close_camera_dialog(self):
        try:
            if hasattr(self, "cam_timer") and self.cam_timer is not None and self.cam_timer.isActive():
                self.cam_timer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, "cap") and self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        try:
            if hasattr(self, "cam_dialog"):
                self.cam_dialog.close()
        except Exception:
            pass
        self.cap = None
        self.cam_timer = None

    # ------------------------------
    # UI Setup
    # ------------------------------
    def initUI(self):
        window = QWidget()
        vbox = QVBoxLayout()

        # --- TITLE + LOGO ---
        hbox = QHBoxLayout()
        self.title = QLabel("Access Control System")

        logo = QLabel()
        logo_path = os.path.join("images", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pixmap)
        hbox.addWidget(logo, alignment=Qt.AlignLeft)
        hbox.addWidget(self.title, alignment=Qt.AlignCenter)
        vbox.addLayout(hbox)

        # --- MENU ---
        menu = self.menuBar()
        file = menu.addMenu("File")
        save = QAction("Save Record", self)
        save.setShortcut("Ctrl+S")
        load = QAction("Load Record", self)
        load.setShortcut("Ctrl+L")
        toggle = QAction("Toggle Theme", self)
        toggle.setShortcut("Ctrl+T")
        view = QAction("View Table", self)
        view.setShortcut("Ctrl+V")
        settings_action = QAction("Settings", self)
        file.addAction(save)
        file.addAction(load)
        file.addAction(toggle)
        file.addAction(view)
        file.addSeparator()
        file.addAction(settings_action)
        file.triggered.connect(self.menu_commands)

        # --- FORM ---
        self.form_frame = QFrame()
        self.form_frame.setObjectName("form_frame")
        form = QFormLayout()

        self.tag = QLineEdit()
        self.name = QLineEdit()
        self.address = QLineEdit()
        self.purpose = QLineEdit()
        self.timein = QLineEdit()
        self.timeout = QLineEdit()
        self.date = QLineEdit()
        self.picture = QLabel()

        self.get_time_btn = QPushButton("⏱")
        self.get_time_btn.clicked.connect(lambda: self.get_current_time(1))
        self.get_time_btn2 = QPushButton("⏱")
        self.get_time_btn2.clicked.connect(lambda: self.get_current_time(2))
        self.date_btn = QPushButton("📅")
        self.date_btn.clicked.connect(self.get_current_date)

        self.timein.setReadOnly(True)
        self.timeout.setReadOnly(True)
        self.date.setReadOnly(True)

        picture_hbox = QHBoxLayout()
        profile_path = os.path.join("images", "profile.jpg")
        if os.path.exists(profile_path):
            self.picture.setPixmap(QPixmap(profile_path).scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        picture_hbox.addWidget(self.picture, alignment=Qt.AlignCenter)

        change_btn = QPushButton("Change Photo")
        # open camera with default camera index 0
        change_btn.clicked.connect(lambda: self.open_camera_dialog(0))
        picture_hbox.addWidget(change_btn, alignment=Qt.AlignCenter)

        self.time_in_hbox = QHBoxLayout()
        self.time_in_hbox.addWidget(self.timein)
        self.time_in_hbox.addWidget(self.get_time_btn)

        self.time_out_hbox = QHBoxLayout()
        self.time_out_hbox.addWidget(self.timeout)
        self.time_out_hbox.addWidget(self.get_time_btn2)

        self.date_hbox = QHBoxLayout()
        self.date_hbox.addWidget(self.date)
        self.date_hbox.addWidget(self.date_btn)

        form.addRow(picture_hbox)
        form.addRow("Tag:", self.tag)
        form.addRow("Name:", self.name)
        form.addRow("Address:", self.address)
        form.addRow("Time in:", self.time_in_hbox)
        form.addRow("Purpose:", self.purpose)
        form.addRow("Time out:", self.time_out_hbox)
        form.addRow("Date:", self.date_hbox)

        self.form_frame.setLayout(form)
        vbox.addWidget(self.form_frame)
        vbox.setAlignment(Qt.AlignTop)
        window.setLayout(vbox)
        self.setCentralWidget(window)

    # ------------------------------
    # Themes
    # ------------------------------
    def set_light_theme(self):
        self.title.setStyleSheet("font-size:28px;font-weight:bold;color:black;letter-spacing:2px;")
        self.setStyleSheet("""
            QMainWindow,QDialog{background-color:#f0f0f0;}
            QLabel{font-size:17px;font-weight:500;color:#222;}
            QLineEdit{padding:8px 12px;font-size:16px;border:1px solid #999;border-radius:8px;background:white;color:black;}
            QPushButton{background-color:#0078d7;color:white;border-radius:8px;font-size:16px;padding:6px 12px;}
            QPushButton:hover{background-color:#005fa3;}
            QMenuBar{background-color:#C8E1FA;color:#1E2832;font-size:15px}
            QMenuBar::item::selected{background-color:#C8C8C8;color:#1E1E1E;font-size:15px}
            QMenu{background-color:#C8E1FA;color:#1E2832;font-size:15px}
            QMenu::item::selected{background-color:#C8C8C8;color:#1E1E1E;font-size:15px}
            #form_frame{background-color:#ffffff;border-radius:12px;padding:20px;border:1px solid #ccc;}
                """)

    def set_dark_theme(self):
        self.title.setStyleSheet("font-size:28px;font-weight:bold;color:white;letter-spacing:2px;")
        self.setStyleSheet("""
            QMainWindow,QDialog{background-color:#2A2A2A;}
            QLabel{font-size:17px;font-weight:500;color:white;}
            QLineEdit{padding:8px 12px;font-size:16px;border:1px solid #bdbdbd;border-radius:8px;background:#f7f7f7;}
            QPushButton{background-color:#0078d7;color:white;border-radius:8px;font-size:16px;padding:6px 12px;}
            QPushButton:hover{background-color:#005fa3;}
            QMenuBar{background-color:#1E2832;color:#C8E1FA;font-size:15px}
            QMenuBar::item::selected{background-color:#1E1E1E;color:#C8C8C8;font-size:15px}
            QMenu{background-color:#1E2832;color:#C8E1FA;font-size:15px}
            QMenu::item::selected{background-color:#1E1E1E;color:#C8C8C8;font-size:15px}
            #form_frame{background-color:#1E1E1E;border-radius:12px;padding:20px;border:1px solid #3A3A3A;}
        """)

# ------------------------------
# Run App
# ------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
