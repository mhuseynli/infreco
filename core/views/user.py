from rest_framework import generics, status
from rest_framework.response import Response
from core.database import db
from bson import ObjectId

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
        user_id = self.kwargs.get("user_id")
        if not webshop_id:
            return Response({"detail": "Missing webshop ID in headers."}, status=status.HTTP_400_BAD_REQUEST)

        user = db.users.find_one({"_id": ObjectId(user_id), "webshop_id": webshop_id})
        if not user:
            raise Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        webshop_id = self.request.webshop.get("id")
        user = self.get_object()

        serializer = self.get_serializer(user, data=request.data, partial=True, context={"webshop_id": webshop_id})
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        return Response(updated_user)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        db.users.delete_one({"_id": ObjectId(user["_id"])})
        return Response({"detail": "User deleted successfully."}, status=status.HTTP_200_OK)
