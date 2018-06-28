from django.template import loader, RequestContext
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings

from django.urls import reverse

from plugins.pandoc_plugin import plugin_settings
from utils import models, setting_handler
from submission import models as sub_models
from core import models as core_models
from production import logic

import subprocess

def inject_pandoc(context):
    '''
    Provides buttons for users to automatically convert manuscript files (docx or rtf) to html or xml.
    Uses the pandoc plugin, which must be installed on the server.
    '''
    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    request = context.get('request')
    pandoc_enabled = setting_handler.get_plugin_setting(plugin, 'pandoc_enabled', request.journal)

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
