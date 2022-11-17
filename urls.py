from django.urls import re_path

from plugins.pandoc_plugin import views

urlpatterns = [
    re_path(r'^$', views.index, name='pandoc_index'),
    re_path(r'^convert/(?P<article_id>\d+)/file/(?P<file_id>\d+)/$', views.convert_file, name='pandoc_convert'),
]
