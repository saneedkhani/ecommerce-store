from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'image', 'created_at']
        read_only_fields = ['created_at']
        extra_kwargs = {'price': {'min_value': 0}}
