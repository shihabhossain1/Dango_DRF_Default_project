from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered # type: ignore[attr-defined]
from django.apps import apps

# Register your models here.
app_models = apps.get_app_config('account').get_models()
for model in app_models:
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass