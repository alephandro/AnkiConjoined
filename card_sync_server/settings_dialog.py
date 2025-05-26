from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFormLayout, QGroupBox,
    QSettings, QIntValidator, QDialogButtonBox
)


class SettingsDialog(QDialog):
    """Dialog for configuring the card sync addon settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Card Sync Settings")
        self.setMinimumWidth(400)
        self.settings = QSettings("AnkiConjoined", "CardSync")

        layout = QVBoxLayout()

        server_group = QGroupBox("Server Settings")
        server_layout = QFormLayout()

        server_host = self.settings.value("server_host", "127.0.0.1")
        server_port = self.settings.value("server_port", "9999")
        web_url = self.settings.value("web_url", "http://127.0.0.1:8000")

        self.host_input = QLineEdit(server_host)
        server_layout.addRow("Socket Server Host:", self.host_input)

        self.port_input = QLineEdit(server_port)
        self.port_input.setValidator(QIntValidator(1, 65535))
        server_layout.addRow("Socket Server Port:", self.port_input)

        self.web_url_input = QLineEdit(web_url)
        server_layout.addRow("Web Server URL:", self.web_url_input)

        server_group.setLayout(server_layout)
        layout.addWidget(server_group)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def save_settings(self):
        """Save settings and close dialog."""
        self.settings.setValue("server_host", self.host_input.text())
        self.settings.setValue("server_port", self.port_input.text())
        self.settings.setValue("web_url", self.web_url_input.text())
        self.accept()