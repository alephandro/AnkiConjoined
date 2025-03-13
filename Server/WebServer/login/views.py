from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.

def index(request):

    html = """
        <h1>Main Page</h1>
        <p>Years till 2050</p>
        <ul>
    """

    for year in range(2025, 2051):
        html += f"<li>{str(year)}</li>"

    html += "</ul>"
    return render(request, 'index.html')

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