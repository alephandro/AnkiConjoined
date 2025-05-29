import os
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFormLayout,
    QCheckBox, QSettings
)
from .auth_manager import AuthManager


class LoginDialog(QDialog):
    """Dialog for user authentication with the sync server."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login to Anki Sync Server")
        self.setMinimumWidth(300)

        self.addon_dir = os.path.dirname(os.path.abspath(__file__))

        self.auth_manager = AuthManager(self.addon_dir)

        self.settings = QSettings("AnkiConjoined", "CardSync")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        saved_username = self.settings.value("saved_username", "")
        self.username_edit.setText(saved_username)
        form_layout.addRow("Username:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)

        self.remember_checkbox = QCheckBox("Remember username")
        self.remember_checkbox.setChecked(bool(saved_username))

        server_url = self.settings.value("web_url", "http://127.0.0.1:8000")
        self.server_info = QLabel(f"Server: {server_url}")
        self.server_info.setStyleSheet("color: gray; font-size: 10px;")

        layout.addLayout(form_layout)
        layout.addWidget(self.remember_checkbox)
        layout.addWidget(self.server_info)

        button_layout = QHBoxLayout()

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.try_login)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.auth_success = False

    def try_login(self):
        """Attempt to log in to the server."""
        username = self.username_edit.text()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return

        if self.remember_checkbox.isChecked():
            self.settings.setValue("saved_username", username)
        else:
            self.settings.remove("saved_username")

        success, message = self.auth_manager.authenticate(username, password)

        if success:
            self.auth_success = True
            QMessageBox.information(self, "Success", f"Welcome, {username}!")
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", message)

    @staticmethod
    def get_credentials(parent=None):
        """Static method to create the dialog and run it."""
        dialog = LoginDialog(parent)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted and dialog.auth_success:
            return True
        return False