from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, permissions, serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserSerializer

TokenResponse = inline_serializer('TokenResponse', fields={
    'token': serializers.CharField(),
    'user': UserSerializer(),
})


@extend_schema(tags=['Auth'], responses={201: TokenResponse})
class RegisterView(generics.CreateAPIView):
    """Create a customer account and get an auth token back."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Auth'], responses={200: TokenResponse})
class LoginView(ObtainAuthToken):
    """Log in with username and password. Send the token as `Authorization: Token <token>`."""

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})


@extend_schema(tags=['Auth'], request=None, responses={204: None})
class LogoutView(APIView):
    """Delete the current token so it can't be used again."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Auth'])
class MeView(generics.RetrieveUpdateAPIView):
    """View or update the logged-in user's profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
