from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import get_object_or_404

from plugins.pandoc_plugin import forms
from plugins.pandoc_plugin import plugin_settings

from core import models
from submission import models as sub_models

from utils import setting_handler
from utils import models

import os
import subprocess

def index(request):
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

def convert(request, article_id):
    '''
    If request is POST, try to get article's manuscript file (should be docx or rtf), convert to markdown, then convert to html,
    save new files in applicable locations, register as Galley objects in database. Refresh submission page with new galley objects.
    If request is GET, render button to convert.
    '''

    # if post, get the original manuscript file, convert to html or xml based on which button the user clicked
    if request.method == "POST":

        # get article and manuscript info
        if request.POST.get('convert_html'):
            article_id = request.POST['convert_html']
        elif request.POST.get('convert_xml'):
            article_id = request.POST['convert_xml']

        article = get_object_or_404(sub_models.Article, pk=article_id)
        manuscripts = article.manuscript_files.filter(is_galley=False)

        # make sure there is at least one manuscript, if so get the first entry
        if len(manuscripts) > 0:
            orig_path = manuscripts[0].self_article_path()
            
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
            logic.save_galley(article, request, temp_md_path, True, "Other", True)

            # convert to html or xml, passing article's title as metadata
            metadata = '--metadata=title:"{}"'.format(article.title)

            if request.POST.get('convert_html'):

                output_path = stripped_path + '.html'
                pandoc_command = ['pandoc', '-s', temp_md_path, '-o', output_path, metadata]
                subprocess.run(pandoc_command)
                logic.save_galley(article, request, output_path, True, 'HTML', False)

            elif request.POST.get('convert_xml'):

                output_path = stripped_path + '.xml'
                pandoc_command = ['pandoc', '-s', temp_md_path, '-o', output_path, metadata]
                subprocess.run(pandoc_command)
                logic.save_galley(article, request, output_path, True, 'XML', False)
        
            # TODO: make new file galley and child of manuscript file
            # AM I MAKING TWO COPIES OF THESE FILES? DO I NEED TO DELETE THE FILES CREATED BY PANDOC?

        return redirect(reverse('production_article', kwargs={'article_id': article.pk}))

    # render buttons if GET request
    else:
        return reverse('production_article', kwargs={'article_id': request.article.pk})
        
        # DO I NEED TO PASS CONTEXT FOR HOOK?
        # NEED LOGIC FOR IF HTML OR XML ALREADY GENERATED

        



