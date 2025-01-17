from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.core.exceptions import ObjectDoesNotExist
from .forms import CustomUserCreationForm, ForgotPasswordForm, ResetPasswordForms
from django.contrib.auth.models import AnonymousUser

from django.shortcuts import render
from .models import Product

# views.py

from django.shortcuts import render

def home(request):
    # Fetch all trending products
    trending_products = Product.objects.filter(trending=True)

    # Fetch visible categories
    categories = Catagory.objects.filter(status=False)

    # You can pass the first category to the template or all categories, depending on your needs
    category = categories.first()  # For example, passing the first category

    return render(request, 'shop/home.html', {
        'products': trending_products,
        'categories': categories,
        'category': category  # Pass category to the template
    })


def collections(request):
    categories = Catagory.objects.filter(status=False)  # Fetch active categories
    return render(request, 'shop/collections.html', {"categories": categories})

def collectionsview(request, name):
    try:
        category = Catagory.objects.get(name=name, status=False)  # Use status=False for active categories
        products = Product.objects.filter(category=category, status=True)  # Use status=True for active products
        return render(request, "shop/product/index.html", {"products": products, "category": category})
    except Catagory.DoesNotExist:
        messages.warning(request, "No Such Category Found")
        return redirect('collections')

def register(request):
    return render(request, 'shop/register.html')

def project_details(request, cname, pname):
    try:
        product = Product.objects.get(name=pname, status=True)
        category = Catagory.objects.get(name=cname, status=False)
        
        # Check if the user is logged in and get the wishlist
        if isinstance(request.user, AnonymousUser):
            user_wishlist = []  # No wishlist for anonymous users
        else:
            user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product', flat=True)
        
        # Check if the current product is in the user's wishlist
        is_in_wishlist = product.id in user_wishlist
        
        # Pass the information to the template
        return render(
            request, 
            'shop/product/product_details.html', 
            {
                'category': category,
                'product': product,
                'is_in_wishlist': is_in_wishlist  # New variable to indicate wishlist status
            }
        )
    except (Product.DoesNotExist, Catagory.DoesNotExist):
        messages.warning(request, "No Such Product or Category Found")
        return redirect('collections')
@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('index')
    
    if product.quantity > 0:
        quantity = int(request.POST.get('quantity', 1))  # Get quantity from form (default to 1 if not provided)
        
        # Use get_or_create to check if the cart item already exists for the user and product
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}  # Correct way to pass defaults
        )

        if not created:
            cart_item.quantity += quantity  # Update the quantity if the item already exists
            cart_item.save()
            messages.success(request, f"{product.name} quantity updated in your cart.")
        else:
            messages.success(request, f"{product.name} added to your cart.")

        return redirect('cart')
    else:
        messages.error(request, f"Sorry, {product.name} is out of stock.")
        return redirect('index')
import os
import qrcode
from django.conf import settings
def generate_qr_code(total_price, user_id):
    # Define the static directory for storing QR codes
    qr_code_dir = os.path.join(settings.BASE_DIR, 'static', 'qr_codes')  # qr_codes inside static

    # Ensure the directory exists, if not, create it
    if not os.path.exists(qr_code_dir):
        os.makedirs(qr_code_dir)

    # Generate the QR code content
    qr_content = f'upi://pay?pa=cnarul138-2@oksbi&pn=Shopkart&am={total_price}&cu=INR'

    # Create the QR code image
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_content)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    # Define the file path for the QR code image
    qr_filename = f'qr_{user_id}.png'

    qr_file_path = os.path.join(qr_code_dir, qr_filename)

    # Save the QR code image
    img.save(qr_file_path)
    print(qr_file_path)

    return os.path.join('qr_codes', qr_filename)  # Return relative path for use in the template


from django.shortcuts import redirect

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Cart, Order, OrderProduct
import os

@login_required(login_url='/login/')
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.selling_price * item.quantity for item in cart_items)

    qr_code_path = None  # Default to None
    if total_price > 0:  # Only generate the QR if there are items in the cart
        qr_code_path = generate_qr_code(total_price, request.user)
    
    if request.method == 'POST':
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id',None)  # Get transaction_id, default to None if not provided

        if cart_items:
            if payment_method == 'online' and not transaction_id:
                # If payment method is online and transaction_id is missing
                messages.warning(request, "Transaction ID is required for online payments.")
                return redirect('cart')  # Reload the cart page
            
            # Create the order
            order = Order.objects.create(
                user=request.user,
                address=address,
                phone_number=phone_number,
                payment_method=payment_method,
                total_price=total_price,
                status='Pending',
                transaction_id=transaction_id if payment_method == 'online' else 0
            )
            
            for item in cart_items:
                OrderProduct.objects.create(
                    order=order, 
                    product=item.product, 
                    quantity=item.quantity
                )
                
                # Deduct product quantity from stock
                item.product.quantity -= item.quantity
                item.product.save()

            # Clear the cart after order placement
            cart_items.delete()
            
            # Delete the QR code after successful order placement
            if qr_code_path:
                os.remove("static/" + qr_code_path)
            
            messages.success(request, "Your order has been placed successfully.")
            return redirect('order_confirmation', order_id=order.id)
        else:
            messages.warning(request, "Your cart is empty.")

    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'qr_code_path': qr_code_path
    })

from django.contrib import messages

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Signup successful! You can now log in.")
            return redirect('login')
        else:
            # Collect all form errors and display them
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'shop/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if the input is a valid username or email
        try:
            user = User.objects.get(email=username_or_email)
            username = user.username
        except User.DoesNotExist:
            username = username_or_email

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            mes = messages.get_messages(request)
            for m in mes:
                pass
            messages.success(request, "Login successful!")
            return redirect('index')
        else:
            messages.error(request, "Invalid username or email, and/or password.")
    
    return render(request, 'shop/login.html')

def logout_view(request):
    logout(request)
    mes = messages.get_messages(request)
    for m in mes:
        pass
    messages.success(request, "You have logged out successfully.")
    return redirect('index')

@login_required(login_url='/login/')
def view_orders(request):
    orders = Order.objects.filter(user=request.user)
    context = {'orders': orders}
    return render(request, 'shop/order.html', context)

@login_required(login_url='/login/')
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_confirmation.html', {'order': order})
@login_required(login_url='/login/')
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.selling_price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        address = request.POST['address']
        payment_method = request.POST['payment_method']
        transaction_id = request.POST.get('transaction_id', None)  # Get transaction_id, default to None if not provided
        
        if cart_items:  # Ensure cart is not empty
            if payment_method == 'online' and not transaction_id:
                # If payment method is online and transaction_id is not provided, show a warning
                mes = messages.get_messages(request)
                for m in mes:
                    pass
                messages.warning(request, "Transaction ID is required for online payments.")
                return redirect('checkout')  # Reload the checkout page
            print(payment_method)
            if payment_method == 'online':
                print("online payment")
            # Create an order
            order = Order.objects.create(
                user=request.user,
                address=address,
                payment_method=payment_method,
                total_price=total_price,
                status='Pending',  # Set initial order status to Pending
                transaction_id=transaction_id if payment_method == 'online' else None  # Save transaction_id for online payment
            )
            
            # Create OrderProduct entries for each item in the cart
            for item in cart_items:
                orderProduct = OrderProduct.objects.create(
                    order=order, 
                    product=item.product, 
                    quantity=item.quantity
                )
                
                # Deduct product quantity from stock
                item.product.quantity -= item.quantity  
                item.product.save()
                
                orderProduct.save()  # Save the order product
                print(f"Product {item.product.name} with quantity {item.quantity} saved to OrderProduct.")
            
            # Clear the cart after the order is placed
            cart_items.delete()  
            
            # Provide a success message
            messages.success(request, "Your order has been placed successfully.")
            return redirect('order_confirmation', order_id=order.id)
        else:
            messages.warning(request, "Your cart is empty.")
    
    return render(request, 'shop/checkout.html', {'cart_items': cart_items, 'total_price': total_price})



def remove_from_cart(request, cart_item_id):
    try:
        cart_item = Cart.objects.get(id=cart_item_id, user=request.user)
        cart_item.delete()
        messages.success(request, "Item removed from your cart.")
    except Cart.DoesNotExist:
        messages.error(request, "This item is not in your cart.")
    return redirect('cart')

#address update part

@login_required
def update_address(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        user = request.user

        # Update the user's last order address
        last_order = user.order_set.last()
        if last_order:
            last_order.address = address
            last_order.phone_number = phone_number
            last_order.save()
            messages.success(request, "Address updated successfully.")
        else:
            messages.error(request, "No previous orders found to update address.")
        
        return redirect('view_cart')  # Redirect back to cart page

#Reset Password Codes
import random
import string
from django.contrib.sites.shortcuts import get_current_site
from .models import Profile
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
def forgot_password(request):
    form = ForgotPasswordForm()
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']  # Use cleaned_data to access the validated email
            try:
                user = User.objects.get(email=email)
                # Send email to reset password
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk)) 
                domain = request.get_host()

                subject = "Reset Password Requested"
                message = render_to_string('shop/reset_password_email.html', {
                    'domain': domain,
                    'token': token,
                    'uid': uid
                })
                send_mail(subject, message, 'noreply@example.com', [email])
                messages.success(request, 'Email has been sent successfully')
                print(domain)
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email address')  # Extra safeguard (not strictly necessary)
        else:
            messages.error(request, 'Invalid form submission')  # Show this only if form is invalid

    return render(request, "shop/forgot_password.html", {"form": form})


def reset_password(request, uidb64, token):
    if request.method == "POST":
        print("Post is enter")
        form = ResetPasswordForms(request.POST)
        print(form.errors)
        if form.is_valid():
            print("forms vaild")
            new_password = form.cleaned_data['new_password']
            try:
                uid = urlsafe_base64_decode(uidb64).decode()
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None
            if user is not None and default_token_generator.check_token(user, token):
                print("Token is valid")
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your Password has Been Reset Successfully.")
                return redirect('login')
            else:
                print("Invalid token or user")
                messages.error(request, "The password reset link is invalid.")
    else:
        form = ResetPasswordForms()  # Render the form for GET requests.

    return render(request, 'shop/reset_password.html', {"form": form})



    #online payment
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def razorpay_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body)
        # Verify Razorpay signature
        try:
            client = razorpay.Client(auth=("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET"))
            client.utility.verify_payment_signature(data)
            # Process payment success logic here
            return JsonResponse({"status": "success"}, status=200)
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"status": "failure"}, status=400)
        

#cancel Order

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.can_cancel():
        # Mark the order as canceled
        order.is_canceled = True
        order.save()

        # Adjust the stock for each product in the order
        order_products = OrderProduct.objects.filter(order=order)
        for order_product in order_products:
            order_product.product.quantity += order_product.quantity
            order_product.product.save()

        messages.success(request, "Your order has been canceled.")
    else:
        messages.error(request, "Cancellation period has expired.")

    return redirect(reverse("view_orders"))


@login_required
def add_to_wishlist(request, category, product_id):
    product = Product.objects.get(id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()

    if wishlist_item:
        # Item already in wishlist, remove it
        wishlist_item.delete()
        message = "Product removed from wishlist!"
    else:
        # Item not in wishlist, add it
        Wishlist.objects.create(user=request.user, product=product)
        message = "Product added to wishlist!"

    # Optionally, pass the message or redirect to a product details page
    return redirect(reverse('project_details', kwargs={'cname': category, 'pname': product.name}))
@login_required

def wishlist_view(request):
    # Get the user's wishlist and related product information
    user_wishlist = Wishlist.objects.filter(user=request.user).select_related('product')

    # Get category details for each product (assuming each product belongs to a category)
    products_with_categories = [
        {
            'product': item.product,
            'category': item.product.category  # Assuming `category` is a ForeignKey in Product
        }
        for item in user_wishlist
    ]

    return render(
        request,
        'shop/wishlist.html',
        {'user_wishlist': products_with_categories}
    )

def remove_from_wishlist(request, product_id):
    # Get the product to remove from the wishlist
    product = get_object_or_404(Product, id=product_id)

    # Get or create the wishlist item for the current user
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
    print("Enter")
    if wishlist_item:
        # Remove the product from the user's wishlist
        wishlist_item.delete()
        print("remove")
        messages.success(request, f'Removed {product.name} from your wishlist.')
    else:
        messages.warning(request, f'{product.name} is not in your wishlist.')

    # Redirect back to the wishlist page
    return redirect('wishlist_view')

def search_products(request):
    query = request.GET.get('q', '')  # Get the search query from the request
    results = []
    category = None

    if query:
        # Search in product name and description
        results = Product.objects.filter(name__icontains=query) | Product.objects.filter(description__icontains=query)

        # Get the category of the results if available
        if results.exists():
            category = results.first().category  # Assuming products belong to a single category

    return render(request, 'shop/search_results.html', {
        'query': query,
        'results': results,
        'category': category,
    })

