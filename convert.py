import mimetypes
import os
import subprocess
import tempfile

from bs4 import BeautifulSoup, Comment
from PIL import Image, UnidentifiedImageError

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

def resize_image(img_path, size):
    try:
        img = Image.open(img_path)
    except FileNotFoundError:
        logger.warning("File not found, can't resize: %s" % img_path)
        return
    except UnidentifiedImageError:
        # Could be an SVG
        return

    img = img.resize((size[0], size[1]), Image.LANCZOS)

    img.save(img_path, "png")

def get_img_size(style, default_dpi):
    styles = dict(s.split(":") for s in style.split(";"))
    w = styles.get("width", False)
    h = styles.get("height", False)
    if w and h:
        w = float(w.strip("in"))
        h = float(h.strip("in"))
        return (int(w * default_dpi[0]), int(h * default_dpi[1]))
    return False

def generate_html_from_doc(doc_path, extract_images=False, resize_images=False, default_dpi=(96, 96)):
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
    dropped_images = []
    for img in pandoc_soup.find_all("img"):
        tmp_img_path = img["src"]

        if (
            not os.path.isfile(tmp_img_path)
            or mimetypes.guess_type(tmp_img_path)[0] not in IMAGE_MIMETYPES
        ):
            original_name = os.path.basename(tmp_img_path)
            dropped_images.append(original_name)
            img.replace_with(Comment(
                " pandoc_plugin: image '{}' was not included — its format "
                "isn't supported for web display (JPEG, PNG, GIF, TIFF, and "
                "AVIF are), or image extraction was turned off for this "
                "journal. Re-embed it as a supported image format (e.g. via "
                "'Paste Special > Picture (PNG)' in Word) and regenerate. "
                .format(original_name)
            ))
            continue

        # Replace pandoc path to image with filename
        img["src"] = os.path.basename(img["src"])

        if resize_images and img.has_attr("style"):
            size = get_img_size(img["style"], default_dpi)
            if size:
                resize_image(tmp_img_path, size)

        # Undo pandoc guess of height/width attributes of images.
        del img["style"]

    if dropped_images:
        logger.warning(
            "[PANDOC] {} image(s) referenced in the source document could "
            "not be converted and were replaced with a comment in the "
            "generated HTML: {}".format(
                len(dropped_images), ", ".join(dropped_images)
            )
        )

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

