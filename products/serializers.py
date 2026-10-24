from decimal import Decimal
from rest_framework import serializers
from .models import Category, Product, Review, WishlistItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    on_sale = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'category_name', 'description', 'price', 'sale_price',
                  'current_price', 'on_sale', 'discount_percent', 'stock', 'image', 'is_featured',
                  'rating', 'review_count', 'created_at']
        read_only_fields = ['created_at']
        extra_kwargs = {'price': {'min_value': 0}, 'sale_price': {'min_value': 0}}

    def get_rating(self, product) -> Decimal:
        return product.rating

    def get_review_count(self, product) -> int:
        return product.reviews_total

    def validate(self, attrs):
        price = attrs.get('price', getattr(self.instance, 'price', None))
        sale_price = attrs.get('sale_price', getattr(self.instance, 'sale_price', None))
        if sale_price is not None and price is not None and sale_price >= price:
            raise serializers.ValidationError({'sale_price': 'Sale price must be lower than the regular price.'})
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']

    def get_user(self, review) -> str:
        return review.user.first_name or review.user.username


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_id', 'added_at']
        read_only_fields = ['added_at']
