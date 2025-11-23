from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from account.models import *
from django.contrib.auth import authenticate
from account.models import Profile
from django.utils import timezone
from rest_framework import status, serializers
from rest_framework.response import Response
from django.contrib.auth import authenticate

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        request = self.context['request']

        credentials = {
            'username': attrs.get('username'),
            'password': attrs.get('password')
        }

        user = authenticate(**credentials)

        if user is None or not user.is_active:
            raise serializers.ValidationError({'detail': 'Invalid username or password'}, code='authorization')

        self.user = user
        data = super().validate(attrs)

        # Add custom user & device info
        profile = Profile.objects.get(user=user)
        data['user'] = {
            'id': user.id,
            'email': user.username,
            'name': user.get_full_name(),
            'is_email_verified': profile.is_email_verified if hasattr(profile, 'is_email_verified') else False,
            'profile_image': request.build_absolute_uri(profile.profile_image.url) if profile.profile_image else None,
            'bio': profile.bio,
            'is_superuser': user.is_superuser,
        }

        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Get refresh token from the request data
        refresh_token = attrs['refresh']
        
        # Use RefreshToken class to extract the payload from the token
        token = RefreshToken(refresh_token)
        
        # Extract the user ID from the token payload
        user_id = token['user_id']
    
        # Retrieve the user from the database
        try:
            user = User.objects.get(id=user_id)
            profile = Profile.objects.get(user=user)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Profile not found")
        
        
        # Add custom response data (user info)
        data['user_info'] = {
            'id': user.id,
            'email': user.username,
            'name': user.get_full_name(),
            'is_email_verified': profile.is_email_verified if hasattr(profile, 'is_email_verified') else False,
            'bio': profile.bio,
            'profile_image': self.context['request'].build_absolute_uri(profile.profile_image.url) if profile.profile_image else None,
            'is_superuser': user.is_superuser,
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer