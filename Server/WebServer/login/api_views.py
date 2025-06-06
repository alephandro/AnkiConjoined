from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging
import os
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

TOKEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tokens')
os.makedirs(TOKEN_DIR, exist_ok=True)


@csrf_exempt
def token_auth(request):
    """
    API endpoint for token-based authentication.
    Returns a token if credentials are valid.
    """
    if request.method != 'POST':
        logger.warning("Method not allowed for token_auth: %s", request.method)
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        except json.JSONDecodeError:
            logger.error("Invalid JSON in token_auth request")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        logger.info("Authentication attempt for user: %s", username)

        if not username or not password:
            logger.warning("Missing username or password in token_auth request")
            return JsonResponse({"error": "Username and password are required"}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            token = str(uuid.uuid4())

            token_file = os.path.join(TOKEN_DIR, token)
            with open(token_file, 'w') as f:
                token_data = {
                    "user_id": user.id,
                    "username": user.username,
                    "created": datetime.now().isoformat(),
                    "expires": (datetime.now() + timedelta(hours=24)).isoformat()
                }
                json.dump(token_data, f)

            logger.info("Authentication successful for user: %s", username)

            return JsonResponse({
                "token": token,
                "user_id": user.id,
                "username": user.username
            })
        else:
            logger.warning("Invalid credentials for user: %s", username)
            return JsonResponse({"error": "Invalid credentials"}, status=401)

    except Exception as e:
        logger.exception("Error in token_auth: %s", str(e))
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def verify_token(request):
    """
    API endpoint to verify if a token is valid and return the associated user info.
    """
    if request.method != 'POST':
        logger.warning("Method not allowed for verify_token: %s", request.method)
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        try:
            data = json.loads(request.body)
            token = data.get('token')
        except json.JSONDecodeError:
            logger.error("Invalid JSON in verify_token request")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not token:
            logger.warning("Token is required in verify_token request")
            return JsonResponse({"error": "Token is required"}, status=400)

        token_file = os.path.join(TOKEN_DIR, token)
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                token_data = json.load(f)

            expires = datetime.fromisoformat(token_data["expires"])
            if datetime.now() > expires:
                os.remove(token_file)
                logger.warning("Token expired: %s", token)
                return JsonResponse({"valid": False, "error": "Token expired"}, status=401)

            logger.info("Token verification successful: %s", token)
            return JsonResponse({
                "valid": True,
                "user_id": token_data["user_id"],
                "username": token_data["username"]
            })
        else:
            logger.warning("Invalid token: %s", token)
            return JsonResponse({"valid": False, "error": "Invalid token"}, status=401)

    except Exception as e:
        logger.exception("Error in verify_token: %s", str(e))
        return JsonResponse({"error": str(e)}, status=500)