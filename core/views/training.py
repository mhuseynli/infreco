from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.trainers.collaborative import CollaborativeTrainer
from core.trainers.content_based import ContentBasedTrainer


class TrainCollaborativeView(APIView):
    def post(self, request, *args, **kwargs):
        """Endpoint to trigger collaborative filtering training."""
        webshop_id = request.headers.get("X-API-KEY")
        if not webshop_id:
            return Response({"detail": "Missing webshop ID."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            trainer = CollaborativeTrainer(webshop_id)
            trainer.train()
            return Response({"message": "Collaborative training completed."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Error during training: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrainContentBasedView(APIView):
    def post(self, request, *args, **kwargs):
        webshop_id = request.headers.get("X-API-KEY")
        if not webshop_id:
            return Response({"detail": "Missing webshop ID."}, status=status.HTTP_400_BAD_REQUEST)

        trainer = ContentBasedTrainer(webshop_id)
        trainer.train()
        return Response({"message": "Content-based training completed."}, status=status.HTTP_200_OK)
