from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Category)
admin.site.register(models.Item)
admin.site.register(models.ItemsInCart)
admin.site.register(models.Purchase)
admin.site.register(models.PurchaseDetail)