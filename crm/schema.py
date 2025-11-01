import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django import DjangoObjectType

from crm.filters import CustomerFilter, OrderFilter, ProductFilter
from .models import Customer, Product, Order
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from decimal import Decimal


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        fields = ("id", "name", "email", "phone", "created_at")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = ("id", "customer", "products", "total_amount", "order_date")

# Relay Nodes (for pagination)
class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        fields = "__all__"

class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = "__all__"

class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = "__all__"


class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            raise Exception("Invalid email format")

        # Check unique email
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")

        # Validate phone (simple regex)
        if phone and not re.match(r'^\+?\d[\d\-\s]{7,}$', phone):
            raise Exception("Invalid phone number format")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully!")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.JSONString, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created = []
        errors = []
        with transaction.atomic():
            for data in input:
                try:
                    name = data.get("name")
                    email = data.get("email")
                    phone = data.get("phone")

                    if not name or not email:
                        raise ValueError("Name and email are required")
                    validate_email(email)
                    if Customer.objects.filter(email=email).exists():
                        raise ValueError(f"Duplicate email: {email}")
                    if phone and not re.match(r'^\+?\d[\d\-\s]{7,}$', phone):
                        raise ValueError(f"Invalid phone number: {phone}")

                    created.append(Customer.objects.create(name=name, email=email, phone=phone))
                except Exception as e:
                    errors.append(str(e))
        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be positive")
        if stock < 0:
            raise Exception("Stock cannot be negative")

        product = Product.objects.create(name=name, price=Decimal(price), stock=stock)
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids):
        if not product_ids:
            raise Exception("At least one product must be provided")

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            raise Exception("Invalid product IDs")

        order = Order.objects.create(customer=customer)
        order.products.set(products)
        order.calculate_total()
        return CreateOrder(order=order)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()



class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)
    all_customers = DjangoFilterConnectionField(CustomerNode, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductNode, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderNode, filterset_class=OrderFilter)

    def resolve_customers(self,info):
        return Customer.objects.prefetch_related('orders').all()
    
    def resolve_products(self,info):
        return Product.objects.prefetch_related('orders').all()
    
    def resolve_orders(self,info):
        return Order.objects.select_related('customer').prefetch_related('products').all()
    


