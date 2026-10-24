from django.contrib import admin
from .models import Category, Product, Review, WishlistItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'sale_price', 'stock', 'is_featured', 'created_at')
    list_editable = ('price', 'sale_price', 'stock', 'is_featured')
    list_filter = ('category', 'is_featured')
    search_fields = ('name', 'description')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__username', 'comment')


admin.site.register(WishlistItem)
