from django import forms
from django.forms.models import inlineformset_factory

from .models import Assembly



class AssemblyForm(forms.ModelForm):

    class Meta:
        model = Assembly
        fields = ['name', 'assembly_number', 'description', ]
        labels = {
            'assembly_number': 'Assembly ID Number',
        }
