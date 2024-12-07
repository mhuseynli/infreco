from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.recommenders.collaborative import CollaborativeRecommender
from core.recommenders.content_based import ContentBasedRecommender
from core.data_processing import fetch_webshop_data
from core.database import db


class BaseRecommendationView(APIView):
    """
    Base class for recommendation views to ensure consistent patterns and access to webshop_id.
    """

    def get_webshop(self, request):
        """
        Retrieve the webshop object from the request.
        Raises a 401 error if not found.
        """
        webshop = getattr(request, "webshop", None)
        if not webshop:
            raise ValueError("Webshop ID is missing in the request. Ensure middleware is properly configured.")
        return webshop

    def get_user_by_external_id(self, webshop_id, user_external_id):
        """
        Find a user by external_id and webshop_id.
        :param webshop_id: The ID of the webshop
        :param user_external_id: The external ID of the user
        :return: User document or raises a 404 Response
        """
        try:
            user = db.users.find_one({"external_id": user_external_id, "webshop_id": webshop_id})
            if not user:
                raise ValueError(f"User with external ID '{user_external_id}' not found.")
            return user
        except ValueError as e:
            raise Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class RecommendCollaborativeView(BaseRecommendationView):
    """
    View for collaborative filtering recommendations.
    """

    def get(self, request, *args, **kwargs):
        user_external_id = kwargs.get("user_id")

        if not user_external_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            webshop = self.get_webshop(request)
            user = self.get_user_by_external_id(webshop["id"], user_external_id)
            user_id = str(user["_id"])

            # Load collaborative recommender
            recommender = CollaborativeRecommender(webshop["id"])
            recommender.load()

            # Generate recommendations
            recommendations = recommender.recommend(user_id)
            return Response({"recommendations": recommendations}, status=status.HTTP_200_OK)

        except Response as response:
            return response
        except Exception as e:
            return Response({"detail": f"Error generating recommendations: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendContentBasedView(BaseRecommendationView):
    """
    View for content-based filtering recommendations.
    """

    def get(self, request, *args, **kwargs):
        user_external_id = kwargs.get("user_id")

        if not user_external_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            webshop = self.get_webshop(request)
            users, items, events, _ = fetch_webshop_data(webshop["id"])

            # Resolve user by external ID
            user = self.get_user_by_external_id(webshop["id"], user_external_id)
            user_id = str(user["_id"])

            # Load content-based recommender
            recommender = ContentBasedRecommender(webshop["id"])
            recommender.load()

            # Generate recommendations
            recommendations = recommender.recommend(user_id, events, items)

            # Enrich recommendations with product details
            enriched_recommendations = [
                {
                    "score": rec["score"],
                    "item": {key: value for key, value in next(
                        (item for item in items if str(item["_id"]) == rec["item_id"]), {}).items() if key != "_id"}
                }
                for rec in recommendations if next((item for item in items if str(item["_id"]) == rec["item_id"]), None)
            ]

            return Response({"recommendations": enriched_recommendations}, status=status.HTTP_200_OK)

        except Response as response:
            return response
        except Exception as e:
            return Response({"detail": f"Error generating recommendations: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
