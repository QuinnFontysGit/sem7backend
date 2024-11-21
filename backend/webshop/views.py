from rest_framework import viewsets, status, serializers
from .models import Product, Cart, Account
from .serializers import ProductSerializer, CartSerializer
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

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

@api_view(['POST'])
def logout_view(request):
    logout(request)
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

        user = Account.objects.create_user(username=username, password=password, email=email,
                                           address=address, first_name=first_name, last_name=last_name)

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

    login(request, user)
    return Response({"message": "Login successful", "username": user.username})