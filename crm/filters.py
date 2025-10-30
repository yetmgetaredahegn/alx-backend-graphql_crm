import django_filters
from .models import Customer, Order, Product

class CustomerFilter(django_filters.FilterSet):
    # Case-insensitive partial match for name
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    # Case-insensitive partial match for email
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")

    # Date range filters
    created_at__gte = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_at__lte = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    # Custom filter: phone starts with "+1"
    phone_pattern = django_filters.CharFilter(method="filter_phone_pattern")

    def filter_phone_pattern(self, queryset, name, value):
        # This allows pattern-based matching for phone numbers
        return queryset.filter(phone__startswith=value)

    class Meta:
        model = Customer
        fields = ["name", "email", "created_at"]



class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    price__gte = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price__lte = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    stock__gte = django_filters.NumberFilter(field_name="stock", lookup_expr="gte")
    stock__lte = django_filters.NumberFilter(field_name="stock", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["name", "price", "stock"]



class OrderFilter(django_filters.FilterSet):
    total_amount__gte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    total_amount__lte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    order_date__gte = django_filters.DateFilter(field_name="order_date", lookup_expr="gte")
    order_date__lte = django_filters.DateFilter(field_name="order_date", lookup_expr="lte")

    # Related model filtering
    customer_name = django_filters.CharFilter(field_name="customer__name", lookup_expr="icontains")
    product_name = django_filters.CharFilter(field_name="product__name", lookup_expr="icontains")

    # Challenge: Filter orders that include a specific product ID
    product_id = django_filters.NumberFilter(field_name="product__id")

    class Meta:
        model = Order
        fields = [
            "total_amount",
            "order_date",
            "customer_name",
            "product_name",
        ]
