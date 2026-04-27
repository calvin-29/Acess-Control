from PyQt5.QtWidgets import (
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QDialog, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon
import os
import cv2
import sys

# ------------------------------
# Camera Integration
# ------------------------------

class Camera:
    def __init__(self, app, available_cameras):
        self.app = app
        self.available_cameras = available_cameras

    def change_camera(self, index):
        if index == self.app.current_camera_index:
            return
        self.app.current_camera_index = index
        self.close_camera_dialog()
        self.open_camera_dialog(index)

    def open_camera_dialog(self, index=0):
        self.app.config_data["camera"] = index if index in self.available_cameras else 0
        self.app.save()

        self.cam_dialog = QDialog(self.app)
        self.cam_dialog.setWindowTitle("Camera - Snap Profile Photo")
        self.cam_dialog.setMinimumSize(520, 420)
        layout = QVBoxLayout(self.cam_dialog)

        self.cam_label = QLabel()
        self.cam_label.setMinimumSize(500, 320)
        self.cam_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cam_label)

        btn_hbox = QHBoxLayout()
        snap_icon = self.app.get_resources("images", "camera.svg")
        snap_btn = QPushButton()
        snap_btn.setIconSize(QSize(24, 24))
        if os.path.exists(snap_icon):
            snap_btn.setIcon(QIcon(snap_icon))
        self.combo = QComboBox()

        cam_items = [str(i) for i in self.available_cameras] if self.available_cameras else ["0"]
        self.combo.clear()
        self.combo.addItems(cam_items)

        if index < 0 or index >= len(cam_items):
            index = 0
        self.combo.setCurrentIndex(index)
        self.combo.currentIndexChanged[int].connect(self.change_camera)

        cancel_icon = self.app.get_resources("images", "cancel.svg")
        close_btn = QPushButton()
        close_btn.setIconSize(QSize(24, 24))
        if os.path.exists(cancel_icon):
            close_btn.setIcon(QIcon(cancel_icon))
        btn_hbox.addWidget(snap_btn)
        btn_hbox.addWidget(self.combo)
        btn_hbox.addWidget(close_btn)
        layout.addLayout(btn_hbox)

        snap_btn.clicked.connect(self.take_snapshot)
        close_btn.clicked.connect(self.close_camera_dialog)
        self.cam_dialog.closeEvent = lambda a0: self.close_camera_dialog()
        self.cam_dialog.finished.connect(self.close_camera_dialog)

        try:
            cam_index = int(self.combo.currentText()) if self.combo.count() > 0 else 0
        except ValueError:
            cam_index = 0

        api_preference = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
        self.cap = cv2.VideoCapture(cam_index, api_preference)
        if not self.cap or not self.cap.isOpened():
            QMessageBox.critical(self.app, "Camera Error", f"Unable to access the camera (index {cam_index}).")
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
            QMessageBox.warning(self.app, "Error", "Camera is not active.")
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            QMessageBox.warning(self.app, "Error", "Failed to capture image.")
            return

        try:
            face_crop = cv2.resize(cv2.flip(frame, 1), (200, 200))
            profile_path = self.app.get_resources("images", "temp.jpg")
            cv2.imwrite(profile_path, face_crop)

            check = QDialog(self.app)
            check.setWindowTitle("Is the pic good")

            vbox = QVBoxLayout()
            pixmap = QPixmap(profile_path).scaled(350, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl = QLabel(pixmap=pixmap)
            vbox.addWidget(lbl)

            def accept():
                pixmap = QPixmap(profile_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.app.picture.setPixmap(pixmap)
                QMessageBox.information(self.app, "Saved", "Profile picture updated.")
                check.close()
                self.close_camera_dialog()
                self.app.statusBar().showMessage("Profile picture updated", 2000)
            def reject():
                check.close()

            hbox = QHBoxLayout()

            good_icon = self.app.get_resources("images", "check.svg")
            good = QPushButton(icon=QIcon(good_icon), text="")
            good.clicked.connect(accept)
            good.setToolTip("Accept")
            hbox.addWidget(good)

            bad_icon = self.app.get_resources("images", "x.svg")
            bad = QPushButton(icon=QIcon(bad_icon), text="")
            bad.clicked.connect(reject)
            bad.setToolTip("Retake")
            hbox.addWidget(bad)
            
            vbox.addLayout(hbox)
            check.setLayout(vbox)
            check.exec_()
        except Exception as e:
            QMessageBox.critical(self.app, "Capture Error", f"Failed to save captured image:\n{e}")
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
