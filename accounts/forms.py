from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(
            username__iexact=username,
        ).exists():
            raise forms.ValidationError(
                "A user with this username already exists.",
            )

        return username
