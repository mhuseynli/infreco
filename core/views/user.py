from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from core.database import db
from core.serializers.user import UserSerializer


class UserCreateView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        webshop_id = request.webshop.get("id")
        if not webshop_id:
            return Response({"detail": "Missing webshop ID in headers."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, context={"webshop_id": webshop_id})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(user, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        webshop_id = self.request.webshop.get("id")
        external_id = self.kwargs.get("user_id")  # Use user_id as external_id
        if not webshop_id:
            raise ValidationError({"detail": "Missing webshop ID in headers."})

        user = db.users.find_one({"external_id": external_id, "webshop_id": webshop_id})
        if not user:
            raise NotFound({"detail": f"User with external_id '{external_id}' not found."})
        return user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        webshop_id = self.request.webshop.get("id")
        user = self.get_object()

        serializer = self.get_serializer(
            user, data=request.data, partial=True, context={"webshop_id": webshop_id}
        )
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        return Response(updated_user)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        result = db.users.delete_one({"external_id": user["external_id"], "webshop_id": self.request.webshop["id"]})
        if result.deleted_count == 0:
            raise NotFound({"detail": f"User with external_id '{user['external_id']}' not found."})
        return Response({"detail": "User deleted successfully."}, status=status.HTTP_200_OK)
