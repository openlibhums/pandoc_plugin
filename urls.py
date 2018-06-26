from django.conf.urls import url

from plugins.pandoc_plugin import views

urlpatterns = [
    url(r'^$', views.index, name='pandoc_index'),
]