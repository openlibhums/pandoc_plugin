from django.conf.urls import url

from plugins.pandoc import views

urlpatterns = [
    url(r'^$', views.index, name='pandoc_index'),
    url(r'^convert/(?P<article_id>\d+)/file/(?P<file_id>\d+)/$', views.convert_file, name='pandoc_convert'),
]
