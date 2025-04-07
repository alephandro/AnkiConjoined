import os
import json
import requests
from aqt.qt import QSettings


class AuthManager:
    """
    Manages authentication and session persistence for the Anki Sync plugin.
    """

    def __init__(self, addon_dir):
        self.addon_dir = addon_dir
        self.auth_file = os.path.join(addon_dir, "auth_data.json")
        self.settings = QSettings("AnkiConjoined", "CardSync")
        self.server_url = self.settings.value("server_url", "http://127.0.0.1:8000")

        # Load existing auth data if available
        self.auth_data = self._load_auth_data()

    def _load_auth_data(self):
        """Load authentication data from file"""
        try:
            if os.path.exists(self.auth_file):
                with open(self.auth_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading auth data: {e}")
        return None

    def _save_auth_data(self, auth_data):
        """Save authentication data to file"""
        try:
            with open(self.auth_file, 'w') as f:
                json.dump(auth_data, f)
            return True
        except Exception as e:
            print(f"Error saving auth data: {e}")
            return False

    def is_authenticated(self):
        """Check if user is authenticated and token is still valid"""
        if not self.auth_data or not self.auth_data.get("token"):
            return False

        try:
            # Verify token with server
            response = requests.post(
                f"{self.server_url}/api/verify-token/",
                json={"token": self.auth_data["token"]},
                timeout=5
            )

            if response.status_code == 200 and response.json().get("valid"):
                return True

            # If token is invalid, clear auth data
            self._clear_auth_data()
            return False
        except requests.RequestException:
            # If server is not reachable, assume token is valid (offline mode)
            # This allows users to continue working offline
            return True

    def authenticate(self, username, password):
        """Authenticate with server and get token"""
        try:
            response = requests.post(
                f"{self.server_url}/api/token-auth/",
                json={"username": username, "password": password},
                timeout=5
            )

            if response.status_code == 200:
                auth_data = response.json()
                self._save_auth_data(auth_data)
                self.auth_data = auth_data
                return True, "Authentication successful"
            else:
                error_msg = "Invalid username or password"
                if response.status_code != 401:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", "Unknown error")
                    except:
                        error_msg = f"Server error: {response.status_code}"
                return False, error_msg
        except requests.RequestException as e:
            return False, f"Connection error: {str(e)}"

    def logout(self):
        """Clear authentication data"""
        self._clear_auth_data()

    def _clear_auth_data(self):
        """Clear authentication data from memory and file"""
        self.auth_data = None
        if os.path.exists(self.auth_file):
            try:
                os.remove(self.auth_file)
            except:
                pass

    def get_username(self):
        """Get currently authenticated username"""
        if self.auth_data:
            return self.auth_data.get("username")
        return None

    def get_token(self):
        """Get authentication token"""
        if self.auth_data:
            return self.auth_data.get("token")
        return None

    def set_server_url(self, url):
        """Set server URL and save to settings"""
        self.server_url = url
        self.settings.setValue("server_url", url)