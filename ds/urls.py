"""ds URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),

    path('pgn', views.cell1, name='cell1'),
    path('miluogo', views.cell2, name='cell2'),
    path('reviewlizer', views.cell3, name='cell3'),

    path('fakeNews', views.cell4, name='cell4'),
    path('sales', views.cell5, name='cell5'),
    path('moviePosters', views.cell6, name='cell6'),

    path('instaSeer', views.cell7, name='cell7'),
    path('airfoils', views.cell8, name='cell8'),
    path('about', views.cell9, name='cell9'),
    path('aboutit', views.aboutit, name='aboutit')


]
