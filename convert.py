import mimetypes
import os
import subprocess
import tempfile

from bs4 import BeautifulSoup
from core.files import IMAGE_MIMETYPES
from utils import models, setting_handler
from utils.logger import get_logger

from plugins.pandoc_plugin import plugin_settings

logger = get_logger(__name__)

# Argument added to all calls to pandoc that caps the size of Pandoc's heap,
# preventing maliciously formatted files from triggering a runaway
# conversion process.
MEMORY_LIMIT_ARG = ['+RTS', '-M{}M'.format(plugin_settings.MEMORY_LIMIT_MB), '-RTS']
EXTRACT_MEDIA = "--extract-media"
PANDOC_CMD = ['pandoc']


def generate_html_from_doc(doc_path, extract_images=False):
    """ Generates an HTML galley from the given document path
    :param doc_path: A string with the path to the file to be converted
    :return: The string with the produced HTML and an iterable of paths to the
        extracted images
    """
    _, extension = os.path.splitext(doc_path)
    if extension not in ['.docx', '.rtf']:
        raise TypeError("File Extension {} not supported".format(extension))

    images_temp_path = tempfile.mkdtemp()
    if extract_images:
        extract_images_arg = [EXTRACT_MEDIA, images_temp_path]
    else:
        extract_images_arg = []

    pandoc_command = (
            PANDOC_CMD
            + MEMORY_LIMIT_ARG
            + extract_images_arg
            + ['-s', doc_path, '-t', 'html']
    )
    try:
        logger.info("[PANDOC] Running command '{}'".format(pandoc_command))
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


def generate_pdf_from_doc(doc_path, mime_type):
    """Generates a PDF galley from the given document path and handles images.

    :param doc_path: A string with the path to the file to be converted
    :param mime_type: MIME type of the file to be validated
    :return: The path to the generated PDF and an iterable of paths to the extracted images
    """
    # Validate if the MIME type is supported
    if mime_type not in plugin_settings.PDF_CONVERSION_SUPPORTED_MIME_TYPES:
        raise TypeError(f"File MIME type {mime_type} not supported")

    # Temporary directory to extract images
    images_temp_path = tempfile.mkdtemp()

    pandoc_command = (
        PANDOC_CMD
        + MEMORY_LIMIT_ARG
        + [EXTRACT_MEDIA, images_temp_path]
        + [doc_path, '-o', f'{os.path.splitext(doc_path)[0]}.pdf']
    )

    try:
        logger.info(f"[PANDOC] Running command: {pandoc_command}")
        subprocess.run(pandoc_command, check=True)
    except subprocess.CalledProcessError as e:
        raise PandocError(f"PandocError: {e.stderr}")

    # Extract image paths
    image_paths = [
        os.path.join(base, f)
        for base, _, files in os.walk(images_temp_path)
        for f in files
        if mimetypes.guess_type(f)[0] in IMAGE_MIMETYPES
    ]

    pdf_output_path = f'{os.path.splitext(doc_path)[0]}.pdf'

    return pdf_output_path, image_paths


class PandocError(Exception):
    def __init__(self, msg, cmd=None):
        super().__init__(self, msg)
        self.cmd = cmd

