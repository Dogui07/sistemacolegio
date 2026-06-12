from django.urls import path
from . import views

urlpatterns = [
    path('<slug:colegio_slug>/', views.index, name='home_colegio'),
]
