import pyotp
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin

class Product(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title

class Account(AbstractUser, PermissionsMixin):
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    
    def generate_totp_secret(self):
        secret = pyotp.random_base32()
        self.totp_secret = secret
        self.save()
        return secret
    
    def get_totp_uri(self):
        if not self.totp_secret:
            raise ValueError("Secret not set")
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            self.email,
            issuer_name="SecdevWebshopQuinn"
        )

    def __str__(self):
        return self.first_name

class Cart(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="cart")
    products = models.ManyToManyField(Product, through='CartProduct', related_name='cart_products')

class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['added_at']