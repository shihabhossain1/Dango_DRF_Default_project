from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Country
from .serializers import *
from django.db import transaction
from django.db.models import Q
import os, json
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from travel_aggregator.error_log import log
from travel_aggregator.postman import send_email
from uuid import uuid4
from datetime import timedelta
from django.utils import timezone
from decouple import config
from .pagination import CustomPagination
# Create your views here.



class CountryListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    """
    List all countries or a specific country by id.
    """
    def get(self, request, pk=None):
        if pk:
            # Retrieve a single country by id
            try:
                country = Country.objects.get(pk=pk)
                serializer = CountrySerializer(country)
                return Response(serializer.data)
            except Country.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # List all countries
            countries = Country.objects.all()
            serializer = CountrySerializer(countries, many=True)
            return Response(serializer.data)


    def post(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "account", "data", "countries.json")

        if not os.path.exists(file_path):
            return Response(
                {"error": f"File not found: {file_path}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        # Extract "data" list
        data_list = []
        for item in content:
            if item.get("type") == "table" and "data" in item:
                data_list = item["data"]

        if not data_list:
            return Response(
                {"error": "No valid 'data' found in countries.json"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created, updated = 0, 0
        results = []

        with transaction.atomic():  # safer bulk insert/update
            for country_data in data_list:
                iso_code = country_data.get("iso_code")
                name = country_data.get("name")
                phoneCode = country_data.get("phoneCode")
                emojiU = country_data.get("emojiU")
                native = country_data.get("native")

                if not iso_code or not name:
                    continue

                obj, created_flag = Country.objects.update_or_create(
                    iso_code=iso_code,
                    defaults={
                        "name": name,
                        "phoneCode": phoneCode,
                        "emojiU": emojiU,
                        "native": native,
                    },
                )

                serializer = CountrySerializer(obj)
                results.append(serializer.data)

                if created_flag:
                    created += 1
                else:
                    updated += 1

        return Response(
            {
                "created": created,
                "updated": updated,
                "countries": results,
            },
            status=status.HTTP_200_OK,
        )

class CityListCreateAPIView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        queryset = City.objects.all().order_by('name')

        # Filtering
        country_id = request.GET.get('country')
        name = request.GET.get('search')
        is_active = request.GET.get('is_active')

        if country_id:
            queryset = queryset.filter(country_id=country_id)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if is_active is not None:
            if is_active.lower() in ['true', '1']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                queryset = queryset.filter(is_active=False)

        # Pagination
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = CitySerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    

    def post(self, request):
        serializer = CitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CityDetailAPIView(APIView):

    def get_object(self, pk):
        try:
            return City.objects.get(pk=pk)
        except City.DoesNotExist:
            return None

    def get(self, request, pk):
        city = self.get_object(pk)
        if not city:
            return Response({"error": "City not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CitySerializer(city)
        return Response(serializer.data)

    def patch(self, request, pk):
        city = self.get_object(pk)
        if not city:
            return Response({"error": "City not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CitySerializer(city, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        city = self.get_object(pk)
        if not city:
            return Response({"error": "City not found"}, status=status.HTTP_404_NOT_FOUND)
        city.delete()
        return Response({"message": "City deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(username=email)
                profile = user.profile
                token = uuid4()
                profile.verification_token = token
                profile.verification_token_expires = timezone.now()
                profile.save()

                reset_link = f"{config('FRONTEND_DOMAIN')}/change-password/?token={token}&email={email}"

                context = {
                    'user': user.get_full_name() or user.username,
                    'reset_link': reset_link,
                }

                send_email('Change Your Password', [email], 'emails/change_pass_email.html', context, [])

                return Response({"message": "Password reset link sent to email."}, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({"error": "No user with this email."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']

            try:
                # Find the profile with this token
                profile = Profile.objects.get(verification_token=token)

                # Check token expiry
                if profile.verification_token_expires and \
                   timezone.now() <= profile.verification_token_expires + timedelta(hours=1):
                    
                    user = profile.user
                    user.set_password(new_password)
                    user.save()

                    # Invalidate the token
                    profile.verification_token = None
                    profile.verification_token_expires = None
                    profile.save()

                    return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            except Profile.DoesNotExist:
                return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        # Initialize the serializer with the request data
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            # Validations passed, now update the password
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({"detail": "Password has been updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Get the profile of the authenticated user
        profile = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        # Get the profile of the authenticated user
        profile = get_object_or_404(Profile, user=request.user)

        # Serialize the data and update the profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)