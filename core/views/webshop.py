import logging

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from core.database import db
from bson import ObjectId
from core.serializers.webshop import WebshopSerializer

logger = logging.getLogger("core")


class RegisterWebshopView(generics.CreateAPIView):
    serializer_class = WebshopSerializer

    def create(self, request, *args, **kwargs):
        try:
            # Validate and save the webshop data
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            webshop = serializer.save()

            # Fetch allowed attributes for the chosen type
            type_data = db.attributes.find_one({"_id": webshop["type_id"]})
            allowed_attributes = type_data["attributes"] if type_data else []

            return Response(
                {
                    "email": webshop["email"],
                    "webshop_name": webshop["webshop_name"],
                    "type": type_data["type"] if type_data else "Unknown",
                    "allowed_attributes": allowed_attributes,
                    "message": "Webshop registered successfully!",
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            logger.warning(f"Validation error details: {e.detail}")
            return Response({"errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WebshopView(generics.GenericAPIView):
    serializer_class = WebshopSerializer

    def get(self, request, *args, **kwargs):
        """Fetch webshop details by API key."""
        api_key = request.headers.get("X-API-KEY")
        logger.info(f"API Key received: {api_key}")

        if not api_key:
            return Response({"detail": "API key required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Fetch the webshop from the database
        webshop = db.webshops.find_one({"id": api_key})
        if not webshop:
            return Response({"detail": "Webshop not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the type information and allowed attributes
        type_data = db.attributes.find_one({"_id": ObjectId(webshop["type_id"])})
        webshop["allowed_attributes"] = type_data.get("attributes", []) if type_data else []
        webshop["type"] = type_data.get("type", "Unknown") if type_data else "Unknown"

        # Serialize the data
        serialized_data = {
            "email": webshop.get("email"),
            "webshop_name": webshop.get("webshop_name"),
            "is_verified": webshop.get("is_verified", False),
            "recommendation_engine": webshop.get("recommendation_engine", ""),
            "engine_parameters": webshop.get("engine_parameters", {}),
            "api_endpoint": webshop.get("api_endpoint", ""),
            "type": webshop["type"],
            "allowed_attributes": webshop["allowed_attributes"],
        }
        return Response(serialized_data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """Update webshop details."""
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return Response({"detail": "API key required."}, status=status.HTTP_401_UNAUTHORIZED)

        webshop = db.webshops.find_one({"id": api_key})
        if not webshop:
            return Response({"detail": "Webshop not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate and apply updates
        update_data = request.data
        db.webshops.update_one({"id": api_key}, {"$set": update_data})

        # Fetch the updated webshop and attributes
        updated_webshop = db.webshops.find_one({"id": api_key})
        type_data = db.attributes.find_one({"_id": ObjectId(updated_webshop["type_id"])})
        updated_webshop["allowed_attributes"] = type_data["attributes"] if type_data else []
        updated_webshop["type"] = type_data["type"] if type_data else "Unknown"

        serializer = self.get_serializer(updated_webshop)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Delete a webshop and its related data."""
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return Response({"detail": "API key required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Delete the webshop
        delete_result = db.webshops.delete_one({"id": api_key})
        if delete_result.deleted_count == 0:
            return Response({"detail": "Webshop not found or already deleted."}, status=status.HTTP_404_NOT_FOUND)

        # Clean up related data
        db.users.delete_many({"webshop_id": api_key})
        db.items.delete_many({"webshop_id": api_key})
        db.events.delete_many({"webshop_id": api_key})

        return Response({"detail": "Webshop and all related data deleted successfully."}, status=status.HTTP_200_OK)
