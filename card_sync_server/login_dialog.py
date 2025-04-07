import requests
import json
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFormLayout,
    QCheckBox, QSettings
)


class LoginDialog(QDialog):
    """Dialog for user authentication with the sync server."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login to Anki Sync Server")
        self.setMinimumWidth(300)

        # Settings for remembering username
        self.settings = QSettings("AnkiConjoined", "CardSync")

        # Create layout
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Username field
        self.username_edit = QLineEdit()
        saved_username = self.settings.value("username", "")
        self.username_edit.setText(saved_username)
        form_layout.addRow("Username:", self.username_edit)

        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)

        # Remember username checkbox
        self.remember_checkbox = QCheckBox("Remember username")
        self.remember_checkbox.setChecked(bool(saved_username))

        # Add form to main layout
        layout.addLayout(form_layout)
        layout.addWidget(self.remember_checkbox)

        # Buttons layout
        button_layout = QHBoxLayout()

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.try_login)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        # Add buttons to button layout
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)

        # Add button layout to main layout
        layout.addLayout(button_layout)

        # Set layout for dialog
        self.setLayout(layout)

        # Server URL - would come from config
        self.server_url = "http://127.0.0.1:8000"  # Default Django development server

        # Connection result
        self.auth_token = None
        self.authenticated_username = None

    def try_login(self):
        """Attempt to log in to the server."""
        username = self.username_edit.text()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return

        try:
            # Save username if remember is checked
            if self.remember_checkbox.isChecked():
                self.settings.setValue("username", username)
            else:
                self.settings.remove("username")

            # Attempt to authenticate with server
            response = requests.post(
                f"{self.server_url}/api/token-auth/",
                json={"username": username, "password": password},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.authenticated_username = username
                QMessageBox.information(self, "Success", f"Welcome, {username}!")
                self.accept()
            else:
                error_msg = "Invalid username or password."
                if response.status_code != 400:  # Not a validation error
                    error_msg = f"Server error: {response.status_code}"
                QMessageBox.warning(self, "Login Failed", error_msg)

        except requests.RequestException as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Could not connect to the server. Please check your internet connection.\n\nError: {str(e)}"
            )

    @staticmethod
    def get_credentials(parent=None):
        """Static method to create the dialog and get credentials."""
        dialog = LoginDialog(parent)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return {
                "username": dialog.authenticated_username,
                "token": dialog.auth_token
            }
        return None