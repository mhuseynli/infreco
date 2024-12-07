from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers.event import EventSerializer
from core.services.rabbitmq import send_event_to_queue
from core.database import db


class EventView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Create a new event.
        """
        webshop_id = request.webshop.get("id")  # Webshop ID from middleware
        if not webshop_id:
            return Response({"detail": "Missing X-API-KEY header."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = EventSerializer(data=request.data, context={"webshop_id": webshop_id})
        serializer.is_valid(raise_exception=True)

        # Prepare data for RabbitMQ
        rabbitmq_event_data = self.prepare_rabbitmq_data(serializer.validated_data, webshop_id)
        try:
            send_event_to_queue(rabbitmq_event_data)
        except Exception as e:
            return Response({"detail": f"Failed to queue event: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Event queued successfully."}, status=status.HTTP_202_ACCEPTED)

    def get(self, request, user_id=None, *args, **kwargs):
        """
        Fetch events for a webshop with optional filtering by user external_id.
        """
        webshop_id = request.webshop.get("id")  # Webshop ID from middleware

        if not webshop_id:
            return Response({"detail": "Missing X-API-KEY header."}, status=status.HTTP_400_BAD_REQUEST)

        # Build query to fetch events
        query = {"webshop_id": webshop_id}

        # If a user_id is provided, resolve the user's ObjectId
        if user_id:
            user = db.users.find_one({"external_id": user_id, "webshop_id": webshop_id})
            if not user:
                return Response({"detail": f"User with external_id '{user_id}' not found."},
                                status=status.HTTP_404_NOT_FOUND)
            query["user_id"] = user["_id"]

        # Fetch events based on the query
        events = list(db.events.find(query))

        # Enrich events with data from referenced collections
        enriched_events = []
        for event in events:
            # Resolve referenced collections
            user = db.users.find_one({"_id": event["user_id"]})
            product = db.items.find_one({"_id": event["product_id"]})
            event_type = db.event_types.find_one({"_id": event["event_id"]})

            # Construct enriched event
            enriched_event = {
                "user": {
                    key: value for key, value in user.items() if key != "_id"
                } if user else None,
                "product": {
                    key: value for key, value in product.items() if key != "_id"
                } if product else None,
                "event_type": {
                    key: value for key, value in event_type.items() if key != "_id"
                } if event_type else None,
                "timestamp": event["timestamp"],
            }

            enriched_events.append(enriched_event)

        return Response({"events": enriched_events}, status=status.HTTP_200_OK)

    def prepare_rabbitmq_data(self, validated_data, webshop_id):
        """
        Prepare the event data for RabbitMQ.
        """
        return {
            "webshop_id": webshop_id,
            "user_id": str(validated_data["user_id"]),  # Resolved user ID
            "product_id": str(validated_data["product_id"]),  # Resolved product ID
            "event_id": str(validated_data["event_id"]),  # Resolved event type ID
            "timestamp": validated_data["timestamp"].isoformat(),
        }


class EventListView(APIView):
    def get(self, request, user_id=None, *args, **kwargs):
        """
        Fetch events for a webshop with optional filtering by user external_id.
        """
        webshop_id = request.webshop.get("id")  # Webshop ID from middleware

        if not webshop_id:
            return Response({"detail": "Missing X-API-KEY header."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the user ID if `user_id` is provided
        user_object_id = None
        if user_id:
            user = db.users.find_one({"external_id": user_id, "webshop_id": webshop_id})
            if not user:
                return Response({"detail": f"User with external_id '{user_id}' not found."},
                                status=status.HTTP_404_NOT_FOUND)
            user_object_id = user["_id"]

        # Build query to fetch events
        query = {"webshop_id": webshop_id}
        if user_object_id:
            query["user_id"] = user_object_id

        events = list(db.events.find(query))

        # Enrich events with data from referenced collections
        enriched_events = []
        for event in events:
            # Resolve referenced collections
            user = db.users.find_one({"_id": event["user_id"]})
            product = db.items.find_one({"_id": event["product_id"]})
            event_type = db.event_types.find_one({"_id": event["event_id"]})

            enriched_event = {
                "product": {
                    key: value for key, value in product.items() if key != "_id"
                } if product else None,
                "event_type": {
                    key: value for key, value in event_type.items() if key != "_id"
                } if event_type else None,
                "timestamp": event["timestamp"],
            }

            enriched_events.append(enriched_event)

        return Response({"events": enriched_events}, status=status.HTTP_200_OK)
