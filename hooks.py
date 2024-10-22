from django.template.loader import render_to_string

from plugins.pandoc_plugin import plugin_settings
from utils import models, setting_handler


def inject_pandoc(context):
    """
    Provides buttons for users to automatically convert manuscript files (docx or rtf) to html.
    Uses the pandoc plugin, which must be installed on the server.
    """
    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    request = context.get('request')
    pandoc_enabled = setting_handler.get_plugin_setting(
        plugin,
        'pandoc_enabled',
        request.journal,
        create=True,
        pretty='Pandoc Enabled',
        types='boolean',
    )

    if pandoc_enabled.processed_value:
        return render_to_string(
            'pandoc_plugin/inject.html',
            context={
                'article': context.get('article'),
                'file': context.get('file')},
            request=request,
        )

    else:
        return ''


def conversion_row_hook(context, file_, article):
    """ Provides a verbose menu for pandoc transformations in a row format"""

    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    request = context["request"]
    pandoc_enabled = setting_handler.get_plugin_setting(
        plugin,
        'pandoc_enabled',
        request.journal,
        create=True,
        pretty='Pandoc Enabled',
        types='boolean',
    )

    if pandoc_enabled.processed_value:
        context={'article': article, 'file': file_}
        return render_to_string(
                "pandoc_plugin/row_hook.html",
                context=context,
                request=request,
        )
    else:
        return ''
