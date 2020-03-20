from django import forms

class PandocAdminForm(forms.Form):
    pandoc_enabled = forms.BooleanField(required=False)
    pandoc_extract_images = forms.BooleanField(required=False)
