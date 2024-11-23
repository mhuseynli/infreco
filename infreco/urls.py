from django.contrib import admin
from django.urls import path

from core.views.events import EventView
from core.views.item import ItemCreateView, ItemDetailView
from core.views.recommendation import RecommendCollaborativeView, RecommendContentBasedView, RecommendSurpriseView
from core.views.training import TrainCollaborativeView, TrainContentBasedView, TrainSurpriseView
from core.views.user import UserCreateView, UserDetailView
from core.views.webshop import RegisterWebshopView, WebshopView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webshops/register/', RegisterWebshopView.as_view(), name='register-webshop'),
    path('webshops/', WebshopView.as_view(), name='webshop'),
    path('events/', EventView.as_view(), name='event'),

    path('users/', UserCreateView.as_view(), name='user-create'),  # Create user
    path('users/<str:user_id>/', UserDetailView.as_view(), name='user-detail'),  # Retrieve, update, delete user

    path('items/', ItemCreateView.as_view(), name='item-create'),  # Create item
    path('items/<str:item_id>/', ItemDetailView.as_view(), name='item-detail'),  # Retrieve, update, delete item

    # Recommender endpoints
    path('recommender/train/collaborative/', TrainCollaborativeView.as_view(), name='train-collaborative'),
    path('recommender/train/content-based/', TrainContentBasedView.as_view(), name='train-content-based'),
    path('recommender/collaborative/', RecommendCollaborativeView.as_view(), name='recommend-collaborative'),
    path('recommender/content-based/<str:user_id>/', RecommendContentBasedView.as_view(),
         name='recommend-content-based'),
    path('recommender/train/surprise/', TrainSurpriseView.as_view(), name='train-surprise'),
    path('recommender/surprise/<str:user_id>/', RecommendSurpriseView.as_view(), name='recommend-surprise'),
]
