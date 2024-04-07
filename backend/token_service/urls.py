from django.urls import path
from .views import get_balance_view, get_balance_batch_view

urlpatterns = [
    path('get_balance/', get_balance_view, name='get_balance'),
    path(
        'get_balance_batch/', get_balance_batch_view, name='get_balance_batch'
    ),
]
