import os

from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.template.loader import render_to_string
from django.conf import settings

from plugins.pandoc_plugin import plugin_settings, convert
from utils import setting_handler
from submission.models import Article
from core.models import File


def generate_pdf_with_cover_sheet(
    article_id,
    file_id,
    journal=None,
    temp_dir=None,
    conversion_type="stamped",
):
    # Fetch article and manuscript
    article = get_object_or_404(Article, pk=article_id)
    manuscript = get_object_or_404(File, pk=file_id, article_id=article.pk)

    # Fetch plugin settings
    plugin = plugin_settings.PandocPlugin.get_self()

    # Set up temporary directory
    if temp_dir is None:
        temp_dir = os.path.join(settings.BASE_DIR, "files", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    doc_pdf_path = cover_pdf_path = merged_pdf_path = None

    try:
        # Convert the Word document to PDF
        file_path = manuscript.self_article_path()
        doc_pdf_path = convert.convert_word_to_pdf(
            file_path,
            f"{manuscript.pk}_document.pdf",
        )

        if conversion_type == "stamped":
            # Fetch and render the cover sheet HTML
            cover_sheet_html = setting_handler.get_plugin_setting(
                plugin=plugin,
                setting_name="cover_sheet",
                journal=journal or article.journal,
                create=True,
            ).processed_value
            context = Context({"article": article})
            rendered_html = Template(cover_sheet_html).render(context)

            # Convert the HTML cover sheet to PDF
            cover_pdf_path = convert.convert_html_to_pdf(
                rendered_html,
                f"{manuscript.pk}_cover.pdf",
            )

            # Merge the PDFs
            merged_pdf_path = convert.merge_pdfs(
                cover_pdf_path,
                doc_pdf_path,
                f"{manuscript.pk}_merged.pdf",
            )

            # Set the final PDF path
            final_pdf_path = merged_pdf_path
        else:
            # If no cover sheet, the final PDF is the converted Word document
            final_pdf_path = doc_pdf_path

        # Ensure the target directory exists
        target_directory = os.path.join(
            settings.BASE_DIR,
            "files",
            "articles",
            str(article.pk),
        )
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        # Set the target path for the final PDF
        final_target_path = os.path.join(
            target_directory,
            os.path.basename(final_pdf_path),
        )

        # Move the final PDF to the correct directory if necessary
        if final_pdf_path != final_target_path:
            os.rename(final_pdf_path, final_target_path)

        return final_target_path, article

    finally:
        # Clean up temp files if they exist
        for temp_file in [doc_pdf_path, cover_pdf_path, merged_pdf_path]:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

