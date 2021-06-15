from utils import models
from utils import plugins
from utils.install import update_settings

PLUGIN_NAME = 'pandoc'
DESCRIPTION = 'A plugin to assist typesetters with converting docx/rtf files to html'
AUTHOR = 'Drew Stimson and Daniel Evans'
VERSION = 0.4
JANEWAY_VERSION = '1.3.6'
SHORT_NAME = 'pandoc'
MANAGER_URL = 'pandoc_index'

MEMORY_LIMIT_MB = 512


class PandocPlugin(plugins.Plugin):
    plugin_name = PLUGIN_NAME
    display_name = 'Pandoc Plugin'
    description = DESCRIPTION
    author = AUTHOR
    short_name = SHORT_NAME

    manager_url = MANAGER_URL

    version = VERSION
    janeway_version = JANEWAY_VERSION

    is_workflow_plugin = False


def install():
    PandocPlugin.install()
    update_settings(
        file_path='plugins/pandoc/install/settings.json'
    )


def hook_registry():
    """
    When site with hooks loaded, this is run for each plugin to create list of plugins
    """
    return {
            'conversion_buttons': {
                'module': 'plugins.pandoc.hooks',
                'function': 'inject_pandoc',
            },
            'conversion_row': {
                'module': 'plugins.pandoc.hooks',
                'function': 'conversion_row_hook',
            },
    }
