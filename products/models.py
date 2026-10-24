from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-grid', help_text='Bootstrap icon class, e.g. bi-laptop')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def with_ratings(self):
        """Add avg_rating and review_count in one query (avoids a query per product card)."""
        return self.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews', distinct=True))


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     help_text='Leave empty when the product is not on sale')
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.sale_price is not None and self.sale_price >= self.price:
            raise ValidationError({'sale_price': 'Sale price must be lower than the regular price.'})

    @property
    def on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def current_price(self):
        return self.sale_price if self.on_sale else self.price

    @property
    def discount_percent(self):
        if not self.on_sale or not self.price:
            return 0
        return round((self.price - self.sale_price) / self.price * 100)

    @property
    def savings(self):
        return self.price - self.current_price

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def rating(self):
        """Average star rating (uses the with_ratings() annotation when available)."""
        if hasattr(self, 'avg_rating'):
            return round(self.avg_rating or 0, 1)
        return round(self.reviews.aggregate(avg=Avg('rating'))['avg'] or 0, 1)

    @property
    def reviews_total(self):
        if hasattr(self, 'review_count'):
            return self.review_count
        return self.reviews.count()

    def __str__(self):
        return self.name


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')  # one review per customer per product

    def __str__(self):
        return f'{self.rating}★ {self.product} by {self.user}'


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user} ♥ {self.product}'


def user_can_review(user, product):
    """Only customers with a paid (processing / shipped / delivered) order containing the product."""
    if not user.is_authenticated:
        return False
    return product.orderitem_set.filter(
        order__user=user, order__status__in=['processing', 'shipped', 'delivered']).exists()
