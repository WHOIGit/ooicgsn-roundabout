from django import forms
from .models import ConfigEvent, ConfigName, ConfigValue, ConstDefault, ConstDefaultEvent
from roundabout.inventory.models import Inventory, Deployment
from roundabout.parts.models import Part
from roundabout.users.models import User
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from bootstrap_datepicker_plus import DatePickerInput
from sigfig import round
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


TEST_DEPLOYMENT_DATES = (
      ("02/23/2015", "02/23/2015"),
      ("07/24/2013", "07/24/2013"),
      ("07/01/2016", "07/01/2016"),
  )

# Configuration Event form 
# Inputs: Config Date and Approval
class ConfigEventForm(forms.ModelForm):
    class Meta:
        model = ConfigEvent 
        fields = ['deployment','approved']
        labels = {
            'deployment': 'Deployment',
            'approved': 'Approved'
        }
        widgets = {
            'deployment': forms.Select(
                attrs = {
                    'required': True
                }
            )
        }
    def __init__(self, *args, **kwargs):
        super(ConfigEventForm, self).__init__(*args, **kwargs)

# Configuration Value form
# Inputs: Configuration values and notes per Part Config Type
class ConfigValueForm(forms.ModelForm):
    class Meta:
        model = ConfigValue
        fields = ['config_name','config_value', 'notes']
        labels = {
            'config_name': 'Configuration/Constant Name',
            'config_value': 'Value',
            'notes': 'Additional Notes'
        }
        widgets = {
            'config_value': forms.Textarea(
                attrs = {
                    'style': 'white-space: nowrap'
                }
            )
        }
    
    def __init__(self, *args, **kwargs):
        super(ConfigValueForm, self).__init__(*args, **kwargs)

    def clean_config_name(self):
        config_name = self.cleaned_data.get('config_name')
        return config_name

# Configuration Name Form
# Inputs: Name, Input Type
class ConfigNameForm(forms.ModelForm):
    class Meta:
        model = ConfigName
        fields = ['name', 'config_type']
        labels = {
            'name': 'Configuration/Constant Name',
            'config_type': 'Type'
        }
        widgets = {
            'name': forms.TextInput(
                attrs = {
                    'required': False
                }
            ),
        }


# Constant Default form
# Inputs: Constant default values
class ConstDefaultForm(forms.ModelForm):
    class Meta:
        model = ConstDefault
        fields = ['config_name','default_value']
        labels = {
            'config_name': 'Constant Name',
            'default_value': 'Value'
        }
        widgets = {
            'config_name': forms.Select(
                attrs = {
                    'readonly': True,
                    'style': 'cursor: not-allowed; pointer-events: none; background-color: #d5dfed;'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super(ConstDefaultForm, self).__init__(*args, **kwargs)

    def clean_config_name(self):
        config_name = self.cleaned_data.get('config_name')
        return config_name


# Constant Default Event form 
# Inputs: Reviewers
class ConstDefaultEventForm(forms.ModelForm):
    class Meta:
        model = ConstDefaultEvent 
        fields = ['user_draft']
        labels = {
            'user_draft': 'Reviewers'
        }
        widgets = {
            'user_draft': forms.SelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(ConstDefaultEventForm, self).__init__(*args, **kwargs)
        self.fields['user_draft'].queryset = User.objects.all().exclude(groups__name__in=['inventory only'])

    def clean_user_draft(self):
        user_draft = self.cleaned_data.get('user_draft')
        return user_draft

    def save(self, commit = True): 
        event = super(ConstDefaultEventForm, self).save(commit = False)
        if commit:
            event.save()
            return event
        
# Configuration Value form instance generator for ConfigEvents
ConfigEventValueFormset = inlineformset_factory(
    ConfigEvent, 
    ConfigValue, 
    form=ConfigValueForm,
    fields=('config_name', 'config_value', 'notes'), 
    extra=1, 
    can_delete=True
)

# Configuration Name form instance generator for Parts
PartConfigNameFormset = inlineformset_factory(
    Part, 
    ConfigName, 
    form=ConfigNameForm, 
    fields=('name', 'config_type'), 
    extra=1, 
    can_delete=True
)

# Configuration Name form instance generator for Parts
EventDefaultFormset = inlineformset_factory(
    ConstDefaultEvent, 
    ConstDefault, 
    form=ConstDefaultForm, 
    fields=('config_name', 'default_value'), 
    extra=0, 
    can_delete=True
)