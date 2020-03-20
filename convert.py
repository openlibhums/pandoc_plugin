import mimetypes
import os
import subprocess
import tempfile

from bs4 import BeautifulSoup
from core.files import IMAGE_MIMETYPES
from utils.logger import get_logger

from plugins.pandoc_plugin import plugin_settings

logger = get_logger(__name__)

# Argument added to all calls to pandoc that caps the size of Pandoc's heap,
# preventing maliciously formatted files from triggering a runaway
# conversion process.
MEMORY_LIMIT_ARG = ['+RTS', '-M{}M'.format(plugin_settings.MEMORY_LIMIT_MB), '-RTS']
EXTRACT_MEDIA = "--extract-media"
PANDOC_CMD = ['pandoc']


def generate_html_from_doc(doc_path):
    """ Generates an HTML galley from the given document path
    :param doc_path: A string with the path to the file to be converted
    :return: The string with the produced HTML and an iterable of paths to the
        extracted images
    """
    _, extension = os.path.splitext(doc_path)
    if extension not in ['.docx', '.rtf']:
        raise TypeError("File Extension {} not supported".format(extension))

    images_temp_path = tempfile.mkdtemp()
    extract_images_arg = [EXTRACT_MEDIA, images_temp_path]

    pandoc_command = (
            PANDOC_CMD
            + MEMORY_LIMIT_ARG
            + extract_images_arg
            + ['-s', doc_path, '-t', 'html']
    )
    try:
        logger.info("[PANDOC]: Running coversion on {}".format(doc_path))
        pandoc_return = subprocess.run(
                pandoc_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
        )
    except subprocess.CalledProcessError as e:
        raise PandocError("PandocError: {e.stderr}".format(e=e))

    # Formatting
    pandoc_soup = BeautifulSoup(pandoc_return.stdout, 'html.parser')
    for img in pandoc_soup.find_all("img"):
        # Replace pandoc path to image with filename
        img["src"] = os.path.basename(img["src"])
        # Undo pandoc guess of height/width attributes of images.
        del img["style"]

    image_paths = [
        os.path.join(base, f)
        for base, dirs, files in os.walk(images_temp_path)
        for f in files
        if mimetypes.guess_type(f)[0] in IMAGE_MIMETYPES
    ]
    logger.debug("[PANDOC] Extracted {} images".format(len(image_paths)))

    return str(pandoc_soup), image_paths


class PandocError(Exception):
    def __init__(self, msg, cmd=None):
        super().__init__(self, msg)
        self.cmd = cmd

