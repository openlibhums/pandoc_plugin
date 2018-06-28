from django import forms

class PandocAdminForm(forms.Form):
    pandoc_enabled = forms.BooleanField(required=False)