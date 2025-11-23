from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


# Create your models here.
class Profile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='profile/image/', null=True, blank=True)
    age = models.IntegerField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)

    # New Fields
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    phone = models.CharField(max_length=35, null=True, blank=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    isoCode = models.CharField(max_length=10, blank=True, null=True)

    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=455, blank=True, null=True)
    verification_token_expires = models.DateTimeField(blank=True, null=True)
    
    verify_otp =models.CharField(max_length=50, blank=True, null=True)
    otp_sent = models.DateTimeField(blank=True, null=True)
    reset_otp_send = models.DateTimeField(blank=True, null=True)
    reset_otp = models.CharField(max_length=6, null=True, blank=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    last_password_change = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        
# save the profile when the user is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()




###
class Country(models.Model):
    """
    Represents a country with basic information
    """
    name = models.CharField(max_length=100, blank=True, null=True, help_text=_('Full name of the country'))
    phoneCode = models.CharField(max_length=200, blank=True, null=True, help_text=_('International dialing code'))
    emojiU = models.CharField(max_length=500, blank=True, null=True, help_text=_('Unicode emoji flag representation'))
    native = models.CharField(max_length=100, blank=True, null=True, help_text=_('Native name of the country'))
    iso_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    
    is_active = models.BooleanField(default=True, help_text=_('Whether this country is active or not'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="countrys")
    name = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True, help_text=_('Whether this city is active or not'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("country", "name")

    def __str__(self):
        return f"{self.name}, {self.country.name}"