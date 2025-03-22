from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product

# Get or create cart helper
def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

# View cart details
class CartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_user_cart(self.request.user)

# Add item to cart
class AddToCartView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart = get_user_cart(request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response({'message': 'Item added to cart'}, status=status.HTTP_200_OK)

# Remove item from cart
class RemoveFromCartView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        cart = get_user_cart(request.user)
        product_id = kwargs.get('product_id')

        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
            return Response({'message': 'Item removed from cart'}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)
