from bs4 import BeautifulSoup
import os
import subprocess
from production import logic

from plugins.pandoc_plugin import plugin_settings

# Argument added to all calls to pandoc that caps the size of Pandoc's heap,
# preventing maliciously formatted files from triggering a runaway
# conversion process.
MEMORY_LIMIT_ARG = ['+RTS', '-M{}M'.format(plugin_settings.MEMORY_LIMIT_MB), '-RTS']
PANDOC_CMD = ['pandoc']


def generate_html_from_doc(article, manuscript, request):
    """ Generates an HTML galley
    """
    orig_path = manuscript.self_article_path()
    stripped_path, exten = os.path.splitext(orig_path)
    if exten not in ['.docx', '.rtf']:
        raise TypeError("File Extension {} not supported".format(extension))

    output_path = stripped_path + '.html'
    pandoc_command = (
            PANDOC_CMD
            + MEMORY_LIMIT_ARG
            + ['-s', orig_path, '-t', 'html']
    )
    try:
        pandoc_return = subprocess.run(
                pandoc_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
        )
    except subprocess.CalledProcessError as e:
        raise PandocError("PandocError: {e.stderr}".format(e))

    # Formatting
    pandoc_soup = BeautifulSoup(pandoc_return.stdout, 'html.parser')
    for img in pandoc_soup.find_all("img"):
    # Pandoc adds `media/` to the src attributes of img tags
        img["src"] = img["src"].replace("media/", "")
        # Undo pandoc guess of height/width attributes of images.
        del img["style"]

    with open(output_path, mode="w", encoding="utf-8") as html_file:
        print(pandoc_soup, file=html_file)

    logic.save_galley(article, request, output_path, True, 'HTML', save_to_disk=False)
    #return str(pandoc_soup)


class PandocError(Exception):
    def __init__(self, msg, cmd=None):
        super().__init__(self, msg)
        self.cmd = cmd

