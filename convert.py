import mimetypes
import os
import subprocess
import tempfile

from django.conf import settings

from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger

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


def generate_pdf_with_cover_sheet(doc_path, mime_type, cover_sheet_html):
    if mime_type not in plugin_settings.PDF_CONVERSION_SUPPORTED_MIME_TYPES:
        raise TypeError(f"File MIME type {mime_type} not supported")

    images_temp_path = tempfile.mkdtemp()
    cover_pdf_path = os.path.join(tempfile.gettempdir(), 'cover_sheet.pdf')
    document_pdf_path = os.path.join(tempfile.gettempdir(),
                                     f'{os.path.basename(doc_path)}_document.pdf')
    merged_pdf_path = os.path.join(tempfile.gettempdir(),
                                   f'{os.path.basename(doc_path)}_merged.pdf')

    try:
        subprocess.run(
            [
                'pandoc',
                '-o',
                cover_pdf_path,
                '--from=html',
                '--to=pdf',
                '--pdf-engine=xelatex',
            ],
            input=cover_sheet_html.encode(),
            check=True,
        )
    except subprocess.CalledProcessError as err:
        raise PandocError(
            f"Error during cover sheet PDF conversion: {str(err)}")

    pandoc_command = (
        PANDOC_CMD
        + MEMORY_LIMIT_ARG
        + [EXTRACT_MEDIA, images_temp_path]
        + [doc_path, '-o', document_pdf_path, '--pdf-engine=xelatex']
    )

    try:
        logger.info(f"[PANDOC] Running command: {pandoc_command}")
        subprocess.run(pandoc_command, check=True)
    except subprocess.CalledProcessError as e:
        raise PandocError(f"PandocError: {e.stderr}")

    image_paths = [
        os.path.join(base, f)
        for base, _, files in os.walk(images_temp_path)
        for f in files
        if mimetypes.guess_type(f)[0] in IMAGE_MIMETYPES
    ]

    merger = PdfMerger()
    merger.append(cover_pdf_path)
    merger.append(document_pdf_path)
    with open(merged_pdf_path, 'wb') as merged_file:
        merger.write(merged_file)

    return merged_pdf_path, image_paths


def convert_word_to_pdf(doc_path, output_filename):
    """Convert Word doc (docx, rtf, odt, etc.) to PDF using Pandoc with MIME type validation."""
    mime_type, _ = mimetypes.guess_type(doc_path)

    if mime_type not in plugin_settings.PDF_CONVERSION_SUPPORTED_MIME_TYPES:
        raise TypeError(f"Unsupported file type for conversion: {mime_type}")

    output_pdf_path = os.path.join(settings.BASE_DIR, 'files', 'temp',
                                   output_filename)

    pandoc_command = [
        'pandoc',
        doc_path,
        '-o',
        output_pdf_path,
        '--pdf-engine=xelatex',
        '-V',
        'geometry:margin=1.5in',
    ]

    try:
        subprocess.run(pandoc_command, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error converting Word document to PDF: {e}")

    return output_pdf_path


def convert_html_to_pdf(html_content, output_filename):
    """Convert HTML content to PDF using Pandoc."""
    output_pdf_path = os.path.join(
        settings.BASE_DIR,
        'files',
        'temp',
        output_filename,
    )

    try:
        subprocess.run(
            [
                'pandoc',
                '--from=html',
                '--to=pdf',
                '-o',
                output_pdf_path,
                '--pdf-engine=xelatex',
                "-V",
                "pagestyle=empty",
                "-V",
                "geometry:margin=1.5in",
            ],
            input=html_content.encode(),
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error converting HTML to PDF: {e}")

    return output_pdf_path


def merge_pdfs(cover_pdf, doc_pdf, output_filename):
    """Merge two PDFs (cover sheet and document) into one."""
    output_pdf_path = os.path.join(settings.BASE_DIR, 'files', 'temp', output_filename)

    merger = PdfMerger()

    try:
        merger.append(cover_pdf)
        merger.append(doc_pdf)
        with open(output_pdf_path, 'wb') as merged_pdf:
            merger.write(merged_pdf)
    except Exception as e:
        raise Exception(f"Error merging PDFs: {e}")
    finally:
        merger.close()

    return output_pdf_path


class PandocError(Exception):
    def __init__(self, msg, cmd=None):
        super().__init__(self, msg)
        self.cmd = cmd
