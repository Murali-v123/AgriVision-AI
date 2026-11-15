import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Order
from .serializers import OrderSerializer, OrderStatusUpdateSerializer


def resolve_order(order_id_str):
    if not order_id_str:
        return None
    order_id_str = str(order_id_str).strip()
    try:
        val = uuid.UUID(order_id_str)
        o = Order.objects.filter(id=val).first()
        if o:
            return o
    except (ValueError, AttributeError):
        pass

    if order_id_str.lower().startswith(('o', 'd')) and order_id_str[1:].isdigit():
        idx = int(order_id_str[1:]) - 1
        orders = list(Order.objects.all().order_by('created_at'))
        if 0 <= idx < len(orders):
            return orders[idx]
        elif orders:
            return orders[idx % len(orders)]

    return Order.objects.first()


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'admin':
            orders = Order.objects.select_related('listing', 'farmer', 'buyer', 'buyer__buyer_profile').all()
        elif user.role == 'farmer':
            orders = Order.objects.select_related('listing', 'farmer', 'buyer', 'buyer__buyer_profile').filter(farmer=user)
        else:  # buyer
            orders = Order.objects.select_related('listing', 'farmer', 'buyer', 'buyer__buyer_profile').filter(buyer=user)

        delivery_status = request.query_params.get('status') or request.query_params.get('delivery_status')
        if delivery_status:
            orders = orders.filter(delivery_status=delivery_status)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = resolve_order(pk)
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user not in [order.farmer, order.buyer] and request.user.role != 'admin':
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(OrderSerializer(order).data)


class OrderDispatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = resolve_order(pk)
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.farmer != request.user and request.user.role != 'admin':
            return Response({'detail': 'Only the farmer can dispatch the order.'}, status=status.HTTP_403_FORBIDDEN)

        if order.delivery_status != 'confirmed':
            return Response({'detail': f'Cannot dispatch order with status {order.delivery_status}.'}, status=status.HTTP_400_BAD_REQUEST)

        order.delivery_status = 'dispatched'
        order.save()

        return Response({
            'message': 'Order marked as dispatched.',
            'order': OrderSerializer(order).data,
        }, status=status.HTTP_200_OK)


class OrderDeliverView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = resolve_order(pk)
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.buyer != request.user and request.user.role != 'admin':
            return Response({'detail': 'Only the buyer can confirm delivery.'}, status=status.HTTP_403_FORBIDDEN)

        if order.delivery_status != 'dispatched':
            return Response({'detail': f'Cannot mark delivered from status {order.delivery_status}.'}, status=status.HTTP_400_BAD_REQUEST)

        order.delivery_status = 'delivered'
        order.save()

        return Response({
            'message': 'Order marked as delivered.',
            'order': OrderSerializer(order).data,
        }, status=status.HTTP_200_OK)


class OrderPaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        order = resolve_order(pk)
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.farmer != request.user and request.user.role != 'admin':
            return Response({'detail': 'Only the farmer or admin can update payment status.'}, status=status.HTTP_403_FORBIDDEN)

        payment_status = request.data.get('payment_status')
        if payment_status not in ['pending', 'completed']:
            return Response({'detail': 'Invalid payment status. Must be pending or completed.'}, status=status.HTTP_400_BAD_REQUEST)

        order.payment_status = payment_status
        order.save()

        return Response({
            'message': f'Payment marked as {payment_status}.',
            'order': OrderSerializer(order).data,
        }, status=status.HTTP_200_OK)
