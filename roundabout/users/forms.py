from django import forms
from django.contrib.auth import get_user_model, forms as auth_forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password

from django.contrib.auth.models import Group

User = get_user_model()


class UserChangeForm(auth_forms.UserChangeForm):

    class Meta(auth_forms.UserChangeForm.Meta):
        model = User


class UserCreationForm(auth_forms.UserCreationForm):

    error_message = auth_forms.UserCreationForm.error_messages.update(
        {"duplicate_username": _("This username has already been taken.")}
    )

    class Meta(auth_forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])


class UserAdminCreateForm(forms.ModelForm):
    username = forms.CharField(strip=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'name', 'email',  'groups', ]
        labels = {
            'groups': 'User Role'
        }

        widgets = {
            'groups': forms.CheckboxSelectMultiple(),
            'password': forms.PasswordInput(),
        }


class UserAdminUpdateForm(forms.ModelForm):
    username = forms.CharField(strip=True)

    class Meta:
        model = User
        fields = ['username', 'name', 'email',  'groups', ]
        labels = {
            'groups': 'User Role'
        }

        widgets = {
            'groups': forms.CheckboxSelectMultiple(),
            'password': forms.PasswordInput(),
        }
