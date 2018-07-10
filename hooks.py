from django.shortcuts import render

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
        return render(request, 'pandoc_plugin/inject.html')

# Useful functions from core.files:
# copy_local_file_to_article(file_to_handle, file_name, article, owner, label=None, description=None, replace=None, galley=False)
# save_file_to_article(file_to_handle, article, owner, label=None, description=None, replace=None, is_galley=False, save=True)
# save_file_to_disk(file_to_handle, filename, folder_structure)
# file_children(file):
# create_temp_file(content, filename)
