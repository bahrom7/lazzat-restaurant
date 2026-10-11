from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/',                              admin.site.urls),
    path('',                                    views.home_view,           name='home'),
    path('menu/',                               views.menu_view,           name='menu'),
    path('about/',                              views.about_view,          name='about'),
    path('contact/',                            views.contact_view,        name='contact'),
    path('order/<int:order_id>/',               views.order_success_view,  name='order-success'),
    path('tracking/<int:order_id>/',            views.order_tracking_view, name='order-tracking'),
    # Auth
    path('login/',                              views.login_view,          name='login'),
    path('register/',                           views.register_view,       name='register'),
    path('logout/',                             views.logout_view,         name='logout'),
    path('auth/send-otp/',                      views.send_otp_view,       name='send-otp'),
    path('auth/verify-otp/',                    views.verify_otp_view,     name='verify-otp'),
    path('auth/register/',                      views.api_register,        name='api-register'),
    path('auth/login/',                         views.api_login_password,  name='api-login'),
    # API
    path('api/',                                include('core.urls')),
    path('health/',                             views.health_check,        name='health'),
    path('game/',                               views.rps_game_view,       name='rps-game'),
    path('api/rps/join/',                       views.rps_join,            name='rps-join'),
    path('api/rps/check/',                      views.rps_check,           name='rps-check'),
    path('api/rps/choice/',                     views.rps_choice,          name='rps-choice'),
    path('api/rps/state/',                      views.rps_state,           name='rps-state'),
    path('api/rps/send-otp/',                   views.rps_send_otp,        name='rps-send-otp'),
    path('api/rps/verify-otp/',                 views.rps_verify_otp,      name='rps-verify-otp'),
    path('api/rps/register/',                   views.rps_register,        name='rps-register'),
    path('api/rps/login/',                      views.rps_login,           name='rps-login'),
    path('api/rps/logout/',                     views.rps_logout,          name='rps-logout'),
    path('api/rps/heartbeat/',                  views.rps_heartbeat,       name='rps-heartbeat'),
    path('api/rps/stats/',                      views.rps_update_stats,    name='rps-stats'),
    path('api/rps/rating/',                     views.rps_rating,          name='rps-rating'),
    path('api/rps/chat/send/',                  views.rps_chat_send,       name='rps-chat-send'),
    path('api/rps/chat/get/',                   views.rps_chat_get,        name='rps-chat-get'),
]
