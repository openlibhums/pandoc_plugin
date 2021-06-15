from django.template.loader import render_to_string
from utils import setting_handler


def inject_pandoc(context):
    """
    Provides buttons for users to automatically convert manuscript files (docx or rtf) to html.
    Uses the pandoc plugin, which must be installed on the server.
    """
    request = context.get('request')
    pandoc_enabled = setting_handler.get_setting(
        setting_group_name="plugin:pandoc",
        setting_name="pandoc_enabled",
        journal=request.journal,
    )

    if pandoc_enabled.processed_value:
        return render_to_string(
            'pandoc/inject.html',
            context={
                'article': context.get('article'),
                'file': context.get('file')},
            request=request,
        )
    else:
        return ''


def conversion_row_hook(context, file_, article):
    """ Provides a verbose menu for pandoc transformations in a row format"""
    request = context["request"]
    pandoc_enabled = setting_handler.get_setting(
        setting_group_name="plugin:pandoc",
        setting_name="pandoc_enabled",
        journal=request.journal,
    )

    if pandoc_enabled.processed_value:
        context = {'article': article, 'file': file_}
        return render_to_string(
            "pandoc/row_hook.html",
            context=context,
            request=request,
        )
    else:
        return ''
