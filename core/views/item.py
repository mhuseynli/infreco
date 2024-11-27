from rest_framework import generics, status
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response
from core.database import db
from core.serializers.item import ItemSerializer

class ItemCreateView(generics.CreateAPIView):
    serializer_class = ItemSerializer

    def create(self, request, *args, **kwargs):
        webshop = request.webshop  # Access webshop from middleware
        serializer = self.get_serializer(
            data=request.data,
            context={"webshop_id": webshop["id"], "request": request}  # Pass request to context
        )
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(item, status=status.HTTP_201_CREATED)


class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemSerializer

    def get_object(self):
        """Fetch the item using external_id and webshop_id."""
        webshop = self.request.webshop  # Access webshop object from middleware
        external_id = self.kwargs.get("external_id")
        item = db.items.find_one({"external_id": external_id, "webshop_id": webshop["id"]})
        if not item:
            raise NotFound({"detail": f"Item with external_id '{external_id}' not found."})
        return item

    def retrieve(self, request, *args, **kwargs):
        """Retrieve an item."""
        item = self.get_object()
        serializer = self.get_serializer(item)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update an item using external_id."""
        webshop = self.request.webshop  # Access webshop object from middleware
        item = self.get_object()

        serializer = self.get_serializer(
            item, data=request.data, partial=True, context={"webshop_id": webshop["id"]}
        )
        serializer.is_valid(raise_exception=True)
        updated_item = serializer.save()
        return Response(updated_item)

    def delete(self, request, *args, **kwargs):
        """Delete an item using external_id."""
        item = self.get_object()
        result = db.items.delete_one({"external_id": item["external_id"], "webshop_id": self.request.webshop["id"]})
        if result.deleted_count == 0:
            raise NotFound({"detail": f"Item with external_id '{item['external_id']}' not found."})
        return Response({"detail": "Item deleted successfully."}, status=status.HTTP_200_OK)
