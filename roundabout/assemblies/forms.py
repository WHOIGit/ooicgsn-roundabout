from django import forms
from django.forms.models import inlineformset_factory

from .models import Assembly, AssemblyPart



class AssemblyForm(forms.ModelForm):

    class Meta:
        model = Assembly
        fields = ['name', 'assembly_type', 'assembly_number', 'description', ]
        labels = {
            'assembly_number': 'Assembly ID Number',
        }


class AssemblyPartForm(forms.ModelForm):

    class Meta:
        model = AssemblyPart
        fields = ['assembly', 'part', 'parent', 'note']
        labels = {
            'part': 'Select Part Template',
            'parent': 'Parent Assembly',
            'note': 'Design Notes'
        }

    class Media:
        js = ('js/form-assemblyparts.js',)

    def __init__(self, *args, **kwargs):

        if 'assembly_pk' in kwargs:
            self.assembly_pk = kwargs.pop('assembly_pk')
        else:
            self.assembly_pk = None

        if 'parent_pk' in kwargs:
            self.parent_pk = kwargs.pop('parent_pk')
        else:
            self.parent_pk = None

        super(AssemblyPartForm, self).__init__(*args, **kwargs)
        #self.fields['parent'].queryset = MooringPart.objects.none()
        #self.fields['parent'].queryset = AssemblyPart.objects.filter(id=self.parent_pk)
        if self.assembly_pk:
            self.fields['parent'].queryset = AssemblyPart.objects.filter(assembly_id=self.assembly_pk)
        elif self.instance.pk:
            self.fields['parent'].queryset = AssemblyPart.objects.filter(assembly=self.instance.assembly)
