from PyQt5.QtWidgets import (
    QLabel, QMainWindow, QPushButton, QApplication, QFormLayout,
    QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QMessageBox, QDialog,
    QFrame, QAction
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QImage
import sys, datetime, sqlite3, os, cv2

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

    # ------------------------------
    # Database and Utility
    # ------------------------------
    def create_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    address TEXT,
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
        name = self.name.text().strip()
        address = self.address.text().strip()
        time_in = self.timein.text().strip()
        time_out = self.timeout.text().strip()
        date = self.date.text().strip()

        if not name or not address or not time_in or not date:
            QMessageBox.warning(self, "Error", "Please fill all required fields.")
            return

        # Load profile image as bytes
        profile_path = os.path.join("images", "temp.jpg")
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
                    cursor.execute("""
                        UPDATE users SET time_out=?, picture=? WHERE name=? AND date=?
                    """, (time_out, picture_data, name, date))
            else:
                cursor.execute("""
                    INSERT INTO users (name, address, time_in, time_out, date, picture)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, address, time_in, time_out, date, picture_data))
            conn.commit()

        QMessageBox.information(self, "Success", "Record saved successfully!")
        self.clear()

    def clear(self):
        self.name.clear()
        self.address.clear()
        self.timein.clear()
        self.timeout.clear()
        self.date.clear()

        images_dir = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(images_dir, exist_ok=True)
        profile_path = os.path.join(images_dir, "profile.jpg")
        temp_image = os.path.join(images_dir, "temp.jpg")

        if os.path.exists(profile_path):
            pixmap = QPixmap(profile_path).scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.picture.setPixmap(pixmap)
        
        if os.path.exists(temp_image):
            os.remove(temp_image)

    def load_record(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Record")
        layout = QFormLayout(dialog)
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter Name")
        layout.addRow("Name:", name_input)
        submit = QPushButton("Submit")
        layout.addRow(submit)

        def load():
            name = name_input.text().strip()
            date = datetime.datetime.now().strftime("%d/%m/%Y")
            if not name:
                QMessageBox.warning(dialog, "Error", "Please enter a name.")
                return

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE name=? AND date=?", (name, date))
                record = cursor.fetchone()
                if record:
                    self.name.setText(record[1])
                    self.address.setText(record[2])
                    self.timein.setText(record[3])
                    self.timeout.setText(record[4])
                    self.date.setText(record[5])
                    if record[6]:
                        pixmap = QPixmap()
                        pixmap.loadFromData(record[6])
                        self.picture.setPixmap(pixmap.scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    QMessageBox.warning(dialog, "Not Found", f"No record found for name: {name}")
            dialog.close()

        submit.clicked.connect(load)
        dialog.exec_()

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
        else:
            self.settings()

    # ------------------------------
    # Camera Integration
    # ------------------------------
    def open_camera_dialog(self):
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
        close_btn = QPushButton("Close")
        btn_hbox.addWidget(snap_btn)
        btn_hbox.addWidget(close_btn)
        layout.addLayout(btn_hbox)

        snap_btn.clicked.connect(self.take_snapshot)
        close_btn.clicked.connect(self.close_camera_dialog)

        self.cap = cv2.VideoCapture(2, cv2.CAP_DSHOW if sys.platform.startswith("win") else 0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Camera Error", "Unable to access the camera.")
            return

        self.cam_timer = QTimer()
        self.cam_timer.timeout.connect(self.update_camera_frame)
        self.cam_timer.start(30)

        # Load face cascade
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        self.cam_dialog.exec_()

    def update_camera_frame(self):
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
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.warning(self, "Error", "Failed to capture image.")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_crop = frame[y:y+h, x:x+w]
        else:
            face_crop = frame  # fallback if no face detected

        face_crop = cv2.resize(face_crop, (200, 200))
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(images_dir, exist_ok=True)
        profile_path = os.path.join(images_dir, "temp.jpg")
        cv2.imwrite(profile_path, face_crop)

        pixmap = QPixmap(profile_path).scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.picture.setPixmap(pixmap)
        QMessageBox.information(self, "Saved", "Profile picture updated.")

    def close_camera_dialog(self):
        try:
            if hasattr(self, "cam_timer") and self.cam_timer.isActive():
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
        settings_action = QAction("Settings", self)
        file.addAction(save)
        file.addAction(load)
        file.addAction(toggle)
        file.addSeparator()
        file.addAction(settings_action)
        file.triggered.connect(self.menu_commands)

        # --- FORM ---
        self.form_frame = QFrame()
        self.form_frame.setObjectName("form_frame")
        form = QFormLayout()

        self.name = QLineEdit()
        self.address = QLineEdit()
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
        change_btn.clicked.connect(self.open_camera_dialog)
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
        form.addRow("Name:", self.name)
        form.addRow("Address:", self.address)
        form.addRow("Time in:", self.time_in_hbox)
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
