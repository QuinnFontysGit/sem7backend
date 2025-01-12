from rest_framework import viewsets, status, serializers
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from .models import Product, Cart, Account, CartProduct
from .serializers import ProductSerializer, CartSerializer, CartProductSerializer
import qrcode
import base64
import qrcode.image.svg
from io import BytesIO
from django.http import JsonResponse
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.decorators import api_view
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from django.contrib.auth.models import Group
from .permissions import IsManagerOrReadOnly, IsCartOwner, IsCustomer
from django_ratelimit.decorators import ratelimit

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsManagerOrReadOnly]

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    
    def get(self, request, *args, **kwargs):
        cart = Cart.objects.filter(account__id=self.request.user.id).first()

        if not cart:
            raise NotFound("No cart found for this user.")

        cartproducts = CartProduct.objects.filter(cart=cart)

        if not cartproducts.exists():
            return Response({"detail": "Your cart is empty."}, status=200)

        serializer = self.serializer_class(cartproducts, many=True)
        return Response(serializer.data)

    permission_classes = [IsCartOwner]

@api_view(['POST'])
def logout_view(request):
    logout(request)
    if request.session:
        request.session.flush()
    return Response({"message": "Logged out successfully!"}, status=200)

@api_view(['POST'])
def register_user(request):
    if request.method == "POST":
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        address = request.data.get("address")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        user = Account.objects.create_user(username=username, email=email,
                                           address=address, first_name=first_name, last_name=last_name)
        user.set_password(password)
        
        Cart.objects.create(account=user)
        
        role = Group.objects.get(name="Customer")
        user.groups.add(role)

        device = TOTPDevice.objects.create(user=user, confirmed=False)

        otp_url = device.config_url
        qr = qrcode.make(otp_url, image_factory=qrcode.image.svg.SvgImage)
        buffer = BytesIO()
        qr.save(buffer)
        buffer.seek(0)

        qr_code_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        qr_code_data_uri = f"data:image/svg+xml;base64,{qr_code_base64}"

        return JsonResponse({"qr_code": qr_code_data_uri, "user_id": user.id})

@api_view(['POST'])
def verify_totp_setup(request):
    if request.method == "POST":
        user_id = request.data.get("userId")
        otp = request.data.get("otp")

        try:
            user = Account.objects.get(id=user_id)
            print(user.first_name)
        except Account.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)

        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()

        if not device:
            return JsonResponse({"error": "No TOTP device found."}, status=404)

        if device.verify_token(otp):
            device.confirmed = True
            device.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "Invalid OTP"}, status=400)

@ensure_csrf_cookie
@ratelimit(key='ip', rate='1000/m', block=False)
def get_csrf_token(request):
    return JsonResponse({"detail": "CSRF token set!"})

@api_view(['POST'])
def login_user(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')
    otp = data.get('otp')  

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = TOTPDevice.objects.get(user=user, confirmed=True)
    except TOTPDevice.DoesNotExist:
        return Response({"error": "MFA not set up for this account"}, status=status.HTTP_403_FORBIDDEN)

    if not device.verify_token(otp):
        return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
    
    role = request.user.groups.first().name if request.user.groups.exists() else 'Customer'

    login(request, user)
    return Response({"message": "Login successful", "userid": user.id, "role": role})

@api_view(['POST'])
def add_to_cart(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("You are not logged in.")
    
    user = request.user
    product_id = request.data.get('productid')
    quantity = request.data.get('quantity', 1)

    if not product_id or not isinstance(quantity, int) or quantity <= 0:
        raise ValidationError("Invalid product provided")
    
    try:
        cart = Cart.objects.get(account__id=user.id)
    except Cart.DoesNotExist:
        raise NotFound("You don't have a shopping cart")
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        raise NotFound("Product not found in database")
    
    cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product)
    cart_product.quantity = cart_product.quantity + quantity
    cart_product.save()

    return Response({"message": "Product added to cart successfully!"})
