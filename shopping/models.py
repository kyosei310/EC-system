from django.db import models
from account.models import AccountUser


class Category(models.Model):
    class Meta:
        db_table = 'shopping_category'

    def __str__(self):
        return self.name
    
    category_id = models.IntegerField(primary_key=True, db_index=True)
    name = models.CharField(max_length=256)

    


class Item(models.Model):
    class Meta:
        db_table = 'shopping_item'

    def __str__(self):
        return self.name


    @property
    def stock_range(self):
        """カートの数量プルダウン用"""
        return range(1, min(self.stock, 99) + 1)


    item_id = models.IntegerField(
        primary_key=True,
        db_index=True,
    )
    name = models.CharField(max_length=128)
    manufacturer = models.CharField(max_length=32)
    color = models.CharField(max_length=16)
    price = models.IntegerField()
    stock = models.IntegerField()
    recommended = models.BooleanField(default=False)  # 0=通常, 1=おすすめ
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        db_column='category_id',
    )



class ItemsInCart(models.Model):
    class Meta:
        db_table = 'shopping_itemsincart'

    id = models.AutoField(primary_key=True)
    amount = models.IntegerField()
    booked_date = models.DateTimeField(auto_now_add=True)
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        db_column='item_id',
    )
    user = models.ForeignKey(
        AccountUser,
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='user_id',
    )


class Purchase(models.Model):
    class Meta:
        db_table = 'shopping_purchase'
        
    purchase_id = models.IntegerField(
        primary_key=True,
        db_index=True,
    )
    destination = models.CharField(max_length=256)
    booked_date = models.DateTimeField(auto_now_add=True)
    cancel = models.BooleanField(default=False)
    user = models.ForeignKey(
        AccountUser,
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='user_id',
    )



class PurchaseDetail(models.Model):
    class Meta:
        db_table = 'shopping_purchasedetail'
    
    purchase_detail_id = models.IntegerField(
        primary_key=True,
        db_index=True,
    )
    amount = models.IntegerField()
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        db_column='item_id',
    )
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        db_column='purchase_id',
    )

