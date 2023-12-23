from django.urls import path
from notices import views

urlpatterns = [
    path('insert_notice/', views.insert_notice, name='insert_notice'),
]
