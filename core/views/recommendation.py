from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.recommenders.collaborative import CollaborativeRecommender
from core.recommenders.content_based import ContentBasedRecommender
from core.recommenders.surprise import SurpriseRecommender
from core.data_processing import fetch_webshop_data

class RecommendCollaborativeView(APIView):
    def get(self, request, *args, **kwargs):
        webshop_id = request.headers.get("X-API-KEY")
        user_attributes = request.query_params.dict()

        recommender = CollaborativeRecommender(webshop_id)
        recommender.load()
        recommendations = recommender.recommend(user_attributes)
        return Response({"recommendations": recommendations}, status=status.HTTP_200_OK)


class RecommendContentBasedView(APIView):
    def get(self, request, *args, **kwargs):
        webshop_id = request.headers.get("X-API-KEY")
        user_id = kwargs.get("user_id")

        if not webshop_id or not user_id:
            return Response({"detail": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        _, _, events = fetch_webshop_data(webshop_id)

        recommender = ContentBasedRecommender(webshop_id)
        recommender.load()
        recommendations = recommender.recommend(user_id, events)
        return Response({"recommendations": recommendations}, status=status.HTTP_200_OK)


class RecommendSurpriseView(APIView):
    def get(self, request, *args, **kwargs):
        webshop_id = request.headers.get("X-API-KEY")
        user_id = kwargs.get("user_id")

        if not webshop_id or not user_id:
            return Response({"detail": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        _, items, events = fetch_webshop_data(webshop_id)

        recommender = SurpriseRecommender(webshop_id)
        recommender.load()
        recommendations = recommender.recommend(user_id, events, items)
        return Response({"recommendations": recommendations}, status=status.HTTP_200_OK)