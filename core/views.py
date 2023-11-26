import logging
from datetime import datetime

from rest_framework import generics, status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .database import db
from core.services.rabbitmq import send_event_to_queue
from .recommender_interface import RecommenderInterface

from .serializers import WebshopSerializer, EventSerializer
import traceback

logger = logging.getLogger(__name__)


# Example class of a specific recommender algorithm
class MyRecommender(RecommenderInterface):
    def train(self, data, parameters):
        # Implement training logic
        pass

    def recommend(self, user_id, num_recommendations=10):
        # Implement recommendation logic
        pass

    def update_model(self, model_path):
        # Implement model update logic
        pass


class TrainRecommenderView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        webshop_id = request.headers.get('X-API-KEY')
        if not webshop_id:
            return Response({"detail": "Missing X-API-KEY header"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch data related to the webshop for training
        events = db.events.find({"webshop_id": webshop_id})
        users = db.users.find({"webshop_id": webshop_id})
        items = db.items.find({"webshop_id": webshop_id})

        # Convert the data to a suitable format for training
        # This might involve transforming it into a pandas DataFrame, a list of dictionaries, etc.
        # The format will depend on our recommender system expects to receive the data
        data = {
            "events": list(events),
            "users": list(users),
            "items": list(items)
        }

        parameters = request.data.get('parameters', {})

        recommender = MyRecommender()
        recommender.train(data, parameters)

        return Response({"message": "Training initiated"}, status=status.HTTP_202_ACCEPTED)


class RecommendationView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        webshop_id = request.headers.get('X-API-KEY')
        if not webshop_id:
            return Response({"detail": "Missing X-API-KEY header"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = kwargs.get('user_id')
        recommender = MyRecommender()
        recommendations = recommender.recommend(user_id, num_recommendations=10)

        return Response({"recommendations": recommendations}, status=status.HTTP_200_OK)


class RegisterWebshopView(generics.CreateAPIView):
    serializer_class = WebshopSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)  # This will raise an exception for validation errors
            webshop = serializer.save()
            return Response({
                "email": webshop['email'],
                "webshop_name": webshop['webshop_name'],
                "message": "Webshop registered successfully!"
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            traceback.print_exc()
            # Capture any other exceptions and print the message
            return Response({"detail": "Unhandled error occurred. Please contact the system administrator."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WebshopView(generics.GenericAPIView):
    serializer_class = WebshopSerializer

    def get(self, request, *args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return Response({"detail": "API key required."}, status=status.HTTP_401_UNAUTHORIZED)

        webshop = db.webshops.find_one({"id": api_key})
        if not webshop:
            return Response({"detail": "Webshop not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(webshop)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return Response({"detail": "API key required."}, status=status.HTTP_401_UNAUTHORIZED)

        webshop = db.webshops.find_one({"id": api_key})
        if not webshop:
            return Response({"detail": "Webshop not found."}, status=status.HTTP_404_NOT_FOUND)

        update_data = request.data
        db.webshops.update_one({"id": api_key}, {"$set": update_data})

        updated_webshop = db.webshops.find_one({"id": api_key})
        serializer = self.get_serializer(updated_webshop)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return Response({"detail": "API key required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Delete the webshop
        delete_result = db.webshops.delete_one({"id": api_key})
        if delete_result.deleted_count == 0:
            return Response({"detail": "Webshop not found or already deleted."}, status=status.HTTP_404_NOT_FOUND)

        # Delete related users, items, and events
        db.users.delete_many({"webshop_id": api_key})
        db.items.delete_many({"webshop_id": api_key})
        db.events.delete_many({"webshop_id": api_key})

        return Response({"detail": "Webshop and all related data deleted successfully."}, status=status.HTTP_200_OK)


class EventView(generics.CreateAPIView):
    serializer_class = EventSerializer

    def create(self, request, *args, **kwargs):
        webshop_id = request.headers.get('X-API-KEY')
        if not webshop_id:
            return Response({"detail": "Missing X-API-KEY header"}, status=status.HTTP_400_BAD_REQUEST)

        webshop = db.webshops.find_one({"id": webshop_id})
        if not webshop:
            return Response({"detail": "Webshop not found."}, status=status.HTTP_404_NOT_FOUND)

        event_serializer = self.get_serializer(data=request.data)
        if event_serializer.is_valid(raise_exception=True):
            event_data = event_serializer.validated_data
            rabbitmq_event_data = self.prepare_rabbitmq_data(webshop_id, event_data)
            try:
                send_event_to_queue(rabbitmq_event_data)
            except Exception as e:
                logger.error(f"Failed to send event to RabbitMQ: {e}", exc_info=True)
                return Response({"detail": f"Failed to queue event: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Event queued successfully"}, status=status.HTTP_202_ACCEPTED)

        return Response(event_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def prepare_rabbitmq_data(self, webshop_id, event_data):
        event_data_copy = event_data.copy()
        if isinstance(event_data_copy.get('timestamp'), datetime):
            event_data_copy['timestamp'] = event_data_copy['timestamp'].isoformat()

        return {
            'webshop_id': webshop_id,
            'user': event_data_copy.get('user', {}),
            'item': event_data_copy.get('item', {}),
            'event_type': event_data_copy.get('event_type'),
            'timestamp': event_data_copy.get('timestamp')
        }
