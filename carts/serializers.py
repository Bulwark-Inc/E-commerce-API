from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=CartItem.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']
        read_only_fields = ['id', 'product', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price']
        read_only_fields = ['id', 'user', 'items', 'total_price']
