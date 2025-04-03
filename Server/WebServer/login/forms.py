from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control',
                                                     'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control',
                                                      'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control',
                                                      'placeholder': 'Confirm Password'})


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'placeholder': 'Password'}))


class NewDeckForm(forms.Form):
    name = forms.CharField(
        label="Deck name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    desc = forms.CharField(
        label="Deck description",
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )

