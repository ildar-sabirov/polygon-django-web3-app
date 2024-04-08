from django.urls import path
from .views import (
    get_balance_view,
    get_balance_batch_view,
    get_top_view,
    get_top_with_transactions_view,
    get_token_info_view,
)

urlpatterns = [
    path('get_balance/', get_balance_view, name='get_balance'),
    path(
        'get_balance_batch/', get_balance_batch_view, name='get_balance_batch'
    ),
    path('get_top/', get_top_view, name='get_top'),
    path(
        'get_top_with_transactions/',
        get_top_with_transactions_view,
        name='get_top_with_transactions'
    ),
    path('get_token_info/', get_token_info_view, name='get_token_info'),
]
