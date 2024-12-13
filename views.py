import os

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST

from core import models as core_models
from production import logic as production_logic
from security.decorators import production_user_or_editor_required
from submission import models as sub_models
from utils import setting_handler, models

from plugins.pandoc_plugin import forms, plugin_settings, convert, logic


def index(request):
    """Render admin page for configuring the Pandoc plugin."""
    form = forms.PandocAdminForm(
        journal=request.journal,
    )

    if request.method == 'POST':
        form = forms.PandocAdminForm(
            request.POST,
            journal=request.journal,
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Settings updated successfully',
            )
            return redirect('pandoc_index')

    return render(
        request,
        'pandoc_plugin/index.html',
        {'admin_form': form},
    )


@require_POST
@production_user_or_editor_required
def convert_file(request, article_id=None, file_id=None):
    """
    Try to get article's manuscript file (should be docx or rtf), convert to markdown, then convert to html,
    save new files in applicable locations, register as Galley objects in database. Refresh submission page with new galley objects.
    If request is GET, render button to convert.
    """

    # retrieve article and selected manuscript
    article = get_object_or_404(sub_models.Article, pk=article_id)
    manuscript = get_object_or_404(core_models.File,
                                   pk=file_id, article_id=article.pk)
    file_path = manuscript.self_article_path()

    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    extract_images = setting_handler.get_plugin_setting(
        plugin, 'pandoc_extract_images', request.journal, create=True,
        pretty='Pandoc extract images', types='boolean').processed_value

    try:
        html, images = convert.generate_html_from_doc(file_path, extract_images)
    except (TypeError, convert.PandocError) as err:
        messages.add_message(request, messages.ERROR, err)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    stripped, _ = os.path.splitext(file_path)
    output_path = stripped + '.html'
    with open(output_path, mode="w", encoding="utf-8") as html_file:
        print(html, file=html_file)

    galley = production_logic.save_galley(
        article,
        request,
        output_path,
        True,
        'HTML',
        save_to_disk=False,
    )
    messages.add_message(request, messages.INFO, "HTML generated successfully")

    for image in images:
        image_name = os.path.basename(image)
        with open(image, 'rb') as image_reader:
            image_file = ContentFile(image_reader.read())
            image_file.name = image_name
            production_logic.save_galley_image(
                galley,
                request,
                image_file,
                image_name,
                fixed=False,
            )

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@require_POST
@production_user_or_editor_required
def convert_to_pdf(request, article_id, file_id):
    conversion_type = request.POST.get('convert_pdf')
    print(request.POST)
    if conversion_type and conversion_type in ['stamped', 'unstamped']:
        try:
            # Generate the PDF with a cover sheet
            final_pdf_path, article = logic.generate_pdf_with_cover_sheet(
                article_id=article_id,
                file_id=file_id,
                journal=request.journal,
                conversion_type=conversion_type
            )

            # Save the merged PDF as a galley
            production_logic.save_galley(
                article=article,
                request=request,
                uploaded_file=final_pdf_path,
                is_galley=True,
                label="PDF",
                save_to_disk=False,
                public=True,
            )

            if conversion_type == "stamped":
                message = "PDF with cover sheet generated successfully."
            else:
                message = "PDF without cover sheet generated successfully"
            messages.success(
                request,
                message,
            )
        except Exception as e:
            messages.error(request, f"Error during PDF generation: {str(e)}")
    else:
        messages.add_message(
            request,
            messages.WARNING,
            'Conversion type must be either stamped or unstamped.',
        )
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
