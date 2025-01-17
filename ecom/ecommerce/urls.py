from django.urls import path
from . import views

urlpatterns = [
    # Home and Collections
    path('', views.home, name='index'),
    path('collections/', views.collections, name='collections'),
    path('collections/<str:name>/', views.collectionsview, name='collectionsview'),
    path('collections/<str:cname>/<str:pname>/', views.project_details, name='project_details'),
    
    # Cart
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='cart'),

    # Checkout (After Cart, Place Order)
    path('cart/checkout/', views.checkout, name='checkout'),  # Checkout page

    # User Authentication (Login, Logout, Signup)
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Orders (User Order History)
    path('orders/', views.view_orders, name='view_orders'),  # User orders history
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),  # Order confirmation page
        path("update-address/", views.update_address, name="update_address"),
    path('razorpay-webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
path('reset-password/<uidb64>/<token>', views.reset_password, name='reset_password'),
    path('add_to_wishlist/<str:category>/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist_view',views.wishlist_view,name='wishlist_view'),
        path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    #cancel Order
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
        path('search/', views.search_products, name='search_products'),

    
]
