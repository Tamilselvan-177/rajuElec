from django.db import models
import datetime
from django.contrib.auth.models import User
import os
from datetime import timedelta
from django.utils.timezone import now

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, blank=True, null=True)  # Store OTP here
    # You can add other fields as needed
    
    def __str__(self):
        return self.user.username
# Function to generate file names for uploaded files
def getFileName(request, filename):
    now_time = datetime.datetime.now().strftime("%Y%m%d%H:%M:%S")
    new_filename = f"{now_time}{filename}"
    return os.path.join('uploads/', new_filename)

class Catagory(models.Model):
    name = models.CharField(max_length=158, null=False, blank=False)
    image = models.ImageField(upload_to=getFileName, null=True, blank=True)
    description = models.TextField(max_length=500, null=False, blank=False)
    status = models.BooleanField(default=False, help_text="False - Visible, True - Hidden")
    trending = models.BooleanField(default=False, help_text="False - Default, True - Trending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Catagory, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, null=False, blank=False)
    vendor = models.CharField(max_length=150, null=False, blank=False)
    product_image = models.ImageField(upload_to=getFileName, null=True, blank=True)
    quantity = models.IntegerField(null=False, blank=False)
    original_price = models.FloatField(null=False, blank=False)
    selling_price = models.FloatField(null=False, blank=False)
    description = models.TextField(max_length=500, null=False, blank=False)
    status = models.BooleanField(default=False, help_text="True - Visible, False - Hidden")
    trending = models.BooleanField(default=False, help_text="False - Default, True - Trending")
    created_at = models.DateTimeField(auto_now_add=True)
    additional_images = models.ManyToManyField('ProductImage', blank=True, related_name='products')


    def __str__(self):
        return self.name

    # Optional validation to ensure selling price is not higher than original price
    def save(self, *args, **kwargs):
        if self.selling_price > self.original_price:
            raise ValueError("Selling price cannot be greater than the original price.")
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='product_images/')



class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=500)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    is_canceled = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=100)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    ordered_at = models.DateTimeField(default=now)  # Use default=now to set the current time
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')])
    products = models.ManyToManyField(Product, through='OrderProduct')
    transaction_id = models.CharField(max_length=255,default=0,null=True)

    def can_cancel(self):
        # Check if the order status is 'Completed', if it is, the order cannot be canceled
        if self.status == 'Completed':
            return False
        # Allow cancellation only if it's within 24 hours from the order date
        return now() <= self.ordered_at + timedelta(hours=24)

    def __str__(self):
        return f"Order {self.id} by {self.user}"



class OrderProduct(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


    def __str__(self):
        return f"{self.product.name} (Quantity: {self.quantity})"
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, related_name="cart_items", on_delete=models.SET_NULL, null=True, blank=True)  # Foreign Key to Order

    def __str__(self):
        return f"{self.product.name} (Quantity: {self.quantity})"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)

    def __str__(self):
        return f"Wishlist item for {self.user.username}: {self.product.name}"
    


