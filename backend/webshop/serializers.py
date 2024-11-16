from .models import Product, Cart, CartProduct, Account
from rest_framework import serializers

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'address')
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        account = Account.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            address=validated_data['address']
        )
        return account

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'stock', 'created_at']
        read_only_fields = ['created_at']

class CartProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartProduct
        fields = ['product', 'quantity', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    products = CartProductSerializer(source='cartproduct_set', many=True)

    class Meta:
        model = Cart
        fields = ['id', 'account', 'products']
