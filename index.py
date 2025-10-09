from PyQt5.QtWidgets import (
    QLabel, QMainWindow, QPushButton, QApplication, QFormLayout,
    QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QMessageBox, QDialog,
    QFrame, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import sys, datetime, sqlite3, os

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

        # Simple hardcoded login (customize this)
        if username == "admin" and password == "1234":
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Window Settings ---
        self.setWindowTitle("Access Control Management System")
        self.setGeometry(100, 100, 600, 400)

        # --- Initialization ---
        self.create_database()  # Create SQLite DB if not exists
        self.initUI()           # Setup UI elements
        self.set_dark_theme()       # Apply custom stylesheet

    # ------------------------------
    # Utility Functions
    # ------------------------------
    def get_current_time(self, mode):
        """Set current system time into Time In field"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if mode == 1:
            self.timein.setText(current_time)
        else:
            self.timeout.setText(current_time)

    def get_current_date(self):
        """Set current system date into date field"""
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        self.date.setText(current_date)
    
    def toggle_theme(self):
        if hasattr(self, 'dark_mode') and self.dark_mode:
            self.dark_mode = False
            self.set_light_theme()
        else:
            self.dark_mode = True
            self.set_dark_theme()

    def create_database(self):
        """Create SQLite database and users table if not exists"""
        with sqlite3.connect("my_db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    address TEXT,
                    time_in TEXT,
                    time_out TEXT,
                    date TEXT
                )
            """)
            conn.commit()

    def save_record(self):
        """Save user input into database"""
        name = self.name.text().strip()
        address = self.address.text().strip()
        time_in = self.timein.text().strip()
        time_out = self.timeout.text().strip()
        date = self.date.text().strip()
        info = (name, address, time_in, date)

        # Validation
        if not name or not address or not time_in or not date:
            QMessageBox.warning(self, "Error", "Please fill all required fields.")
            return

        # Insert into DB
        with sqlite3.connect("my_db.db") as conn:
            cursor = conn.cursor()
            # Check if record exists for the given name and date
            cursor.execute("SELECT * FROM users WHERE name=? AND date=?", (name, date))
            record = cursor.fetchone()

            if record:
                # Update time_out for existing record
                cursor.execute("""
                    UPDATE users 
                    SET time_out=? 
                    WHERE name=? AND date=?
                """, (time_out, name, date))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO users (name, address, time_in, time_out, date)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, address, time_in, time_out, date))

            conn.commit()


        QMessageBox.information(self, "Success", "Record saved successfully!")
        self.clear()

    def clear(self):
        # Clear fields
        self.name.clear()
        self.address.clear()
        self.timein.clear()
        self.timeout.clear()
        self.date.clear()

    def load_record(self):
        """Dialog to update an existing record's timeout."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Record")

        layout = QFormLayout(dialog)

        # --- User name input ---
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter Name")
        layout.addRow("Name:", name_input)

        # --- Submit Button ---
        submit = QPushButton("Submit")
        layout.addRow(submit) 

        def load():
            name = name_input.text().strip()

            if not name:
                QMessageBox.warning(dialog, "Error", "Please fill all fields.")
                return

            with sqlite3.connect("my_db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE name=?", (name,))
                record = cursor.fetchone()
                if record:
                    self.name.setText(record[1])
                    self.address.setText(record[2])
                    self.timein.setText(record[3])
                    self.timeout.setText(record[4])
                    self.date.setText(record[5])
                else:
                    QMessageBox.warning(dialog, "Not Found", f"No record found for name: {name}")
            
            dialog.close()
        
        submit.clicked.connect(load)
        dialog.exec_()

    def settings(self):
        """Dialog for access control settings"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Access Settings")

        layout = QVBoxLayout(dialog)
        label = QLabel("Settings Page — (Add controls or configuration options here)")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec_()

    def menu_commands(self, command: QAction):
        """Handles menu item selections"""
        if command.text() == "Load Record":
            self.load_record()
        elif command.text() == "Save Record":
            self.save_record()
        elif command.text() == "Toggle Theme":
            self.toggle_theme()
        else:
            self.settings()

    # ------------------------------
    # UI Setup
    # ------------------------------
    def initUI(self):
        """Initialize main window layout and widgets"""
        window = QWidget()
        vbox = QVBoxLayout()

        # --- TITLE + LOGO SECTION ---
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

        # --- MENU SECTION ---
        menu = self.menuBar()
        file = menu.addMenu("File")

        save = QAction(QIcon(os.path.join("images", "save.png")), "Save Record", self)
        save.setShortcut("Ctrl+S")

        load = QAction(QIcon(os.path.join("images", "update.png")), "Load Record", self)
        load.setShortcut("Ctrl+U")

        toggle = QAction("Toggle Theme", self)
        toggle.setShortcut("Ctrl+T")

        settings_action = QAction(QIcon(os.path.join("images", "settings.png")), "Settings", self)

        file.addAction(save)
        file.addAction(load)
        file.addAction(toggle)
        file.addSeparator()
        file.addAction(settings_action)
        file.triggered.connect(self.menu_commands)

        # --- FORM SECTION ---
        self.form_frame = QFrame()
        self.form_frame.setObjectName("form_frame")

        form = QFormLayout()

        self.name = QLineEdit()
        self.address = QLineEdit()
        self.timein = QLineEdit()
        self.timeout = QLineEdit()
        self.date = QLineEdit()
        self.picture = QLabel()

        # Buttons for time/date
        self.get_time_btn = QPushButton("⏱")
        self.get_time_btn.clicked.connect(lambda: self.get_current_time(1))
        self.get_time_btn2 = QPushButton("⏱")
        self.get_time_btn2.clicked.connect(lambda: self.get_current_time(2))
        self.date_btn = QPushButton("📅")
        self.date_btn.clicked.connect(self.get_current_date)

        self.timein.setReadOnly(True)
        self.timeout.setReadOnly(True)
        self.date.setReadOnly(True)

        # Profile Picture Placeholder
        picture_hbox = QHBoxLayout()
        profile_path = os.path.join("images", "profile.jpg")
        if os.path.exists(profile_path):
            self.picture.setPixmap(QPixmap(profile_path).scaled(100, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        picture_hbox.addWidget(self.picture, alignment=Qt.AlignCenter)

        # Time + Date Layouts
        self.time_in_hbox = QHBoxLayout()
        self.time_in_hbox.addWidget(self.timein)
        self.time_in_hbox.addWidget(self.get_time_btn)

        self.time_out_hbox = QHBoxLayout()
        self.time_out_hbox.addWidget(self.timeout)
        self.time_out_hbox.addWidget(self.get_time_btn2)

        self.date_hbox = QHBoxLayout()
        self.date_hbox.addWidget(self.date)
        self.date_hbox.addWidget(self.date_btn)

        # Add all to form
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
    
    def set_light_theme(self):
        """Apply application stylesheet"""
        self.title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: black;
            letter-spacing: 2px;
        """)
        self.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 17px;
                font-weight: 500;
                color: #222;
            }
            QLineEdit {
                padding: 8px 12px;
                font-size: 16px;
                border: 1px solid #999;
                border-radius: 8px;
                background: white;
                color: black;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            #form_frame {
                background-color: #ffffff;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #ccc;
            }
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #aaa;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #cce4ff;
            }
            QMenuBar {
                font-size: 14px;
                color: black;
                background-color: #e0e0e0;
            }
        """)

    def set_dark_theme(self):
        """Apply application stylesheet"""
        self.title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
            letter-spacing: 2px;
        """)

        self.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #2A2A2A;
            }
            QLabel {
                font-size: 17px;
                font-weight: 500;
                color: white;
            }
            QLineEdit {
                padding: 8px 12px;
                font-size: 16px;
                border: 1px solid #bdbdbd;
                border-radius: 8px;
                background: #f7f7f7;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            #form_frame{
                background-color: #1E1E1E;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #3A3A3A;
            }
            QMenu {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 5px 15px;
                background-color: transparent;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #4a90d9;
                border-radius: 3px;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 5px 0;
            }
            QMenuBar {
                font-size: 14px;
                color: white;
                background-color: black;
            }
            QMenuBar::item:selected {
                color: #2A2A2A
            }
        """)


# ------------------------------
# Main Entry Point
# ------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
