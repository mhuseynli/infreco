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
        user_external_id = kwargs.get("user_id")

        if not webshop_id or not user_external_id:
            return Response({"detail": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_external_id = int(user_external_id)  # Convert to integer if needed
            users, items, events, _ = fetch_webshop_data(webshop_id)

            # Resolve user by external ID
            user = next((u for u in users if u["external_id"] == user_external_id), None)
            if not user:
                return Response({"detail": f"User with external ID '{user_external_id}' not found."},
                                status=status.HTTP_404_NOT_FOUND)
            user_id = str(user["_id"])

            # Load the recommender
            recommender = ContentBasedRecommender(webshop_id)
            recommender.load()

            # Generate recommendations
            recommendations = recommender.recommend(user_id, events, items)
            return Response({"recommendations": recommendations}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"detail": f"Invalid user ID format: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error generating recommendations: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
