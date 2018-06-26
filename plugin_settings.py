PLUGIN_NAME = 'Pandoc Plugin'
DESCRIPTION = 'A plugin to assist typesetters with converting docx/rtf files to html or xml'
AUTHOR = 'Drew Stimson and Daniel Evans'
VERSION = 0.1
SHORT_NAME = 'pandoc'
MANAGER_URL = 'pandoc_index'

from utils import models

def install():
    new_plugin, created = models.Plugin.objects.get_or_create(name=SHORT_NAME, version=VERSION, enabled=True)

    if created:
        print('Plugin {0} installed.'.format(PLUGIN_NAME))
    else:
        print('Plugin {0} is already installed.'.format(PLUGIN_NAME))

def hook_registry():
    '''
    When site with hooks loaded, this is run for each plugin to create list of plugins
    '''
    # Will want something like return {'conversion_button': {'module': 'plugins.pandoc_plugin.hooks', 'function': 'inject_pandoc'}}
    pass