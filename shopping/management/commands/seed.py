# -*- coding: utf-8 -*-
"""
サンプルデータ投入コマンド

配置場所:
    <アプリ名>/management/commands/seed.py

実行方法:
    python manage.py seed            # データ投入(既存データはスキップ/更新)
    python manage.py seed --clear    # 全削除してから投入
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.apps import apps


class SeedDefinitionError(CommandError):
    """サンプルデータ投入に必要なモデル/属性の定義が不足している場合に送出する例外。

    CommandError を継承しているため、管理コマンド実行時には
    長い Python のトレースバックではなく、メッセージのみがクリーンに表示される。
    """
    pass


class Command(BaseCommand):
    help = "各テーブルにサンプルデータ(5件ずつ)を投入します"

    REQUIRED_TABLES = {
        "account_user": {
            "alias": "Account",
            "fields": ["user_id", "password", "name", "address"],
        },
        "shopping_category": {
            "alias": "Category",
            "fields": ["category_id", "name"],
        },
        "shopping_item": {
            "alias": "Item",
            "fields": ["item_id", "name", "manufacturer", "color", "price", "stock", "recommended", "category"],
        },
        "shopping_itemsincart": {
            "alias": "Itemincart",
            "fields": ["amount", "booked_date", "item", "user"],
        },
        "shopping_purchase": {
            "alias": "Purchase",
            "fields": ["purchase_id", "destination", "booked_date", "cancel", "user"],
        },
        "shopping_purchasedetail": {
            "alias": "Purchasedetail",
            "fields": ["purchase_detail_id", "amount", "item", "purchase"],
        },
        "administrator_admin": {
            "alias": "Admin",
            "fields": ["admin_id", "password"],
        },
    }

    def load_models(self):
        model_map = {
            model._meta.db_table: model
            for model in apps.get_models()
        }

        missing_tables = []
        missing_fields = []

        for table_name, info in self.REQUIRED_TABLES.items():
            model = model_map.get(table_name)

            if model is None:
                missing_tables.append(table_name)
                continue

            model_fields = {
                field.name
                for field in model._meta.get_fields()
            }

            for field_name in info["fields"]:
                if field_name not in model_fields:
                    missing_fields.append((table_name, field_name))

        if missing_tables or missing_fields:
            messages = []

            for table_name in missing_tables:
                messages.append(
                    f"テーブル名：{table_name} に対応するモデルが定義されていません。"
                )

            for table_name, field_name in missing_fields:
                messages.append(
                    f"テーブル名：{table_name} に属性名：{field_name} が定義されていません。"
                )

            raise SeedDefinitionError(
                "サンプルデータの投入に必要なモデル定義が不足しています。\n"
                + "\n".join(messages)
            )

        return {
            info["alias"]: model_map[table_name]
            for table_name, info in self.REQUIRED_TABLES.items()
        }

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="投入前に既存データをすべて削除する",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        models = self.load_models()

        Account = models["Account"]
        Category = models["Category"]
        Item = models["Item"]
        Itemincart = models["Itemincart"]
        Purchase = models["Purchase"]
        Purchasedetail = models["Purchasedetail"]
        Admin = models["Admin"]

        if options["clear"]:
            self.stdout.write("既存データを削除しています...")
            # 外部キー制約を考慮して子テーブルから削除
            Purchasedetail.objects.all().delete()
            Purchase.objects.all().delete()
            Itemincart.objects.all().delete()
            Item.objects.all().delete()
            Category.objects.all().delete()
            Account.objects.all().delete()
            Admin.objects.all().delete()

        # ====================================
        # 会員 (account_user)
        # ====================================
        accounts_data = [
            ("user001", "password001", "山田 太郎", "東京都新宿区西新宿1-1-1"),
            ("user002", "password002", "佐藤 花子", "大阪府大阪市北区梅田2-2-2"),
            ("user003", "password003", "鈴木 一郎", "愛知県名古屋市中区栄3-3-3"),
            ("user004", "password004", "田中 美咲", "福岡県福岡市博多区博多駅前4-4-4"),
            ("user005", "password005", "高橋 健太", "北海道札幌市中央区大通西5-5-5"),
        ]
        accounts = {}
        for user_id, password, name, address in accounts_data:
            obj, created = Account.objects.update_or_create(
                user_id=user_id,
                defaults={
                    "password": password,
                    "name": name,
                    "address": address,
                },
            )
            accounts[user_id] = obj
        self.stdout.write(self.style.SUCCESS(f"会員: {len(accounts)}件"))

        # ====================================
        # カテゴリ (shopping_category)
        # ====================================
        categories_data = [
            (1, "鞄"),
            (2, "帽子"),
        ]
        categories = {}
        for category_id, name in categories_data:
            obj, created = Category.objects.update_or_create(
                category_id=category_id,
                defaults={"name": name},
            )
            categories[category_id] = obj
        self.stdout.write(self.style.SUCCESS(f"カテゴリ: {len(categories)}件"))

        # ====================================
        # 商品 (shopping_item)
        # ====================================
        items_data = [
            # (item_id, name, manufacturer, color, price, stock, recommended, category_id)
            (101, "レザーハンドバッグ エレガント", "サンプルレザー工房", "ブラウン", 12800, 15, True, 1),
            (102, "キャンバストートバッグ L", "ダミーバッグ社", "ベージュ", 3980, 50, False, 1),
            (103, "撥水リュック 25L", "テストアウトドア", "ブラック", 6480, 30, True, 1),
            (104, "コットンキャップ ロゴ刺繍", "帽子サンプル堂", "ネイビー", 2480, 60, False, 2),
            (105, "つば広ストローハット", "帽子サンプル堂", "ナチュラル", 3280, 40, True, 2),
        ]
        items = {}
        for item_id, name, manufacturer, color, price, stock, recommended, cat_id in items_data:
            obj, created = Item.objects.update_or_create(
                item_id=item_id,
                defaults={
                    "name": name,
                    "manufacturer": manufacturer,
                    "color": color,
                    "price": price,
                    "stock": stock,
                    "recommended": recommended,
                    "category": categories[cat_id],
                },
            )
            items[item_id] = obj
        self.stdout.write(self.style.SUCCESS(f"商品: {len(items)}件"))

        # ====================================
        # カート内商品 (shopping_itemsincart)
        # ※ booked_date は auto_now_add のため実行時刻が入ります
        # ====================================
        cart_data = [
            # (amount, item_id, user_id)
            (1, 101, "user001"),
            (3, 103, "user002"),
            (2, 102, "user003"),
            (1, 104, "user004"),
            (2, 105, "user005"),
        ]
        # 重複投入を避けるため一旦削除してから作成
        Itemincart.objects.all().delete()
        cart_objs = [
            Itemincart(amount=amount, item=items[item_id], user=accounts[user_id])
            for amount, item_id, user_id in cart_data
        ]
        Itemincart.objects.bulk_create(cart_objs)
        self.stdout.write(self.style.SUCCESS(f"カート内商品: {len(cart_objs)}件"))

        # ====================================
        # 注文 (shopping_purchase)
        # ====================================
        purchases_data = [
            # (purchase_id, destination, cancel, user_id)
            (1001, "東京都新宿区西新宿1-1-1", False, "user001"),
            (1002, "大阪府大阪市北区梅田2-2-2", False, "user002"),
            (1003, "愛知県名古屋市中区栄3-3-3", True, "user003"),
            (1004, "福岡県福岡市博多区博多駅前4-4-4", False, "user004"),
            (1005, "北海道札幌市中央区大通西5-5-5", False, "user005"),
        ]
        purchases = {}
        for purchase_id, destination, cancel, user_id in purchases_data:
            obj, created = Purchase.objects.update_or_create(
                purchase_id=purchase_id,
                defaults={
                    "destination": destination,
                    "cancel": cancel,
                    "user": accounts[user_id],
                },
            )
            purchases[purchase_id] = obj
        self.stdout.write(self.style.SUCCESS(f"注文: {len(purchases)}件"))

        # ====================================
        # 注文詳細 (shopping_purchasedetail)
        # ====================================
        details_data = [
            # (purchase_detail_id, amount, item_id, purchase_id)
            (10001, 1, 101, 1001),
            (10002, 2, 103, 1002),
            (10003, 1, 102, 1003),
            (10004, 1, 104, 1004),
            (10005, 3, 105, 1005),
        ]
        for detail_id, amount, item_id, purchase_id in details_data:
            Purchasedetail.objects.update_or_create(
                purchase_detail_id=detail_id,
                defaults={
                    "amount": amount,
                    "item": items[item_id],
                    "purchase": purchases[purchase_id],
                },
            )
        self.stdout.write(self.style.SUCCESS(f"注文詳細: {len(details_data)}件"))

        # ====================================
        # 管理者 (administrator_admin)
        # ====================================
        admins_data = [
            ("admin001", "adminpass001"),
            ("admin002", "adminpass002"),
            ("admin003", "adminpass003"),
            ("admin004", "adminpass004"),
            ("admin005", "adminpass005"),
        ]
        for admin_id, raw_password in admins_data:
            Admin.objects.update_or_create(
                admin_id=admin_id,
                defaults={"password": make_password(raw_password)},
            )
        self.stdout.write(self.style.SUCCESS(f"管理者: {len(admins_data)}件"))

        self.stdout.write(self.style.SUCCESS("=== サンプルデータの投入が完了しました ==="))