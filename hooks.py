from django.template import loader, RequestContext
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings

if settings.URL_CONFIG = 'path':
    from core.monkeypatch import reverse
else:
    from django.shortcuts import reverse

from plugins.pandoc_plugin import plugin_settings
from utils import models, setting_handler
from submission import models as sub_models
from core import models as core_models
from production import logic

import subprocess


def inject_pandoc(context):
    '''
    Provides buttons for users to automatically convert manuscript files (docx or rtf) to html or xml.
    Uses the pandoc plugin, which must be installed on the server. Expects an article's pk to be passed
    as part of context.
    '''
    plugin = plugin_settings.get_self()

    # get article info
    request = context.get('request')
    article_id = context.get('article_id')
    article = get_object_or_404(sub_models.Article, pk=article_id)

    # if post, get the original manuscript file, convert to html or xml based on which button the user clicked
    if request.method == "POST":
        manuscripts = article.manuscript_files.filter(is_galley=False)

        # make sure there is at least one manuscript, if so get the first entry
        if len(manuscripts) > 0:
            orig_path = manuscripts[0].self_article_path()
            
            # generate a filename for the intermediate md file - raise error if unexpected file type
            if orig_path.endswith('.docx'):
                temp_md_path = orig_path[:-5]
                temp_md_path += '.md'
            elif orig_path.endswith('.rtf'):
                temp_md_path = orig_path[:-4]
                temp_md_path += '.md'
            else:
                raise TypeError('Unexpected Manuscript File Type')

            # construct and execute subprocess.run() command to create intermediate md file
            pandoc_command = ['pandoc', '-s', orig_path, '-t', 'markdown', '-o', temp_md_path]
            subprocess.run(pandoc_command)

            # TODO: make md file galley, child of original article

            # strip md off file path
            output_path = temp_md_path[:-3]

            # convert to html or xml, passing article's title as metadata
            metadata = '--metadata=title:"{}"'.format(article.title)
            if request.POST.get('convert_html'):

                output_path += '.html'
                pandoc_command = ['pandoc', '-s', temp_md_path, '-o', output_path, metadata]
                subprocess.run(pandoc_command)

            elif request.POST.get('convert_xml'):

                output_path += '.xml'
                pandoc_command = ['pandoc', '-s', temp_md_path, '-o', output_path, metadata]
                subprocess.run(pandoc_command)
        
            # TODO: make new galleys children of manuscript file

        return redirect(reverse('production_article', kwargs={'article_id': article.pk}))

    # render buttons if GET request
    else:

        return render(request, 'pandoc_plugin/inject.html')



'''
def inject_pandoc(context):
    request = context.get('request')
    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    pandoc_shortname = setting_handler.get_plugin_setting(plugin, 'pandoc_shortname', request.journal)
    pandoc_enabled = setting_handler.get_plugin_setting(plugin, 'pandoc_enabled', request.journal)

    if not pandoc_enabled.value:
        return

    template = loader.get_template('pandoc_plugin/inject.html')
    pandoc_context = {'pandoc_shortname': pandoc_shortname.processed_value}
    html_content = template.render(pandoc_context)

    return html_content

    # OR

    plugin = plugin_setings.get_self()

    embed_html = '<form method="post"><button type="submit">Automatically generate html galley</button></form>'

    return embed_html
'''

# Useful functions from core.files:
# copy_local_file_to_article(file_to_handle, file_name, article, owner, label=None, description=None, replace=None, galley=False)
# save_file_to_article(file_to_handle, article, owner, label=None, description=None, replace=None, is_galley=False, save=True)
# save_file_to_disk(file_to_handle, filename, folder_structure)
# file_children(file):
# create_temp_file(content, filename)
