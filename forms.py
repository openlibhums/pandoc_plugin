from django import forms

from tinymce.widgets import TinyMCE

from utils import setting_handler, models
from plugins.pandoc_plugin import plugin_settings


class PandocAdminForm(forms.Form):
    pandoc_enabled = forms.BooleanField(label="Enable Pandoc", required=False)
    pandoc_extract_images = forms.BooleanField(label="Extract Images", required=False)
    cover_sheet = forms.CharField(
        label="Cover Sheet",
        widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
        required=False
    )
    def __init__(self, *args, journal=None, **kwargs):
        """Initialize form with current plugin settings and apply help text."""
        super().__init__(*args, **kwargs)
        self.journal = journal
        self.plugin = models.Plugin.objects.get(
            name=plugin_settings.SHORT_NAME,
        )

        # Initialize fields with settings values and help texts
        pandoc_enabled_setting = setting_handler.get_plugin_setting(
            self.plugin, 'pandoc_enabled', self.journal, create=True,
            pretty='Enable Pandoc', types='boolean'
        )
        self.fields[
            'pandoc_enabled'
        ].initial = pandoc_enabled_setting.processed_value

        extract_images_setting = setting_handler.get_plugin_setting(
            self.plugin, 'pandoc_extract_images', self.journal, create=True,
            pretty='Pandoc extract images', types='boolean'
        )
        self.fields[
            'pandoc_extract_images'
        ].initial = extract_images_setting.processed_value

        cover_sheet_setting = setting_handler.get_plugin_setting(
            self.plugin, 'cover_sheet', self.journal, create=True,
            pretty='Cover Sheet', types='text'
        )
        self.fields[
            'cover_sheet'
        ].initial = cover_sheet_setting.processed_value

    def save(self):
        """Save each setting in the cleaned data to the plugin settings."""
        for setting_name, setting_value in self.cleaned_data.items():
            setting_handler.save_plugin_setting(
                plugin=self.plugin,
                setting_name=setting_name,
                value=setting_value,
                journal=self.journal
            )
