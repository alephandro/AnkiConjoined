import json
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(project_root)

from DataManagement.cards_management import generate_random_deck_code
from hashlib import sha256
from django.http import HttpResponse
from django.shortcuts import render, redirect
from login.models import *
from django.db.models import Q
from login.forms import NewDeckForm


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

    if request.method == "POST":
        deck_name = request.POST.get("deck_name")
        deck_desc = request.POST.get("deck_desc")
        save_deck_local(deck_name, deck_desc)
        return HttpResponse(f"Deck created: {deck.deck_name}\n Your deck code is: '{deck.deck_code}'")

    else:
        return HttpResponse(f"Invalid method: {request.method}")

def save_deck_local(deck_name, deck_desc):
    deck = Deck(
        deck_name=deck_name,
        deck_code=generate_random_deck_code(),
        deck_desc=deck_desc
    )
    deck.save()

    empty = {}
    path = f"{project_root}/Server/{deck.deck_code}.json"
    with open(path, "w") as file:
        json.dump(empty, file)

    return deck

def save_deck_user_privilege(user, deck, privilege):
    if check_user(user):
        user = User.objects.get(username=user)
        deck = Deck.objects.get(deck_name=deck)

        userDeck = UserDeck(
            user=user,
            deck=deck,
            privilege=privilege
        )

        userDeck.save()

        return True

    else:
        return False


def deck_creation_view(request):
    return render(request, "deck_creation.html")

def deck_creation_form(request):
    if request.method == "POST":

        form = NewDeckForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            desc = form.cleaned_data["desc"]
            deck = save_deck_local(name, desc)
            if save_deck_user_privilege("pedro", deck.deck_name, "c"):
                return HttpResponse(f"Deck created: {deck.deck_name}, and your deck code is: '{deck.deck_code}'")
            else:
                return HttpResponse(f"Invalid form: {form.errors}")
        else:
            return HttpResponse(f"Invalid form: {form.is_valid()}")
    else:
        form = NewDeckForm()
        return render(request, "deck_creation_form.html", {
            'form': form
        })

def check_user(username):
    user = User.objects
    user = user.get(username=username)
    return user is not None

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

def drop_deck(deck_name):
    deck = Deck.objects.get(deck_name=deck_name)
    deck_code = deck.deck_code
    deck.delete()

    deck_relations = UserDeck.objects.filter(deck=deck_code)
    for deck_relation in deck_relations:
        deck_relation.delete()

    path = f"{project_root}/Server/{deck_code}.json"
    if os.path.exists(path):
        os.remove(path)

def delete_deck(request, deck_code):
    # check the privileges
    # username = request.POST.get("username")
    username = "pedro"
    privilege = UserDeck.objects.get(user=username, deck=deck_code).privilege
    if privilege == "c":
        deck_name = Deck.objects.get(deck_code=deck_code).deck_name
        drop_deck(deck_name)
        return redirect("my_decks")
    else:
        return HttpResponse(f"Invalid privilege: {privilege}")

def user_decks(request):
    # username = request.POST.get("username")
    username = "pedro"
    deck_codes = UserDeck.objects.filter(user=username).values_list('deck_id', flat=True)
    decks = Deck.objects.filter(deck_code__in=deck_codes)

    return render(request, "user_decks.html", {
        'decks': decks
    })