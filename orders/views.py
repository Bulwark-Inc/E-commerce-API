from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order, OrderItem
from carts.models import Cart, CartItem
from .serializers import OrderSerializer

# Checkout → convert cart to order
class CheckoutView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        cart = Cart.objects.filter(user=user).first()

        if not cart or not cart.items.exists():
            return Response({'error': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Create Order
        order = Order.objects.create(user=user)
        total_price = 0

        # Move items from cart to order
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price  # snapshot of price
            )
            total_price += item.product.price * item.quantity

        order.total_price = total_price
        order.save()

        # Clear cart
        cart.items.all().delete()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# List user's orders
class OrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


# Order detail
class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
