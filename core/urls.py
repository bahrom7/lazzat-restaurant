from django.urls import path
from . import views

urlpatterns = [
    path('menu/',                   views.api_menu,            name='api-menu'),
    path('status/',                 views.api_restaurant_status, name='api-status'),
    path('promo/',                  views.api_check_promo,     name='api-promo'),
    path('order/',                  views.api_create_order,    name='api-create-order'),
    path('order/<int:order_id>/',   views.api_order_status,    name='api-order-status'),
    path('rate/<int:item_id>/',     views.api_rate_item,       name='api-rate'),
]
