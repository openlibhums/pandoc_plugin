from django.urls import re_path

from plugins.pandoc_plugin import views

urlpatterns = [
    re_path(
        r'^$',
        views.index,
        name='pandoc_index',
    ),
    re_path(
        r'^convert/(?P<article_id>\d+)/file/(?P<file_id>\d+)/$',
        views.convert_file,
        name='pandoc_convert',
    ),
    re_path(
        r'^convert-to-pdf/(?P<article_id>\d+)/(?P<file_id>\d+)/$',
        views.convert_to_pdf,
        name='convert_to_pdf',
    ),
]
