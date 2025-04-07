from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


@csrf_exempt
def token_auth(request):
    """
    API endpoint for token-based authentication.
    Returns a token if credentials are valid.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        # Check if username and password are provided
        if not username or not password:
            return JsonResponse({"error": "Username and password are required"}, status=400)

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            from hashlib import sha256
            from django.utils import timezone

            token_base = f"{username}:{timezone.now().timestamp()}"
            token = sha256(token_base.encode()).hexdigest()

            request.session[f"auth_token_{token}"] = {
                "user_id": user.id,
                "username": user.username,
                "created": timezone.now().isoformat()
            }

            return JsonResponse({
                "token": token,
                "user_id": user.id,
                "username": user.username
            })
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def verify_token(request):
    """
    API endpoint to verify if a token is valid and return the associated user info.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        token = data.get('token')

        if not token:
            return JsonResponse({"error": "Token is required"}, status=400)

        # Check if token exists in session
        session_key = f"auth_token_{token}"
        token_data = request.session.get(session_key)

        if token_data:
            return JsonResponse({
                "valid": True,
                "user_id": token_data["user_id"],
                "username": token_data["username"]
            })
        else:
            return JsonResponse({"valid": False, "error": "Invalid or expired token"}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)