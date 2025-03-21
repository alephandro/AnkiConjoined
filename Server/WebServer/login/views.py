import json
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(project_root)

from card_sync_server.DataManagement.cards_management import generate_random_deck_code
from hashlib import sha256
from django.http import HttpResponse
from django.shortcuts import render, redirect
from login.models import *
from django.db.models import Q


# Create your views here.

def index(request):
    year = 2025
    user = "keo"
    data = retrieve_decks(user)
    return render(request, 'index.html',
                  {
                      'var1': 'content of var1',
                      'data': data,
                      'user': user,
                      'years': range(year, 2051),
                      'firstYear': year
                  })

def login(request, name):
    if name == "foo":
        return redirect('login_failed')
    else:
        return redirect(f'/welcome/{name}')

def welcome(request, name):
    return render(request, 'welcome.html',
                  {
                      'name': name
                  })

def login_failed(request):
    return HttpResponse("""
        <h2>Login has failed</h2>
        <hr/>
            <a href="/">Back to the Main Page?</a>
        <hr/>
        """)

def retrieve_decks(user):
    try:
        with open("/Users/alephandro/git/AnkiConjoined/Server/WebServer/decks.json", "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    return data.get(user, 0)


def register(request, username, password):
    user = User(
        username=username,
        password=sha256(password.encode('utf-8')).hexdigest()
    )

    user.save()
    return HttpResponse(f"User created: {user.username}")

def save_deck(request):

    if request.method == "GET":

        deck_name = request.GET.get("deck_name")
        deck_desc = request.GET.get("deck_desc")

        deck = Deck(
            deck_name = deck_name,
            deck_code = generate_random_deck_code(),
            deck_desc = deck_desc
        )

        deck.save()
        return HttpResponse(f"Deck created: {deck.deck_name}\n Your deck code is: '{deck.deck_code}'")
    else:
        return HttpResponse(f"Invalid method: {request.method}")


def save_deck_user_privilege(user, deck, privilege):
    userDeck = UserDeck(
        user=user,
        deck=deck,
        privilege=privilege
    )

    userDeck.save()


def deck_creation_view(request):
    return render(request, "deck_creation.html")

def get_user(request):
    user = User.objects

    password = user.get(username="pepe").password

    html = f"<h1>Password of pepe: {password}</h1>"
    return HttpResponse(html)

def change_password(request, username, old, new):
    user = User.objects.get(username=username)
    hash_old = sha256(old.encode('utf-8')).hexdigest()
    db_old_password = user.password
    if db_old_password != hash_old:
        return HttpResponse("The old password doesn't match with the one in the database.")

    user.password = sha256(new.encode('utf-8')).hexdigest()
    user.save()
    return HttpResponse(f"Password changed: {user.username}")

def drop_user(username):
    user = User.objects.get(username=username)
    user.delete()