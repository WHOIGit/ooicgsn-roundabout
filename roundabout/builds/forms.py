from django import forms
from django.forms.models import inlineformset_factory

from .models import Build, BuildAction



class BuildForm(forms.ModelForm):

    class Meta:
        model = Build
        fields = ['build_number', 'assembly', 'location', 'build_notes', ]
        labels = {
            'build_number': 'Build ID Number',
        }


class BuildActionLocationChangeForm(forms.ModelForm):

    class Meta:
        model = Build
        fields = ['location', 'detail']
        labels = {
            'detail': 'Add a Note',
        }

    def __init__(self, *args, **kwargs):
        super(BuildActionLocationChangeForm, self).__init__(*args, **kwargs)
        self.initial['detail'] = ''
