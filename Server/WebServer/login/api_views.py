from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)


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
        # Parse request body
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        except json.JSONDecodeError:
            logger.error("Invalid JSON in token_auth request")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Log authentication attempt
        logger.info("Authentication attempt for user: %s", username)

        # Check if username and password are provided
        if not username or not password:
            logger.warning("Missing username or password in token_auth request")
            return JsonResponse({"error": "Username and password are required"}, status=400)

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # User is authenticated, generate a simple token
            from hashlib import sha256
            from django.utils import timezone

            # Generate a token based on username and current time
            token_base = f"{username}:{timezone.now().timestamp()}"
            token = sha256(token_base.encode()).hexdigest()

            # Store token in session
            session_key = f"auth_token_{token}"
            token_data = {
                "user_id": user.id,
                "username": user.username,
                "created": timezone.now().isoformat()
            }

            # Store in session
            request.session[session_key] = token_data
            request.session.modified = True  # Ensure session is saved

            logger.info("Authentication successful for user: %s", username)

            # Return token and user info
            return JsonResponse({
                "token": token,
                "user_id": user.id,
                "username": user.username
            })
        else:
            # Authentication failed
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
        # Parse request body
        try:
            data = json.loads(request.body)
            token = data.get('token')
        except json.JSONDecodeError:
            logger.error("Invalid JSON in verify_token request")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not token:
            logger.warning("Token is required in verify_token request")
            return JsonResponse({"error": "Token is required"}, status=400)

        # Check if token exists in session
        session_key = f"auth_token_{token}"
        token_data = request.session.get(session_key)

        if token_data:
            logger.info("Token verification successful: %s", token)
            return JsonResponse({
                "valid": True,
                "user_id": token_data["user_id"],
                "username": token_data["username"]
            })
        else:
            logger.warning("Invalid or expired token: %s", token)
            return JsonResponse({"valid": False, "error": "Invalid or expired token"}, status=401)

    except Exception as e:
        logger.exception("Error in verify_token: %s", str(e))
        return JsonResponse({"error": str(e)}, status=500)