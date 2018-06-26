from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from plugins.pandoc_plugin import forms
from plugins.pandoc_plugin import plugin_settings

from core import models
from submission import models as sub_models

from utils import setting_handler
from utils import models

import os

def index(request):
    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    pandoc_shortname = setting_handler.get_plugin_setting(plugin, 'pandoc_shortname', request.journal, create=True,
                                                          pretty='Pandoc Shortname', types='text').processed_value
    pandoc_enabled = setting_handler.get_plugin_setting(plugin, 'pandoc_enabled', request.journal, create=True,
                                                        pretty='Enable Pandoc', types='boolean').processed_value
    admin_form = forms.PandocAdminForm(initial={'pandoc_shortname': pandoc_shortname, 'pandoc_enabled': pandoc_enabled})

    if request.POST:
        admin_form = forms.PandocAdminForm(request.POST)

        if admin_form.is_valid():
            for setting_name, setting_value in admin_form.cleaned_data.items():
                setting_handler.save_plugin_setting(plugin, setting_name, setting_value, request.journal)
                messages.add_message(request, messages.SUCCESS, '{0} setting updated.'.format(setting_name))

            return redirect(reverse('pandoc_index'))

    template = "pandoc_plugin/index.html"
    context = {
        'admin_form': admin_form,
    }

    return render(request, template, context)

def convert(request, article_id):
    '''
    If request is POST, try to get article's manuscript file (should be docx or rtf), convert to markdown, then convert to html,
    save new files in applicable locations, register as Galley objects in database. Refresh submission page with new galley objects.
    If request is GET, render button to convert.
    '''

    if request.POST:
        article = get_object_or_404(sub_models.Article, pk=article_id)
        man_file = get_object_or_404(models.File, article_id=article_id, is_galley=False)

        



