import json

from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.

def index(request):
    year = 2025
    user = "keo"
    data = retreive_decks(user)
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
    return HttpResponse(f"""
    <h2>Welcome {name}!!</h2>
    """)

def login_failed(request):
    return HttpResponse("""
        <h2>Login has failed</h2>
        <hr/>
            <a href="/">Back to the Main Page?</a>
        <hr/>
        """)

def retreive_decks(user):
    try:
        with open("/Users/alephandro/git/AnkiConjoined/Server/WebServer/decks.json", "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    return data.get(user, 0)