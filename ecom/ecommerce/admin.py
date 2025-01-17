from django.contrib import admin
from .models import Catagory, Product, Cart, Order, OrderProduct,ProductImage,Wishlist

# Register other models in the admin site
admin.site.register(Catagory)
admin.site.register(Product)

# Define a custom admin class for Cart
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'added_at', 'order')  # Added 'order' to list display for better context

# Register the Cart model with the custom CartAdmin
admin.site.register(Cart, CartAdmin)

# Define a custom admin class for OrderProduct
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0  # Set to 0 so no empty forms are displayed

# Define a custom admin class for Order
class OrderAdmin(admin.ModelAdmin):

    def get_ordered_products(self, obj):
        ordered_products = []
        
        # Fetch related OrderProduct entries and display the product name and quantity
        order_products = OrderProduct.objects.filter(order=obj)  # Filter order products by the current order
        
        if order_products.exists():
            for order_product in order_products:
                ordered_products.append(f"{order_product.product.name} (Quantity: {order_product.quantity})")
            return ", ".join(ordered_products)
        return "No Products"

    get_ordered_products.short_description = 'Ordered Products'

    fieldsets = [
        ('Order Details', {'fields': ['user', 'address', 'payment_method', 'phone_number', 'total_price','transaction_id']}), 
        ('Status', {'fields': ['status', 'is_canceled']}),  # Add 'is_canceled' to fieldset
    ]
    
    list_display = ('user', 'ordered_at', 'total_price', 'status', 'is_canceled', 'address', 'get_ordered_products')  # Add 'is_canceled' to list_display
    list_filter = ('status', 'ordered_at', 'is_canceled')  # Add 'is_canceled' to list_filter
    actions = ['delete_selected_orders']

    # Add the inline for OrderProduct
    inlines = [OrderProductInline]

# Register the Order model with the custom OrderAdmin
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)
admin.site.register(ProductImage)
admin.site.register(Wishlist)
