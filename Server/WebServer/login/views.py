import json
import sys, os
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(project_root)

from DataManagement.cards_management import generate_random_deck_code
from login.forms import SignUpForm, LoginForm, NewDeckForm
from login.models import Deck, UserDeck


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('index')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'login/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Account created for {username}!")
            auth_login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'login/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def index(request):
    decks = retrieve_decks(request.user.username)
    year = 2025
    return render(request, 'index.html',
                  {
                      'data': decks,
                      'user': request.user.username,
                      'years': range(year, 2051),
                      'firstYear': year
                  })


def retrieve_decks(user):
    user_decks = UserDeck.objects.filter(user__username=user)
    return [deck.deck for deck in user_decks]


@login_required
def welcome(request, name):
    return render(request, 'welcome.html', {'name': name})


@login_required
def deck_creation_view(request):
    return render(request, "deck_creation.html")


@login_required
def deck_creation_form(request):
    if request.method == "POST":
        form = NewDeckForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            desc = form.cleaned_data["desc"]

            try:
                deck = Deck(
                    deck_name=name,
                    deck_code=generate_random_deck_code(),
                    deck_desc=desc
                )
                deck.save()

                empty = {}
                path = f"{project_root}/Server/{deck.deck_code}.json"
                with open(path, "w") as file:
                    json.dump(empty, file)

                user_deck = UserDeck(
                    user=request.user,
                    deck=deck,
                    privilege="c"
                )
                user_deck.save()

                messages.success(request,
                                 f"Deck '{deck.deck_name}' created successfully! Your deck code is: {deck.deck_code}")
                return redirect('my_decks')

            except Exception as e:
                print(f"Error in deck creation process: {str(e)}")
                try:
                    if 'deck' in locals():
                        path = f"{project_root}/Server/{deck.deck_code}.json"
                        if os.path.exists(path):
                            os.remove(path)
                        deck.delete()
                except Exception as cleanup_error:
                    print(f"Error during cleanup: {str(cleanup_error)}")

                messages.error(request, f"Error creating deck: {str(e)}")
    else:
        form = NewDeckForm()

    return render(request, "deck_creation_form.html", {'form': form})


@login_required
def user_decks(request):
    user_decks = UserDeck.objects.filter(user=request.user)

    # Create a list of decks with additional user privilege information
    decks_with_privileges = []
    for user_deck in user_decks:
        deck_info = {
            'deck_name': user_deck.deck.deck_name,
            'deck_code': user_deck.deck.deck_code,
            'deck_desc': user_deck.deck.deck_desc,
            'user_privilege': user_deck.privilege
        }
        decks_with_privileges.append(deck_info)

    return render(request, "user_decks.html", {'decks': decks_with_privileges})


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


def save_deck_user_privilege(username, deck_code, privilege):
    from django.contrib.auth.models import User

    try:
        print(f"Creating relationship: username={username}, deck_code={deck_code}, privilege={privilege}")

        user = User.objects.get(username=username)
        print(f"Found user with ID: {user.id}")

        deck = Deck.objects.get(deck_code=deck_code)
        print(f"Found deck with name: {deck.deck_name}")
        user_deck = UserDeck(
            user=user,
            deck=deck,
            privilege=privilege
        )
        user_deck.save()
        print("User-deck relationship created successfully")
        return True
    except User.DoesNotExist:
        print(f"Error: User '{username}' not found")
        return False
    except Deck.DoesNotExist:
        print(f"Error: Deck with code '{deck_code}' not found")
        return False
    except Exception as e:
        print(f"Error creating user-deck relationship: {str(e)}")
        return False


@login_required
def delete_deck(request, deck_code):
    try:
        user_deck = UserDeck.objects.get(user=request.user, deck__deck_code=deck_code)
        deck = user_deck.deck

        if request.method == 'POST':
            confirmed = request.POST.get('confirmed') == 'true'

            if not confirmed:
                return redirect('my_decks')

            if user_deck.privilege == "c":
                deck_name = deck.deck_name

                UserDeck.objects.filter(deck=deck).delete()
                deck.delete()

                Deck.objects.filter(deck_code=deck_code).delete()

                path = f"{project_root}/Server/{deck_code}.json"
                if os.path.exists(path):
                    os.remove(path)

                messages.success(request, f"Deck '{deck_name}' has been deleted.")
            else:
                user_deck.delete()
                messages.success(request, f"You have left the deck '{deck.deck_name}'.")

            return redirect("my_decks")

        context = {
            'deck': deck,
            'privilege': user_deck.privilege,
            'is_creator': user_deck.privilege == 'c'
        }
        return render(request, 'login/confirm_deck_action.html', context)

    except UserDeck.DoesNotExist:
        messages.error(request, "Deck not found or you don't have access to it.")
        return redirect("my_decks")