from rest_framework import serializers
from .models import *


class ProfileSerializer(serializers.ModelSerializer):
    # Including fields from the related User model
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')

    class Meta:
        model = Profile
        fields = [
            'profile_image', 'age', 'bio', 'address', 'city', 'state', 
            'postal_code', 'gender', 'date_of_birth', 'phone', 'country', 
            'isoCode', 'username', 'first_name'
        ]

    def update(self, instance, validated_data):
        # Handling the update for the user-related fields
        user_data = validated_data.pop('user', {})
        
        # Update user data if present
        if 'username' in user_data:
            instance.user.username = user_data['username']
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        
        # Save the user instance first
        instance.user.save()
        
        # Update the profile fields with the rest of the data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the profile instance
        instance.save()
        return instance




class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirmPassword = serializers.CharField(write_only=True)
    name = serializers.CharField(write_only=True)
    phone = serializers.CharField()
    country = serializers.CharField()
    isoCode = serializers.CharField()
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirmPassword', 
                  'name', 'phone', 'country', 'isoCode', 'profile_image']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def validate(self, data):
        if data['password'] != data.pop('confirmPassword'):
            raise serializers.ValidationError({"confirmPassword": "Passwords do not match."})
        if len(data['password']) < 8:
            raise serializers.ValidationError({"password": "Password must be at least 8 characters long."})
        return data

    def create(self, validated_data):
        first_name = validated_data.pop('name', '')

        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=first_name
        )

        # Update the auto-created profile
        profile = user.profile
        profile.phone = validated_data.get('phone', profile.phone)
        profile.country = validated_data.get('country', profile.country)
        profile.isoCode = validated_data.get('isoCode', profile.isoCode)
        profile.profile_image = validated_data.get('profile_image', profile.profile_image)
        profile.save()

        return user



class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "phoneCode", "iso_code", "emojiU","native"]

class CitySerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), 
        source='country', 
        write_only=True
    )

    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "country",     # nested object for read
            "country_id",  # for creating/updating
            "is_active",
            "created_at",
            "updated_at",
        ]


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data



class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        # Check if the current password is correct for the authenticated user
        user = self.context['request'].user  # The authenticated user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        # Ensure new password and confirm password match
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New password and confirm password do not match.")
        
        # Check password strength (you can add more checks here if necessary)
        if len(data['new_password']) < 8:
            raise serializers.ValidationError("New password must be at least 8 characters long.")

        return data
