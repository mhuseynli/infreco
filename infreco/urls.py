from django.contrib import admin
from django.urls import path

from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webshops/register/', views.RegisterWebshopView.as_view(), name='register-webshop'),
    path('webshops/', views.WebshopView.as_view(), name='webshop'),
    path('events/', views.EventView.as_view(), name='event'),

    # Recommender endpoints
    path('recommender/train/', views.TrainRecommenderView.as_view(), name='train-recommender'),
    path('recommender/recommend/<str:user_id>/', views.RecommendationView.as_view(), name='recommendations'),
]
