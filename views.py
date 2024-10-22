import os

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.core.files.base import ContentFile
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST

from core import models as core_models
from production import logic
from security.decorators import production_user_or_editor_required
from submission import models as sub_models
from utils import setting_handler, models

from plugins.pandoc_plugin import forms, plugin_settings, convert


def index(request):
    """
    Render admin page allowing users to enable or disable the plugin
    """
    plugin = models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    pandoc_enabled = setting_handler.get_plugin_setting(plugin, 'pandoc_enabled', request.journal, create=True,
                                                        pretty='Enable Pandoc', types='boolean').processed_value
    extract_images = setting_handler.get_plugin_setting(
        plugin, 'pandoc_extract_images', request.journal, create=True,
        pretty='Pandoc extract images', types='boolean').processed_value

    admin_form = forms.PandocAdminForm(initial={
        'pandoc_enabled': pandoc_enabled,
        'pandoc_extract_images': extract_images,
    })

    if request.POST:
        admin_form = forms.PandocAdminForm(request.POST)

        if admin_form.is_valid():
            for setting_name, setting_value in admin_form.cleaned_data.items():
                setting_handler.save_plugin_setting(plugin, setting_name, setting_value, request.journal)
                messages.add_message(request, messages.SUCCESS, '{0} setting updated.'.format(setting_name))

            return redirect(reverse('pandoc_index'))

    template = "pandoc_plugin/index.html"
    context = {
        'admin_form': admin_form,
    }

    return render(request, template, context)


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

    galley = logic.save_galley(
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
            logic.save_galley_image(galley, request, image_file, image_name,
                                    fixed=False)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@require_POST
@production_user_or_editor_required
def convert_to_pdf(request, article_id, file_id):
    """
    Retrieve an article's manuscript file, convert it to PDF using Pandoc,
    handle embedded images, and register it as a galley.
    """
    article = get_object_or_404(
        sub_models.Article,
        pk=article_id,
    )
    manuscript = get_object_or_404(
        core_models.File,
        pk=file_id,
        article_id=article.pk,
    )
    file_path = manuscript.self_article_path()

    try:
        pdf_output_path, image_paths = convert.generate_pdf_from_doc(
            file_path,
            manuscript.mime_type,
        )
    except (TypeError, convert.PandocError) as e:
        messages.error(request, f'Error during PDF conversion: {str(e)}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    galley = logic.save_galley(
        article,
        request,
        pdf_output_path,
        True,
        'PDF',
        save_to_disk=False,
    )

    for image_path in image_paths:
        image_name = os.path.basename(image_path)
        with open(image_path, 'rb') as image_reader:
            image_file = ContentFile(image_reader.read())
            image_file.name = image_name
            logic.save_galley_image(
                galley,
                request,
                image_file,
                image_name,
                fixed=False,
            )

    messages.success(request, 'PDF generated successfully')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
