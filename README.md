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

- Anki 2.1.x installed on your computer
- Python 3.8 or higher
- Django 5.1.x (for server component)
- Access to command line/terminal

### Client Add-on Installation

1. **Download the add-on files**:
   - Download the `card_sync_server` folder from this repository

2. **Install in Anki**:
   - Open Anki
   - Go to Tools > Add-ons > Open Add-ons Folder
   - Create a new folder called `anki_conjoined` (or similar)
   - Copy the contents of the `card_sync_server` folder into this new folder
   - Restart Anki

3. **Install dependencies**:
   - Make sure the following Python packages are installed:
     ```
     pip install requests
     ```

4. **Verify installation**:
   - After restarting Anki, you should see a new "Card Sync" menu in Anki's main window

### Server Installation (Optional, for self-hosting)

#### Socket Server

1. **Set up the socket server**:
   ```bash
   # Navigate to the Server directory
   cd Server
   
   # If using a virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install django
   
   # Run the server
   python server.py
   ```

#### Web Server

1. **Set up the Django server**:
   ```bash
   # Navigate to the WebServer directory
   cd Server/WebServer
   
   # If using a virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install django
   
   # Apply migrations
   python manage.py migrate
   
   # Create a superuser
   python manage.py createsuperuser
   
   # Run the development server
   python manage.py runserver
   ```

2. **Access the web interface**:
   - Open your browser and navigate to `http://127.0.0.1:8000/`
   - Log in with the superuser credentials you created

## Client-Side Usage

### Configuring the Add-on

1. **Access the settings**:
   - In Anki, click on the "Card Sync" menu
   - Select "Settings"
   - Configure the following:
     - Socket Server Host (default: 127.0.0.1)
     - Socket Server Port (default: 9999)
     - Web Server URL (default: http://127.0.0.1:8000)

2. **Login to your account**:
   - In Anki, click on the "Card Sync" menu
   - Select "Login"
   - Enter your username and password

### Syncing Decks

The add-on supports various synchronization operations:

1. **Create a new deck on the server**:
   - Create a deck in Anki
   - From the "Card Sync" menu, select "Sync with Server"
   - Choose your deck and the "create" action
   - The deck will be uploaded to the server and made available to you in the web interface

2. **Download changes from the server**:
   - From the "Card Sync" menu, select "Sync with Server"
   - Choose your deck and the "receive" action
   - Any new or updated cards will be downloaded from the server

3. **Full synchronization (both ways)**:
   - From the "Card Sync" menu, select "Sync with Server"
   - Choose your deck and the "update" action
   - This will both upload your changes and download others' changes

4. **Import a new deck using a code**:
   - Get a deck code from another user (from the web interface)
   - From the "Card Sync" menu, select "Sync with Server"
   - Choose the "new" action and enter the deck code
   - The deck will be downloaded and created in your Anki collection

5. **Delete a deck**:
   - From the "Card Sync" menu, select "Sync with Server"
   - Choose your deck and the "delete" action
   - This will remove the deck from your synchronized decks list

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

## Troubleshooting

### Common Issues

1. **Connection errors**:
   - Ensure the server is running
   - Check your firewall settings
   - Verify the host and port in the settings

2. **Authentication issues**:
   - Make sure you've created an account on the web interface
   - Verify your username and password

3. **AnkiConnect errors**:
   - Ensure you have AnkiConnect add-on installed
   - Restart Anki after installation

### Logs

- Client-side errors are logged to a file named `error_log.txt` in the add-on directory
- Server logs appear in the terminal where the server is running
- Django logs can be found in the Django development server console

## Advanced Features

### Custom Server Setup

You can set up your own server by modifying the server host and port in the settings. This allows you to:

1. Run the server on your local network for home/office use
2. Deploy to a cloud server for wider access
3. Customize authentication and security settings

### Managing Decks via Web Interface

The web interface provides additional features:

1. **User Management**: Add or remove users from decks
2. **Permission Control**: Change user roles and access levels
3. **Deck Description**: Update deck information and descriptions

## Security Considerations

- The communication between client and server is not encrypted by default
- Passwords are stored securely in the Django database
- For production use, consider setting up HTTPS and proper security measures

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Anki for the fantastic flashcard platform
- The Django team for the web framework
