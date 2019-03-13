from django import forms

from .models import Printer


class PrinterForm(forms.ModelForm):

    class Meta:
        model = Printer
        fields = ['name', 'ip_domain', 'printer_type' ]
        labels = {
        'ip_domain': 'IP Address/Domain'
    }
