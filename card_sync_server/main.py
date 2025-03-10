# Import necessary Anki libraries
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, showWarning, tooltip, qconnect
import os

# Import your client functionality with the new callback system
from .client import Client, workflow_simulation

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

# Create a new menu item in Anki
def setup_menu():
    # Create the sync action
    sync_action = QAction("Sync with Server", mw)
    qconnect(sync_action.triggered, show_sync_dialog)
    
    # Add test action for debugging
    test_action = QAction("Test AnkiConnect", mw)
    qconnect(test_action.triggered, test_anki_connect)
    
    # Add them to the Tools menu
    mw.form.menuTools.addAction(sync_action)
    mw.form.menuTools.addAction(test_action)

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
        showWarning(f"Error connecting to AnkiConnect: {error_msg}\n\nMake sure AnkiConnect addon is installed and Anki is running.")
    
    anki_connect_request("version", on_success, on_error)

# Create a dialog with dropdown options
# In main.py - fix the ordering in show_sync_dialog function:

def show_sync_dialog():
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
    
    # For "new" action, add field for deck code (MOVED UP - BEFORE referencing)
    deck_code_label = QLabel("Deck Code (only for 'new' action):")
    layout.addWidget(deck_code_label)
    
    deck_code_input = QLineEdit()
    layout.addWidget(deck_code_input)
    
    # Update description when action changes - NOW AFTER UI elements are defined
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
