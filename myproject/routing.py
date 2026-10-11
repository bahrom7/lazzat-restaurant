from django.urls import re_path
from core.consumers import RPSConsumer

websocket_urlpatterns = [
    re_path(r'ws/rps/(?P<room_id>\w+)/$', RPSConsumer.as_asgi()),
]
