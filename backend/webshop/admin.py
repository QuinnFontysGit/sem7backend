from django.contrib import admin
from .models import Cart, CartProduct, Product, Account

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'address')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'price', 'stock')
    search_fields = ('cart__account__first_name', 'product__title')

class CartProductInline(admin.TabularInline):
    model = CartProduct
    extra = 1
    fields = ('product', 'quantity')
    autocomplete_fields = ['product']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'account')
    inlines = [CartProductInline]