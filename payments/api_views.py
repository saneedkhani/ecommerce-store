from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer, PaymentStatusSerializer
from .services import set_payment_status


@extend_schema(tags=['Payments (staff)'], parameters=[
    OpenApiParameter('status', str, description='Filter by payment status, e.g. pending'),
])
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff only: review submitted payments."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        payments = Payment.objects.select_related('user', 'order').order_by('-created_at')
        if self.request.query_params.get('status'):
            payments = payments.filter(status=self.request.query_params['status'])
        return payments

    @extend_schema(request=PaymentStatusSerializer, responses=PaymentSerializer)
    @action(detail=True, methods=['post'])
    def status(self, request, pk=None):
        """Verify, reject or mark a payment as not received. Updates the order (and stock on reject)."""
        payment = self.get_object()
        serializer = PaymentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_payment_status(payment, serializer.validated_data['status'])
        return Response(PaymentSerializer(payment, context={'request': request}).data)
