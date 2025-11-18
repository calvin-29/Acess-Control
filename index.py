from PyQt5.QtWidgets import (
    QLabel, QMainWindow, QPushButton, QApplication, QFormLayout, QVBoxLayout,
    QHBoxLayout, QWidget, QLineEdit, QMessageBox, QDialog, QFrame, QAction, QTextEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QListWidget, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
import sys
import datetime
import sqlite3
import os
import cv2
import csv
import hashlib

def list_available_cameras(max_index_to_check=6):
    available_cameras = []
    for i in range(max_index_to_check):
        api = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
        cap = cv2.VideoCapture(i, api)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

available_cameras = list_available_cameras()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_appdata_dir():
    COMPANY, APP_NAME = "CruzTech", "Access_Control"
    if sys.platform.startswith("win"):
        local = os.getenv("APPDATA")
        if local:
            base = os.path.join(local, COMPANY, APP_NAME)
        else:
            base = os.path.join(os.path.expanduser("~"), f".{COMPANY.lower()}", APP_NAME)
    else:
        xdg = os.getenv("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
        base = os.path.join(xdg, APP_NAME)
    os.makedirs(base, exist_ok=True)
    return base

class AdminLogin(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Admin Login")
        self.setFixedSize(340, 200)
        layout = QFormLayout(self)

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addRow("Username:", self.username_input)
        layout.addRow("Password:", self.password_input)

        btn_h = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.check_credentials)
        btn_h.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_h.addWidget(self.cancel_btn)

        layout.addRow(btn_h)

    def check_credentials(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password.")
            return

        try:
            with sqlite3.connect(self.parent.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM admins WHERE username=?", (username,))
                row = cursor.fetchone()
                if row and row[0] == hash_password(password):
                    self.accept()
                    return
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Failed to verify credentials:\n{e}")
            return

        QMessageBox.warning(self, "Error", "Invalid credentials.")

class AdminManager(QDialog):
    """
    Simple admin manager: list admins, add admin, delete selected admin.
    Only available to signed-in admins.
    """

    # noinspection PyUnresolvedReferences
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Manage Admins")
        self.resize(420, 300)
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_h = QHBoxLayout()
        self.add_btn = QPushButton("Add Admin")
        self.add_btn.clicked.connect(self.add_admin)
        btn_h.addWidget(self.add_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        btn_h.addWidget(self.delete_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_h.addWidget(self.close_btn)

        layout.addLayout(btn_h)
        self.load_admins()

    def load_admins(self):
        self.list_widget.clear()
        try:
            with sqlite3.connect(self.parent.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username FROM admins ORDER BY username")
                for aid, username in cursor.fetchall():
                    self.list_widget.addItem(f"{aid}: {username}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load admins:\n{e}")

    def add_admin(self):
        username, ok = QInputDialog.getText(self, "New Admin", "Enter username:")
        if not ok or not username.strip():
            return
        password, ok = QInputDialog.getText(self, "New Admin Password", "Enter password:", QLineEdit.Password)
        if not ok or not password:
            return
        try:
            with sqlite3.connect(self.parent.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)",
                               (username.strip(), hash_password(password)))
                conn.commit()
            QMessageBox.information(self, "Added", f"Admin '{username}' added.")
            self.load_admins()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate", "An admin with that username already exists.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add admin:\n{e}")

    def delete_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Select", "Please select an admin to delete.")
            return
        text = item.text()
        aid = int(text.split(":")[0])
        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete admin '{text}'?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                with sqlite3.connect(self.parent.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM admins WHERE id=?", (aid,))
                    conn.commit()
                QMessageBox.information(self, "Deleted", "Admin removed.")
                self.load_admins()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete admin:\n{e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.setWindowTitle("Visitor Login")

        self.setWindowState(Qt.WindowMaximized)

        appdata = get_appdata_dir()
        self.db_path = os.path.join(appdata, "my_db.db")
        self.images_dir = "images"

        icon_path = os.path.join(self.images_dir, "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.create_database()
        self.initUI()
        self.set_dark_theme()

        # camera & session state
        self.cap = None
        self.cam_timer = None
        self.current_camera_index = None
        self.admin = False

    # ------------------------------
    # Database and Utility
    # ------------------------------
    def create_database(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag TEXT,
                        name TEXT,
                        address TEXT,
                        phone TEXT,
                        purpose TEXT,
                        who TEXT,
                        time_in TEXT,
                        time_out TEXT,
                        date TEXT,
                        picture BLOB
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT
                    )
                """)
                cursor.execute("SELECT COUNT(*) FROM admins")
                count = cursor.fetchone()[0]
                if count == 0:
                    cursor.execute("INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)",
                                   ("admin", hash_password("1234")))
                conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to create database:\n{e}")

    def get_current_time(self, mode=None):
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.timeout.setText(current_time)
        self.statusBar().showMessage("Time updated", 2000)

    def get_current_date(self):
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        self.date.setText(current_date)
        self.statusBar().showMessage("Date updated", 2000)

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
        phone = self.phone.text().strip()
        time_in = datetime.datetime.now().strftime("%H:%M:%S")
        purpose = self.purpose.toPlainText().strip()
        who = self.who_to_meet.text().strip()
        time_out = self.timeout.text().strip()
        date = self.date.text().strip()

        if not name or not address or not date or not purpose or not phone or not who:
            QMessageBox.warning(self, "Error", "Please fill all required fields.")
            return

        if len(phone) != 11 or not phone.isnumeric():
            QMessageBox.warning(self, "Error", "Phone number is invalid")
            return

        profile_path = os.path.join(self.images_dir, "temp.jpg")
        picture_data = None
        if os.path.exists(profile_path):
            with open(profile_path, "rb") as f:
                picture_data = f.read()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE date=? AND tag=?", (date, tag))
                record = cursor.fetchone()

                if record:
                    reply = QMessageBox.question(self, "Confirm", f"Update profile for {name}?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        cursor.execute(
                            "UPDATE users SET time_out=?, picture=? WHERE name=? AND date=?",
                            (time_out, picture_data, name, date)
                        )
                else:
                    normalized_tag = tag.rjust(3, '0') if tag else None
                    cursor.execute(
                        """INSERT INTO users (tag, name, address, phone, time_in, purpose, who, time_out, date, picture) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (normalized_tag, name, address, phone, time_in, purpose, who, time_out, date, picture_data)
                    )
                conn.commit()
            self.clear()
            QMessageBox.information(self, "Success", "Record saved successfully!")
            self.statusBar().showMessage("Record saved", 3000)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Failed to save record:\n{e}")

    def clear(self):
        self.tag.clear()
        self.name.clear()
        self.address.clear()
        self.phone.clear()
        self.purpose.clear()
        self.who_to_meet.clear()
        self.timeout.clear()
        self.date.clear()

        profile_path = os.path.join(self.images_dir, "profile.jpg")
        temp_image = os.path.join(self.images_dir, "temp.jpg")

        if os.path.exists(profile_path):
            pixmap = QPixmap(profile_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.picture.setPixmap(pixmap)
        else:
            self.picture.clear()

        if os.path.exists(temp_image):
            try:
                os.remove(temp_image)
            except FileNotFoundError as e:
                pass

    def closeEvent(self, a0):
        self.clear()

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

            normalized = tag.rjust(3, '0')
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE tag=? AND date=?", (normalized, date))
                    record = cursor.fetchone()
                    if record:
                        self.tag.setText(str(record[1] or ""))
                        self.name.setText(str(record[2] or ""))
                        self.address.setText(str(record[3] or ""))
                        self.phone.setText(str(record[4] or ""))
                        self.purpose.setText(str(record[5] or ""))
                        self.who_to_meet.setText(str(record[6] or ""))
                        self.timeout.setText(str(record[8] or ""))
                        self.date.setText(str(record[9] or ""))
                        if record[10]:
                            pixmap = QPixmap()
                            pixmap.loadFromData(record[10])
                            self.picture.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        else:
                            path = os.path.join(self.images_dir, "profile.jpg")
                            if os.path.exists(path):
                                self.picture.setPixmap(
                                    QPixmap(path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    else:
                        QMessageBox.warning(dialog, "Not Found", f"No record found for tag: {tag}")
            except Exception as e:
                QMessageBox.critical(dialog, "DB Error", f"Failed to load record:\n{e}")
            dialog.close()

        submit.clicked.connect(load)
        dialog.exec_()

    def export(self, type_of):
        file_path = os.path.join(os.path.expanduser("~"), "Documents", f"access_records.{type_of}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT tag, name, address, phone, purpose, who, time_in, time_out, date, picture FROM users")
                info = cursor.fetchall()
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to read records:\n{e}")
            return

        try:
            if type_of == "csv":
                with open(file_path, "w", encoding="utf-8", newline='') as e:
                    writer = csv.writer(e)
                    writer.writerow(["tag", "name", "address", "phone", "purpose", "who_to_meet", "time_in", "time_out", "date"])
                    for row in info:
                        writer.writerow(row[1:-1])
            elif type_of == "html":
                os.system(f'html_converter.py "{file_path}" "{info}"')
            elif type_of == "pdf":
                os.system(f'pdf_converter.py "{file_path}" "{info}"')

            else:
                QMessageBox.warning(self, "Unknown type", f"Unknown export type: {type_of}")
                return
            msgbox = QMessageBox(self)
            msgbox.setWindowTitle("File saved successfully")
            msgbox.setText(f"File is saved at {file_path}")
            open_btn = msgbox.addButton("Show in folder", QMessageBox.ActionRole)
            ok_btn = msgbox.addButton(QMessageBox.Ok)

            def reveal():
                try:
                    if sys.platform.startswith("win"):
                        os.startfile(os.path.split(file_path)[0])
                    elif sys.platform.startswith("darwin"):
                        os.system(f'open "{os.path.split(file_path)[0]}"')
                    else:
                        os.system(f'xdg-open "{os.path.split(file_path)[0]}"')
                except Exception:
                    pass

            open_btn.clicked.connect(reveal)
            msgbox.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{e}")

    def view(self):
        if self.admin:
            dialog = QMainWindow(self)
            dialog.setWindowTitle("View Logs")
            dialog.resize(self.width(), self.height()-30)

            menu = dialog.menuBar()
            file = menu.addMenu("File")
            export = file.addMenu("Export")
            export.addAction("Export to csv").triggered.connect(lambda: self.export("csv"))
            export.addAction("Export to html").triggered.connect(lambda: self.export("html"))
            export.addAction("Export to pdf").triggered.connect(lambda: self.export("pdf"))

            win = QWidget()
            vbox = QVBoxLayout()

            search_box = QHBoxLayout()
            search_label = QLabel("🔍 Search:")
            search_input = QLineEdit()
            search_input.setPlaceholderText("Type to search by tag, name, address, or date...")
            search_box.addWidget(search_label)
            search_box.addWidget(search_input)
            vbox.addLayout(search_box)

            table = QTableWidget()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT tag, name, address, phone, purpose, who, time_in, time_out, date FROM users ORDER BY date DESC, time_in DESC")
                info = cursor.fetchall()

                rows, columns = len(info), 9
                table.setRowCount(rows)
                table.setColumnCount(columns)
                table.setStyleSheet("background-color: rgb(200, 200, 200);")
                for row_idx, row_val in enumerate(info):
                    for col_idx, cell in enumerate(row_val):
                        text = "" if cell is None else str(cell)
                        item = QTableWidgetItem(text)
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFont(QFont("Consolas", 10))
                        table.setItem(row_idx, col_idx, item)

                table.setHorizontalHeaderLabels(["Tag", "Name", "Address", "Phone Number", "Purpose", "Who to meet", "Time In",  "Time Out", "Date"])
                header = table.horizontalHeader()
                header.setSectionResizeMode(QHeaderView.Stretch)

            vbox.addWidget(table)
            win.setLayout(vbox)
            dialog.setCentralWidget(win)

            def filter_table():
                filter_text = search_input.text().strip().lower()
                for row in range(table.rowCount()):
                    match = False
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item and filter_text in item.text().lower():
                            match = True
                            break
                    table.setRowHidden(row, not match)

            search_input.textChanged.connect(filter_table)
            dialog.show()
        else:
            QMessageBox.information(self, "Not admin", "You are not the admin")

    def settings(self):
        admin = AdminLogin(self)
        if admin.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Access Granted", "Welcome, Admin!")
            self.admin = True
            self.statusBar().showMessage("Signed in as admin", 3000)
        else:
            QMessageBox.warning(self, "Access Denied", "Invalid credentials.")

    def open_admin_manager(self):
        if not self.admin:
            QMessageBox.information(self, "Not admin", "You must sign in first.")
            return
        mgr = AdminManager(self)
        mgr.exec_()

    def menu_commands(self, command: QAction):
        text = command.text()
        if text == "Load Record":
            self.load_record()
        elif text == "Save Record":
            self.save_record()
        elif text == "Toggle Theme":
            self.toggle_theme()
        elif text == "View Table":
            self.view()
        elif text == "Clear All":
            self.clear()
        elif text == "Clear Date":
            self.date.clear()
        elif text == "Clear Timeout":
            self.timeout.clear()
        elif text == "Sign In / Admin Manager":
            # Sign in if not, else open admin manager
            if self.admin:
                self.open_admin_manager()
            else:
                self.settings()
        elif text == "Logout":
            if self.admin:
                self.admin = False
                QMessageBox.information(self, "Logged out", "You have logged out successfully.")
                self.statusBar().showMessage("Signed out", 3000)
            else:
                QMessageBox.information(self, "Info", "You are not logged in.")
        else:
            # fallback
            self.settings()

    # ------------------------------
    # Camera Integration (with face detection)
    # ------------------------------
    def change_camera(self, index: int):
        if index == self.current_camera_index:
            return
        self.current_camera_index = index
        self.close_camera_dialog()
        self.open_camera_dialog(index)

    def open_camera_dialog(self, index: int = 0):
        self.cam_dialog = QDialog(self)
        self.cam_dialog.setWindowTitle("Camera - Snap Profile Photo")
        self.cam_dialog.setFixedSize(520, 420)
        layout = QVBoxLayout(self.cam_dialog)

        self.cam_label = QLabel()
        self.cam_label.setFixedSize(480, 320)
        self.cam_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cam_label)

        btn_hbox = QHBoxLayout()
        snap_btn = QPushButton("Snap")
        self.combo = QComboBox()

        cam_items = [str(i) for i in available_cameras] if available_cameras else ["0"]
        self.combo.clear()
        self.combo.addItems(cam_items)

        if index < 0 or index >= len(cam_items):
            index = 0
        self.combo.setCurrentIndex(index)
        self.combo.currentIndexChanged[int].connect(self.change_camera)

        close_btn = QPushButton("Close")
        btn_hbox.addWidget(snap_btn)
        btn_hbox.addWidget(self.combo)
        btn_hbox.addWidget(close_btn)
        layout.addLayout(btn_hbox)

        snap_btn.clicked.connect(self.take_snapshot)
        close_btn.clicked.connect(self.close_camera_dialog)
        self.cam_dialog.closeEvent = lambda a0: self.close_camera_dialog()

        try:
            cam_index = int(self.combo.currentText()) if self.combo.count() > 0 else 0
        except ValueError:
            cam_index = 0

        api_preference = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
        self.close_camera_dialog()
        self.cap = cv2.VideoCapture(cam_index, api_preference)
        if not self.cap or not self.cap.isOpened():
            QMessageBox.critical(self, "Camera Error", f"Unable to access the camera (index {cam_index}).")
            self.cap = None
            return

        self.cam_timer = QTimer()
        self.cam_timer.timeout.connect(self.update_camera_frame)
        self.cam_timer.start(30)

        self.cam_dialog.exec_()

    def update_camera_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return
        try:
            frame_rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            scaled = qimg.scaled(self.cam_label.width(), self.cam_label.height(), Qt.KeepAspectRatio)
            self.cam_label.setPixmap(QPixmap.fromImage(scaled))
        except Exception:
            pass

    def take_snapshot(self):
        if not self.cap:
            QMessageBox.warning(self, "Error", "Camera is not active.")
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            QMessageBox.warning(self, "Error", "Failed to capture image.")
            return

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                # pick the largest face (best guess)
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                (x, y, w, h) = faces[0]
                # expand bounding box slightly but stay within image
                pad = int(0.15 * max(w, h))
                x0 = max(0, x - pad)
                y0 = max(0, y - pad)
                x1 = min(frame.shape[1], x + w + pad)
                y1 = min(frame.shape[0], y + h + pad)
                face_crop = frame[y0:y1, x0:x1]
            else:
                # fallback: center crop area
                h_f, w_f = frame.shape[:2]
                min_side = min(h_f, w_f)
                cx, cy = w_f // 2, h_f // 2
                half = min_side // 3
                face_crop = frame[max(0, cy - half):min(h_f, cy + half), max(0, cx - half):min(w_f, cx + half)]

            face_crop = cv2.resize(cv2.flip(face_crop, 1), (200, 200))
            profile_path = os.path.join(self.images_dir, "temp.jpg")
            cv2.imwrite(profile_path, face_crop)

            pixmap = QPixmap(profile_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.picture.setPixmap(pixmap)
            QMessageBox.information(self, "Saved", "Profile picture updated.")
            self.statusBar().showMessage("Profile picture updated", 2000)
        except Exception as e:
            QMessageBox.critical(self, "Capture Error", f"Failed to save captured image:\n{e}")
        finally:
            self.close_camera_dialog()

    def close_camera_dialog(self):
        try:
            if hasattr(self, "cam_timer") and self.cam_timer is not None and self.cam_timer.isActive():
                self.cam_timer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, "cap") and self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if hasattr(self, "cam_dialog") and self.cam_dialog is not None:
                try:
                    self.cam_dialog.close()
                except Exception:
                    pass
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

        # Title + logo
        hbox = QHBoxLayout()
        self.title = QLabel("Access Control System")
        self.title.setFont(QFont("Segoe UI", 30, QFont.Bold))
        logo = QLabel()
        logo_path = os.path.join(self.images_dir, "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pixmap)
        hbox.addWidget(logo, alignment=Qt.AlignLeft)
        hbox.addWidget(self.title, alignment=Qt.AlignCenter)
        hbox.addStretch()
        vbox.addLayout(hbox)

        # Menu
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
        settings_action = QAction("Sign In / Admin Manager", self)
        logout_action = QAction("Logout", self)
        file.addAction(save)
        file.addAction(load)
        file.addAction(toggle)
        file.addAction(view)
        file.addSeparator()
        file.addAction(settings_action)
        file.addAction(logout_action)
        file.triggered.connect(self.menu_commands)

        edit = menu.addMenu("Edit")
        edit.addAction("Clear All")
        edit.addAction("Clear Date")
        edit.addAction("Clear Timeout")
        edit.triggered.connect(self.menu_commands)

        self.form_frame = QFrame()
        self.form_frame.setObjectName("form_frame")

        form = QFormLayout()
        form.setSpacing(10)

        self.tag = QLineEdit()
        self.name = QLineEdit()
        self.address = QLineEdit()
        self.purpose = QTextEdit()
        self.who_to_meet = QLineEdit()
        self.phone = QLineEdit()
        self.timeout = QLineEdit()
        self.date = QLineEdit()
        self.picture = QLabel()

        self.tag.setPlaceholderText("001")
        self.name.setPlaceholderText("Emmanuel Eze")
        self.address.setPlaceholderText("Gwarinpa")
        self.purpose.setPlaceholderText("To Code")
        self.who_to_meet.setPlaceholderText("The manager")
        self.phone.setPlaceholderText("09123456789")
        self.picture.setStyleSheet("border: 3px solid blue; border-radius:10px")

        self.get_time_btn2 = QPushButton("⏱")
        self.get_time_btn2.setToolTip("Set current time")
        self.get_time_btn2.clicked.connect(lambda: self.get_current_time(2))
        self.date_btn = QPushButton("📅")
        self.date_btn.setToolTip("Set current date")
        self.date_btn.clicked.connect(self.get_current_date)

        self.timeout.setReadOnly(True)
        self.date.setReadOnly(True)

        picture_hbox = QHBoxLayout()
        picture_hbox.setAlignment(Qt.AlignCenter)
        profile_path = os.path.join(self.images_dir, "profile.jpg")
        if os.path.exists(profile_path):
            self.picture.setPixmap(QPixmap(profile_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        picture_hbox.addWidget(self.picture)

        change_btn = QPushButton("Change Photo")
        change_btn.clicked.connect(lambda: self.open_camera_dialog(0))
        picture_hbox.addWidget(change_btn)

        self.time_out_hbox = QHBoxLayout()
        self.time_out_hbox.addWidget(self.timeout)
        self.time_out_hbox.addWidget(self.get_time_btn2)

        self.date_hbox = QHBoxLayout()
        self.date_hbox.addWidget(self.date)
        self.date_hbox.addWidget(self.date_btn)

        form.addRow(picture_hbox)
        form_hbox = QHBoxLayout()

        form.addRow(QLabel(""))

        # ---first column---
        first_col = QFormLayout()
        first_col.addRow("Tag:", self.tag)
        first_col.addRow("Name:", self.name)
        first_col.addRow("Address:", self.address)

        # -----second column-----
        second_col = QFormLayout()
        second_col.addRow("Phone number:", self.phone)
        second_col.addRow("Time out:", self.time_out_hbox)
        second_col.addRow("Date:", self.date_hbox)

        form_hbox.addLayout(first_col)
        form_hbox.addSpacing(50)
        form_hbox.addLayout(second_col)

        form.addRow(form_hbox)
        form.addRow("Who to meet:", self.who_to_meet)
        form.addRow("Purpose:", self.purpose)

        btn = QPushButton("Submit")
        btn.clicked.connect(self.save_record)
        btn.setFont(QFont("Segeo UI", 13, QFont.Bold))

        btn.setFixedWidth(300)
        form.addRow(btn)

        self.form_frame.setLayout(form)
        vbox.addWidget(self.form_frame)
        window.setLayout(vbox)
        self.setCentralWidget(window)

    # ------------------------------
    # Themes
    # ------------------------------
    def set_light_theme(self):
        self.title.setStyleSheet("font-size:20px;font-weight:700;color:#222;letter-spacing:1px;")
        self.setStyleSheet("""
            QMainWindow,QDialog{background-color:rgb(235, 235, 200);}
            QLabel{font-size:14px;color:#222;}
            QLineEdit, QTextEdit{padding:8px 10px;font-size:14px;border:1px solid #bdbdbd;border-radius:6px;background:white;color:black;}
            QPushButton{background-color:#0078d7;color:white;border-radius:8px;font-size:14px;padding:6px 10px;}
            QPushButton:hover{background-color:#005fa3;}
            QMenuBar, QMenu{background-color:#e9f2ff;color:#1E2832;font-size:13px}
            QMenuBar::item::selected, QMenu::item::selected{background-color:#e9f2df;color:#1E2812;}
            QComboBox{background-color:#0078d7;color:white;font-size:13px}
            #form_frame{background-color:#ffffff;border-radius:10px;padding:16px;border:1px solid #e1e1e1;}
        """)

    def set_dark_theme(self):
        self.title.setStyleSheet("font-size:20px;font-weight:700;color:white;letter-spacing:1px;")
        self.setStyleSheet("""
            QMainWindow,QDialog{background-color:rgb(20, 20, 50);}
            QLabel{font-size:16px;font-weight:400;font-family:"Segoe UI";color:white;margin:0px 0px 5px 0px}
            QLineEdit, QTextEdit{padding:8px 10px;font-size:16px;border:1px solid #555;border-radius:6px;background:rgb(20, 20, 40);color:white;;margin:0px 0px 5px 0px}
            QPushButton{background-color:#0078d7;color:white;border-radius:8px;font-size:14px;padding:6px 10px;}
            QPushButton:hover{background-color:#005fa3;}
            QMenuBar, QMenu{background-color:#1E2832;color:#C8E1FA;font-size:15px}
            QMenuBar::item::selected, QMenu::item::selected{background-color:#1E2842;color:#C8E1EA}
            QComboBox{background-color:#0078d7;color:white;font-size:13px}
            #form_frame{background-color:rgb(20, 20, 45);border-radius:10px;padding:16px;border:1px solid #333;}
        """)


# ------------------------------
# Run App
# ------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
