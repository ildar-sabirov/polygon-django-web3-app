from django.urls import path
from .views import get_balance_view

urlpatterns = [
    path('get_balance/', get_balance_view, name='get_balance'),
]
