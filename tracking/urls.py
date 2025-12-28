from django.urls import path
from .api import TrackEventView, AliasUserView

urlpatterns = [
    path("track/", TrackEventView.as_view(), name="track-event"),
    path("alias/", AliasUserView.as_view(), name="alias-user"),
]
