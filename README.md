# Anki Conjoined

Anki Conjoined is a comprehensive solution for synchronizing Anki flashcards across multiple devices and enabling collaborative learning through shared decks. This project consists of both a client-side Anki add-on and a server component with a web interface.

## Overview

Traditional Anki synchronization relies on AnkiWeb, which doesn't support collaborative editing of decks. Anki Conjoined fills this gap by providing:

- Multi-device synchronization independent of AnkiWeb
- Collaborative deck creation and editing
- Permission management for shared decks
- Simple sharing mechanism using unique deck codes

## Components

The project consists of three main components:

1. **Client Add-on**: An Anki add-on that enables communication with the server
2. **Socket Server**: A Python socket server that handles card data synchronization
3. **Web Server**: A Django web application for user management, deck administration, and permissions

## Installation

### Prerequisites

- Python 3.8 or higher
- Anki 2.1.x installed on your computer
- Command line/terminal access

### Step 1: Clone and Set Up the Project

```bash
# Clone the repository
git clone <repository-url>
cd AnkiConjoined

# Create and activate virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install Python dependencies
pip install django requests
```

### Step 2: Set Up the Django Web Server

```bash
# Navigate to Django project
cd Server/WebServer

# Set up database
python manage.py migrate

# Create admin user (you'll use this to log in)
python manage.py createsuperuser

# Test the setup
python manage.py check
```

### Step 3: Install the Anki Add-on

1. **Find your Anki add-ons folder**:
   - Open Anki
   - Go to Tools > Add-ons > View Files
   - This opens your add-ons directory

2. **Install the add-on**:
   - In the add-ons directory, create a new folder called `anki_conjoined`
   - Copy ALL contents from the `card_sync_server` folder into this new folder
   - The structure should look like:
     ```
     anki_conjoined/
     ├── __init__.py
     ├── main.py
     ├── client.py
     ├── auth_manager.py
     ├── login_dialog.py
     ├── settings_dialog.py
     ├── testAnkiConnected.py
     └── DataManagement/
         └── random_words
     
     ```

3. **Restart Anki** - You should now see a "Card Sync" menu

### Step 4: Run the Servers

⚠️ **Important**: You need to run BOTH servers simultaneously in separate terminals.

**Terminal 1 - Django Web Server:**
```bash
cd AnkiConjoined/Server/WebServer
source ../../.venv/bin/activate  # Activate virtual environment
python manage.py runserver
```
- This runs the web interface at http://127.0.0.1:8000/
- Keep this terminal open

**Terminal 2 - Socket Server:**
```bash
cd AnkiConjoined/Server
source ../.venv/bin/activate  # Activate virtual environment
python server.py
```
- This runs the sync server on localhost:9999
- Keep this terminal open

### Step 5: Create Your Account

1. Open http://127.0.0.1:8000/ in your web browser
2. Click "Register" and create a user account
3. Log in to verify your account works

### Step 6: Configure Anki Add-on

1. In Anki, click the "Card Sync" menu
2. Select "Settings" and configure:
   - Socket Server Host: `127.0.0.1`
   - Socket Server Port: `9999`
   - Web Server URL: `http://127.0.0.1:8000`
3. Click "Save"

### Step 7: Test the Connection

1. In Anki, go to "Card Sync" > "Login"
2. Enter the username and password you created in Step 5
3. If successful, you'll see a "Login successful" message

## Usage

### Basic Workflow

1. **Create a deck in Anki** with some cards
2. **Upload to server**: Card Sync > Sync with Server > Select your deck > Choose "create"
3. **Share with others**: Give them your deck code from the web interface
4. **Import shared deck**: Card Sync > Sync with Server > Choose "new" > Enter deck code
5. **Sync changes**: Card Sync > Sync with Server > Choose "update" to sync both ways

### Web Interface Features

- View and manage all your decks
- Share deck codes with other users
- Manage user permissions (Creator, Manager, Writer, Reader)
- Edit deck descriptions

## Troubleshooting

### "No such file or directory" Error
```bash
# Make sure you created the virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install django requests
```

### Django Server Won't Start
```bash
cd Server/WebServer
python manage.py migrate
python manage.py check
```

### Anki Add-on Not Showing
1. Make sure you copied ALL files from `card_sync_server/` 
2. Check that the folder is named correctly in your add-ons directory
3. Restart Anki completely

### Connection Errors
1. Ensure both servers are running (Steps 4)
2. Check firewall settings
3. Verify server addresses in Anki settings match your running servers

### Authentication Issues
1. Create account through web interface first (Step 5)
2. Use exact same credentials in Anki
3. Make sure Django server is running

## Advanced Configuration

### Custom Server Setup

You can modify server settings by editing the configuration files:

#### Socket Server Configuration
To change the socket server host and port, modify the Server class initialization in `server.py`:

```python
# Find this line at the bottom of server.py:
if __name__ == "__main__":
    server = Server()  # Default is localhost:9999

# Change it to specify your desired host and port:
if __name__ == "__main__":
    server = Server(host="0.0.0.0", port=8888)  # Example: listen on all interfaces, port 8888
```

Common host settings:
- `"localhost"` or `"127.0.0.1"`: Only accept connections from the same machine
- `"0.0.0.0"`: Accept connections from any network interface (needed for remote access)
- Specific IP: Only accept connections from that specific interface

#### Django Web Server Configuration

To change the Django web server address and port:
```bash
# Specify the IP address and port
python manage.py runserver 0.0.0.0:8000  # Listen on all interfaces, port 8000

# Or use a specific IP
python manage.py runserver 192.168.1.100:8000  # Listen on specific IP, port 8000
```

### Managing Decks via Web Interface

The web interface provides additional features:

1. **User Management**: Add or remove users from decks
2. **Permission Control**: Change user roles and access levels
3. **Deck Description**: Update deck information and descriptions

### Working with Collaborative Decks

When multiple users work on the same deck:

1. **Permission Levels**:
   - Creator (c): Full control over the deck, including deletion
   - Manager (m): Can manage users and edit cards
   - Writer (w): Can add and edit cards
   - Reader (r): Can only view and use cards

2. **Synchronization Process**:
   - Changes made by multiple users are tracked by timestamps
   - When syncing, only newer or modified cards are transferred
   - Each card maintains a unique ID (stable_uid) to track it across systems

## Development Setup

### IDE Configuration

If using PyCharm, VS Code, etc.:
1. Set Python interpreter to: `<project-path>/.venv/bin/python`
2. Set working directory to appropriate folder:
   - Django: `Server/WebServer`
   - Socket Server: `Server`
   - Anki Add-on: Test within Anki

## Security Considerations

- The communication between client and server is not encrypted by default
- Passwords are stored securely in the Django database
- Default setup is for local development only
- For production use, configure proper security settings and consider using HTTPS

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
