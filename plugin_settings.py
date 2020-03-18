from utils import models

PLUGIN_NAME = 'Pandoc Plugin'
DESCRIPTION = 'A plugin to assist typesetters with converting docx/rtf files to html'
AUTHOR = 'Drew Stimson and Daniel Evans'
VERSION = 0.2
JANEWAY_VERSION = '1.3.6'
SHORT_NAME = 'pandoc_plugin'
MANAGER_URL = 'pandoc_index'


def install():
    new_plugin, created = models.Plugin.objects.get_or_create(
        name=SHORT_NAME,
        enabled=True,
        defaults={'version': VERSION},
    )

    if created:
        print('Plugin {0} installed.'.format(PLUGIN_NAME))
    else:
        print('Plugin {0} is already installed.'.format(PLUGIN_NAME))

    models.PluginSetting.objects.get_or_create(name='pandoc_enabled',
                                               plugin=new_plugin,
                                               types='boolean',
                                               pretty_name='Enable Pandoc Plugin',
                                               description='Enable Pandoc Conversion Plugin',
                                               is_translatable=False)


def hook_registry():
    """
    When site with hooks loaded, this is run for each plugin to create list of plugins
    """
    return {
            'conversion_buttons': {
                'module': 'plugins.pandoc_plugin.hooks',
                'function': 'inject_pandoc',
            },
            'conversion_row': {
                'module': 'plugins.pandoc_plugin.hooks',
                'function': 'conversion_row_hook',
            },
    }
