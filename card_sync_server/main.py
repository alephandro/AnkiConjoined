# Import necessary Anki libraries
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, showWarning, tooltip, qconnect
import os

# Import plugin functionality
from .client import Client, workflow_simulation
from .login_dialog import LoginDialog
from .auth_manager import AuthManager

# Setup logging
ADDON_DIR = os.path.dirname(__file__)
ERROR_LOG_PATH = os.path.join(ADDON_DIR, "error_log.txt")


def log_error(message):
    """Log errors to file for debugging"""
    import traceback
    try:
        with open(ERROR_LOG_PATH, "a") as f:
            f.write(f"{message}\n")
            f.write(traceback.format_exc())
            f.write("\n---\n")
    except:
        pass  # Fallback in case logging itself fails


# Progress dialog for async operations
class ProgressDialog(QDialog):
    def __init__(self, parent, title="Please Wait", message="Operation in progress..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QVBoxLayout()

        # Message label
        self.message_label = QLabel(message)
        layout.addWidget(self.message_label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress)

        # Status label
        self.status_label = QLabel("Starting...")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def update_status(self, status):
        self.status_label.setText(status)
        QApplication.processEvents()  # Process UI events to update the display


# Initialize the auth manager
auth_manager = AuthManager(ADDON_DIR)


# Create a new menu item in Anki
def setup_menu():
    # Create the main menu
    main_menu = QMenu('Card Sync', mw)

    # Create the sync action
    sync_action = QAction("Sync with Server", mw)
    qconnect(sync_action.triggered, show_sync_dialog)

    # Add test action for debugging
    test_action = QAction("Test AnkiConnect", mw)
    qconnect(test_action.triggered, test_anki_connect)

    # Add login/logout actions
    login_action = QAction("Login", mw)
    qconnect(login_action.triggered, show_login_dialog)

    logout_action = QAction("Logout", mw)
    qconnect(logout_action.triggered, logout_user)

    # Add settings action
    settings_action = QAction("Settings", mw)
    qconnect(settings_action.triggered, show_settings_dialog)

    # Add actions to the menu
    main_menu.addAction(login_action)
    main_menu.addAction(logout_action)
    main_menu.addSeparator()
    main_menu.addAction(sync_action)
    main_menu.addAction(test_action)
    main_menu.addSeparator()
    main_menu.addAction(settings_action)

    # Add the menu to Anki's menu bar
    mw.form.menubar.addMenu(main_menu)


# Show login dialog
def show_login_dialog():
    credentials = LoginDialog.get_credentials(mw)
    if credentials:
        tooltip("Login successful!", period=3000)


# Logout the current user
def logout_user():
    client = Client()
    client.logout()
    tooltip("Logged out successfully!", period=3000)


# Show settings dialog
def show_settings_dialog():
    # Create a dialog
    dialog = QDialog(mw)
    dialog.setWindowTitle("Card Sync Settings")
    dialog.setMinimumWidth(400)

    layout = QVBoxLayout()

    # Server settings
    server_group = QGroupBox("Server Settings")
    server_layout = QFormLayout()

    # Load current settings
    settings = QSettings("AnkiConjoined", "CardSync")
    server_host = settings.value("server_host", "127.0.0.1")
    server_port = settings.value("server_port", "9999")

    # Host input
    host_input = QLineEdit(server_host)
    server_layout.addRow("Server Host:", host_input)

    # Port input
    port_input = QLineEdit(server_port)
    port_input.setValidator(QIntValidator(1, 65535))
    server_layout.addRow("Server Port:", port_input)

    server_group.setLayout(server_layout)
    layout.addWidget(server_group)

    # Buttons
    button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                  QDialogButtonBox.StandardButton.Cancel)

    def on_save():
        # Save settings
        settings.setValue("server_host", host_input.text())
        settings.setValue("server_port", port_input.text())
        tooltip("Settings saved!", period=2000)
        dialog.accept()

    qconnect(button_box.accepted, on_save)
    qconnect(button_box.rejected, dialog.reject)

    layout.addWidget(button_box)
    dialog.setLayout(layout)

    # Show dialog
    dialog.exec()


# Test function for AnkiConnect
def test_anki_connect():
    from .testAnkiConnected import anki_connect_request

    progress = ProgressDialog(mw, "Testing AnkiConnect", "Testing connection to AnkiConnect...")
    progress.show()

    def on_success(result):
        progress.hide()
        showInfo(f"Success! AnkiConnect is working.\nVersion: {result.get('result', 'Unknown')}")

    def on_error(error_msg):
        progress.hide()
        showWarning(
            f"Error connecting to AnkiConnect: {error_msg}\n\nMake sure AnkiConnect addon is installed and Anki is running.")

    anki_connect_request("version", on_success, on_error)


# Create a dialog with dropdown options
def show_sync_dialog():
    # First check if user is authenticated
    client = Client()
    if not client.ensure_authenticated(mw):
        return  # Authentication failed or was canceled

    dialog = QDialog(mw)
    dialog.setWindowTitle("Sync Options")
    dialog.setMinimumWidth(400)

    layout = QVBoxLayout()

    # Create dropdown for deck selection
    deck_label = QLabel("Select Deck:")
    layout.addWidget(deck_label)

    deck_combo = QComboBox()

    # Populate with all available decks
    def on_decks_loaded(decks):
        deck_combo.clear()
        deck_combo.addItems(decks)

    def on_decks_error(error_msg):
        showWarning(
            f"Error loading decks: {error_msg}\n\nMake sure AnkiConnect addon is installed and working properly.")
        # Add some default decks to allow the dialog to work
        try:
            # Get decks directly from Anki's collection
            deck_names = [d['name'] for d in mw.col.decks.all()]
            deck_combo.addItems(deck_names)
        except:
            deck_combo.addItem("Default")

    # Use the async function to get decks
    from .testAnkiConnected import list_decks
    list_decks(on_decks_loaded, on_decks_error)

    layout.addWidget(deck_combo)

    # Create dropdown for action selection
    action_label = QLabel("Select Action:")
    layout.addWidget(action_label)

    action_combo = QComboBox()
    action_combo.addItems(["create", "receive", "update", "new", "delete"])
    layout.addWidget(action_combo)

    # Add information about each action
    info_label = QLabel("Action Description:")
    layout.addWidget(info_label)

    action_info = QLabel("Choose an action from the dropdown")
    layout.addWidget(action_info)

    # For "new" action, add field for deck code
    deck_code_label = QLabel("Deck Code (only for 'new' action):")
    layout.addWidget(deck_code_label)

    deck_code_input = QLineEdit()
    layout.addWidget(deck_code_input)

    # Update description when action changes
    def update_description(index):
        descriptions = {
            "create": "Upload deck cards to server",
            "receive": "Download new/updated cards from server",
            "update": "Sync both ways (upload and download)",
            "new": "Download a new deck using a deck code",
            "delete": "Delete the deck and its sync information"
        }
        action = action_combo.currentText()
        action_info.setText(descriptions.get(action, ""))

        # Show/hide deck code input based on action
        deck_code_label.setVisible(action == "new")
        deck_code_input.setVisible(action == "new")

    qconnect(action_combo.currentIndexChanged, update_description)
    update_description(0)  # Set initial description

    # Buttons
    button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                  QDialogButtonBox.StandardButton.Cancel)
    qconnect(button_box.accepted, dialog.accept)
    qconnect(button_box.rejected, dialog.reject)
    layout.addWidget(button_box)

    dialog.setLayout(layout)

    # Execute the dialog
    if dialog.exec():
        selected_deck = deck_combo.currentText()
        selected_action = action_combo.currentText()
        deck_code = deck_code_input.text()

        # Execute the selected action
        execute_action(selected_action, selected_deck, deck_code)


def execute_action(action, deck_name, deck_code=""):
    """Execute the selected sync action with progress dialog"""
    # Show progress dialog
    progress = ProgressDialog(mw, f"Executing {action.capitalize()}",
                              f"Starting {action} operation...")
    progress.show()

    # Initialize the client
    client = Client()

    # Setup callback for workflow completion
    def on_workflow_complete(success, message):
        progress.hide()
        if success:
            showInfo(f"Operation '{action}' completed successfully!\n\n{message}")
        else:
            showWarning(f"Operation '{action}' encountered issues:\n\n{message}")

    try:
        # Update progress dialog during operations
        def status_callback(success, message):
            progress.update_status(message)

        # Handle special case for 'new' action
        if action == "new" and deck_code:
            # Parameters: client, create, receive, deck_name, new, delete, callback
            workflow_simulation(client, False, False, deck_code, True, False, on_workflow_complete)
        else:
            # Parameters for workflow_simulation:
            create = action in ["create", "update"]
            receive = action in ["receive", "update"]
            new_deck = False
            delete = action == "delete"

            workflow_simulation(client, create, receive, deck_name, new_deck, delete, on_workflow_complete)

    except Exception as e:
        progress.hide()
        error_msg = f"Error starting operation: {str(e)}"
        log_error(error_msg)
        showWarning(error_msg)


# Add our menu item when Anki starts
setup_menu()