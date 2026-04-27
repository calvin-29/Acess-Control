# File to handle the admin priviledges
from PyQt5.QtWidgets import (
    QPushButton, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, 
    QDialog, QVBoxLayout, QInputDialog, QListWidget
)
import sqlite3
import hashlib
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8"), salt) 

class AdminLogin(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.setWindowTitle("Admin Login")
        self.setMinimumSize(340, 180)
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
            with self.app.get_resources("db", self.app.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM admins WHERE username=?", (username,))
                row = cursor.fetchone()
                if row:
                    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")
                    if bcrypt.checkpw(password_hash, hash_password(password)):
                        self.accept()
                        return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "DB Error", f"Failed to verify credentials:\n{e}")
            return

        QMessageBox.warning(self, "Error", "Invalid credentials.")

class AdminManager(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
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
            with self.app.get_resources("db", self.app.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username FROM admins ORDER BY username")
                for aid, username in cursor.fetchall():
                    self.list_widget.addItem(f"{aid}: {username}")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load admins:\n{e}")

    def add_admin(self):
        username, ok = QInputDialog.getText(self, "New Admin", "Enter username:")
        if not ok or not username.strip():
            return
        password, ok = QInputDialog.getText(self, "New Admin Password", "Enter password:", QLineEdit.Password)
        if not ok or not password:
            return
        try:
            with self.app.get_resources("db", self.app.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)",
                            (username.strip(), hash_password(password)))
                conn.commit()
            QMessageBox.information(self, "Added", f"Admin '{username}' added.")
            self.load_admins()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate", "An admin with that username already exists.")
        except sqlite3.Error as e:
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
                with self.app.get_resources("db", self.app.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM admins WHERE id=?", (aid,))
                    conn.commit()
                QMessageBox.information(self, "Deleted", "Admin removed.")
                self.load_admins()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to delete admin:\n{e}")

