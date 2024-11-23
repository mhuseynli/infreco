from rest_framework import generics, status
from rest_framework.response import Response
from core.database import db
from core.serializers.event import EventSerializer
from core.services.rabbitmq import send_event_to_queue

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
                return Response({"detail": f"Failed to queue event: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Event queued successfully"}, status=status.HTTP_202_ACCEPTED)

        return Response(event_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def prepare_rabbitmq_data(self, webshop_id, event_data):
        event_data_copy = event_data.copy()
        event_data_copy['timestamp'] = event_data_copy.get('timestamp').isoformat()
        return {
            'webshop_id': webshop_id,
            'user': event_data_copy.get('user', {}),
            'item': event_data_copy.get('item', {}),
            'event_type': event_data_copy.get('event_type'),
            'timestamp': event_data_copy.get('timestamp')
        }