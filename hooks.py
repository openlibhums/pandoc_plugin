from django.template.loader import render_to_string

from plugins.pandoc_plugin import plugin_settings
from utils import models, setting_handler


def inject_pandoc(context):
    """
    Provides buttons for users to automatically convert manuscript files (docx or rtf) to html or xml.
    Uses the pandoc plugin, which must be installed on the server.
    """
    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    request = context.get('request')
    pandoc_enabled = setting_handler.get_plugin_setting(plugin, 'pandoc_enabled', request.journal, create=True,
                                                        pretty='Pandoc Enabled', types='boolean')

    if not pandoc_enabled.value:
        return ''

    else:
        return render_to_string('pandoc_plugin/inject.html', context={'article': context.get('article'), 'file': context.get('file')}, request=request)

