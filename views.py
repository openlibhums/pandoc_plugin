from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.urls import reverse

from plugins.pandoc_plugin import forms, plugin_settings

from submission import models as sub_models
from core import models as core_models
from production import logic

from utils import setting_handler, models

import os
import subprocess

def index(request):
    '''
    Render admin page allowing users to enable or disable the plugin
    '''
    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    pandoc_enabled = setting_handler.get_plugin_setting(plugin, 'pandoc_enabled', request.journal, create=True,
                                                        pretty='Enable Pandoc', types='boolean').processed_value
    admin_form = forms.PandocAdminForm(initial={'pandoc_enabled': pandoc_enabled})

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


def convert(request, article_id=None, file_id=None):
    '''
    If request is POST, try to get article's manuscript file (should be docx or rtf), convert to markdown, then convert to html,
    save new files in applicable locations, register as Galley objects in database. Refresh submission page with new galley objects.
    If request is GET, render button to convert.
    '''

    # if post, get the original manuscript file, convert to html or xml based on which button the user clicked
    if request.method == "POST":

        # retrieve article and selected manuscript
        article = get_object_or_404(sub_models.Article, pk=article_id)
        manuscript = get_object_or_404(core_models.File, pk=file_id)

        orig_path = manuscript.self_article_path()
        
        # generate a filename for the intermediate md file - raise error if unexpected manuscript file type
        stripped_path, exten = os.path.splitext(orig_path)

        if exten not in ['.docx', '.rtf']:
            raise TypeError('Unexpected Manuscript File Type')

        temp_md_path = stripped_path + '.md'

        # construct and execute subprocess.run() command to create intermediate md file
        pandoc_command = ['pandoc', '-s', orig_path, '-t', 'markdown', '-o', temp_md_path]
        subprocess.run(pandoc_command)

        # TODO: make md file galley, child of original article
        # DOES THE FILE I'M PASSING NEED TO BE IN MEMORY RATHER THAN A PATH TO THE FILE ON SERVER?

        #logic.save_galley(article, request, temp_md_path, True, "Other", True, save_to_disk=False)

        # convert to html or xml, passing article's title as metadata
        metadata = '--metadata=title:"{}"'.format(article.title)

        if request.POST.get('convert_html'):

            output_path = stripped_path + '.html'
            pandoc_command = ['pandoc', '-s', temp_md_path, '-o', output_path, metadata]
            subprocess.run(pandoc_command)
            logic.save_galley(article, request, output_path, True, 'HTML', False, save_to_disk=False)

        elif request.POST.get('convert_xml'):

            output_path = stripped_path + '.xml'
            pandoc_command = ['pandoc', '-s', temp_md_path, '-o', output_path, metadata]
            subprocess.run(pandoc_command)
            logic.save_galley(article, request, output_path, True, 'XML', False, save_to_disk=False)
        
            # TODO: make new file child of manuscript file

        return redirect(reverse('production_article', kwargs={'article_id': article.pk}))

    # render buttons if GET request
    else:
        return reverse('production_article', kwargs={'article_id': request.article.pk})
        
# NEED LOGIC FOR IF HTML OR XML ALREADY GENERATED