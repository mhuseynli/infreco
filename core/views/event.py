from rest_framework import generics, status
from rest_framework.response import Response
from core.serializers.event import EventSerializer
from core.services.rabbitmq import send_event_to_queue


class EventView(generics.CreateAPIView):
    serializer_class = EventSerializer

    def create(self, request, *args, **kwargs):
        webshop_id = request.webshop.get("id")  # Use webshop ID from middleware
        if not webshop_id:
            return Response({"detail": "Missing X-API-KEY header."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, context={"webshop_id": webshop_id})
        serializer.is_valid(raise_exception=True)

        # Prepare data for RabbitMQ
        rabbitmq_event_data = self.prepare_rabbitmq_data(serializer.validated_data, webshop_id)
        try:
            send_event_to_queue(rabbitmq_event_data)
        except Exception as e:
            return Response({"detail": f"Failed to queue event: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Event queued successfully."}, status=status.HTTP_202_ACCEPTED)

    def prepare_rabbitmq_data(self, validated_data, webshop_id):
        """Prepare the event data for RabbitMQ."""
        return {
            "webshop_id": webshop_id,
            "user_id": str(validated_data["user_id"]),  # Resolved user ID
            "product_id": str(validated_data["product_id"]),  # Resolved product ID
            "event_id": str(validated_data["event_id"]),  # Resolved event type ID
            "timestamp": validated_data["timestamp"].isoformat(),
        }