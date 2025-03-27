from django import forms

class NewDeckForm(forms.Form):
    name = forms.CharField(
        label = "Deck name"
    )

    desc = forms.CharField(
        label = "Deck description",
        widget=forms.Textarea
    )

