import uuid
import hmac
import hashlib
import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from orders.models import Order
from .models import Payment
from .serializers import PaymentSerializer
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
@api_view(['POST'])
def paystack_webhook(request):
    from django.http import JsonResponse
    import json

    # Verify signature to prevent unauthorized calls
    paystack_signature = request.headers.get('X-Paystack-Signature')
    secret = settings.PAYSTACK_SECRET_KEY.encode()

    payload = request.body
    expected_signature = hmac.new(secret, payload, hashlib.sha512).hexdigest()

    if paystack_signature != expected_signature:
        return JsonResponse({'error': 'Invalid signature'}, status=403)

    data = json.loads(payload)
    event = data.get('event')

    if event == 'charge.success':
        payment_data = data.get('data', {})
        reference = payment_data.get('reference')

        try:
            payment = Payment.objects.get(reference=reference)
            if payment.verified:
                return JsonResponse({'status': 'already processed'}, status=200)

            # Verify amount
            if int(payment_data['amount']) != int(payment.amount * 100):
                return JsonResponse({'error': 'Amount mismatch'}, status=400)

            payment.verified = True
            payment.save()

            order = payment.order
            order.status = 'paid'
            order.save()

            return JsonResponse({'status': 'success'}, status=200)

        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Payment not found'}, status=404)

    return JsonResponse({'status': 'ignored'}, status=200)

class InitiatePaymentView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        order_id = kwargs.get('order_id')

        try:
            order = Order.objects.get(id=order_id, user=user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 'pending':
            return Response({'error': 'Order already processed'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate unique reference
        reference = str(uuid.uuid4())

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "email": user.email,
            "amount": int(order.total_price * 100),  # Paystack expects kobo
            "reference": reference,
            "callback_url": "https://yourdomain.com/api/v1/payments/verify/"
        }

        response = requests.post(f"{settings.PAYSTACK_BASE_URL}/transaction/initialize", json=data, headers=headers)

        if response.status_code != 200:
            return Response({'error': 'Payment initialization failed'}, status=status.HTTP_400_BAD_REQUEST)

        # Create Payment only after Paystack succeeds
        payment_data = response.json().get('data', {})
        if not payment_data:
            return Response({'error': 'Invalid response from Paystack'}, status=status.HTTP_400_BAD_REQUEST)

        Payment.objects.create(
            order=order,
            reference=reference,
            amount=order.total_price
        )

        # Mark order as "processing" to prevent duplicate payments
        order.status = 'processing'
        order.save()

        return Response({
            'payment_url': payment_data['authorization_url'],
            'reference': reference
        }, status=status.HTTP_200_OK)

class VerifyPaymentView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reference = kwargs.get('reference')
        user = request.user

        try:
            payment = Payment.objects.get(reference=reference, order__user=user)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        if payment.verified:
            return Response({'message': 'Payment already verified'}, status=status.HTTP_200_OK)

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }

        response = requests.get(f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=headers)

        if response.status_code != 200:
            return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        if response_data.get('data', {}).get('status') == 'success':
            payment.verified = True
            payment.save()

            order = payment.order
            order.status = 'paid'
            order.save()

            return Response({'message': 'Payment verified successfully'}, status=status.HTTP_200_OK)

        return Response({'error': 'Payment not successful'}, status=status.HTTP_400_BAD_REQUEST)