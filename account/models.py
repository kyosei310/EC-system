from django.db import models

# Create your models here.

class AccountUser(models.Model):
    class Meta:
        db_table = 'account_user'
        ordering = ["-user_id"]
        # vervose_name = "ユーザ"
        # vervose_name_plural = "ユーザ"
        
    user_id = models.CharField(primary_key=True, max_length=128, unique=True)
    password = models.CharField(max_length=256)
    name = models.CharField(max_length=128)
    address = models.CharField(max_length=256)
    
    def __str__(self):
        return self.user_id


class Admin(models.Model):
    # varchar, 128桁, PK, INDEX, 自動採番なし
    admin_id = models.CharField(max_length=128, primary_key=True, db_index=True)
    password = models.CharField(max_length=256)
 
    class Meta:
        db_table = 'administrator_admin'
