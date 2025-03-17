import json

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


def register(request):
    user = User(
        username="pepe",
        password=sha256("keo".encode('utf-8')).hexdigest()
    )

    user.save()
    return HttpResponse(f"User created: {user.username}")

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