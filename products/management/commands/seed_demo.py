"""Fill the store with a demo catalogue: categories, products with generated images, reviews and coupons.

    python manage.py seed_demo          # create or update the demo data
    python manage.py seed_demo --reset  # delete ALL products and categories first
"""
import random
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from orders.models import Coupon
from products.models import Category, Product, Review

CATEGORIES = [
    # name, icon, description, gradient colours
    ('Electronics', 'bi-laptop', 'Phones, audio, smart devices and accessories.', ('#e0e7ff', '#c7d2fe')),
    ('Fashion', 'bi-bag-heart', 'Clothing, shoes and accessories for every day.', ('#fce7f3', '#fbcfe8')),
    ('Home & Kitchen', 'bi-house-heart', 'Everything to make your home cosy and your kitchen smarter.', ('#fef3c7', '#fde68a')),
    ('Beauty', 'bi-stars', 'Skincare, fragrance and self-care essentials.', ('#ede9fe', '#ddd6fe')),
    ('Sports & Fitness', 'bi-bicycle', 'Gear for training, outdoors and an active lifestyle.', ('#dcfce7', '#bbf7d0')),
    ('Books', 'bi-book', 'Bestsellers, self-improvement and learning.', ('#e0f2fe', '#bae6fd')),
]

PRODUCTS = [
    # category, name, emoji, price, sale price, stock, featured, description
    ('Electronics', 'AirWave Pro Wireless Headphones', '🎧', 14999, 11999, 25, True,
     'Active noise cancelling, 40-hour battery and deep bass. Foldable design with a travel case and fast USB-C charging.'),
    ('Electronics', 'Nova X5 Smartphone 128GB', '📱', 64999, None, 12, True,
     '6.5" AMOLED display, 50MP triple camera, 5000mAh battery and 33W fast charging. Includes 1 year official warranty.'),
    ('Electronics', 'PulseFit Smart Watch', '⌚', 9999, 7499, 30, False,
     'Heart-rate and SpO2 monitoring, sleep tracking, 100+ sport modes and 10-day battery life. Water resistant (IP68).'),
    ('Electronics', 'ThinBook 14 Laptop (i5, 16GB)', '💻', 159999, 149999, 6, True,
     'Intel Core i5, 16GB RAM, 512GB SSD and a 14" Full HD IPS screen in a 1.3kg aluminium body. Perfect for work and study.'),
    ('Fashion', 'Classic Leather Backpack', '🎒', 7999, None, 18, False,
     'Genuine leather with a padded 15" laptop sleeve, water-resistant lining and comfortable shoulder straps.'),
    ('Fashion', 'Urban Runner Sneakers', '👟', 8999, 6299, 22, True,
     'Lightweight knit upper, cushioned sole and breathable lining for all-day comfort. Available in sizes 39–45.'),
    ('Fashion', 'Everyday Cotton T-Shirt (Pack of 3)', '👕', 3499, None, 50, False,
     '100% combed cotton, pre-shrunk and soft on the skin. Pack includes black, white and navy.'),
    ('Fashion', 'Aviator Sunglasses UV400', '🕶️', 2999, 1999, 3, False,
     'Polarised lenses with full UV400 protection and a lightweight metal frame. Comes with a hard case.'),
    ('Home & Kitchen', 'BrewMaster Coffee Maker', '☕', 18999, 15999, 9, True,
     'Brew up to 12 cups with programmable timer, keep-warm plate and reusable filter. Make café-style coffee at home.'),
    ('Home & Kitchen', 'Ceramic Non-Stick Cookware Set', '🍳', 12499, None, 14, False,
     '5-piece PFOA-free ceramic set with glass lids. Works on gas, electric and induction cooktops.'),
    ('Home & Kitchen', 'Aroma Scented Candle Trio', '🕯️', 2499, 1899, 40, False,
     'Hand-poured soy wax candles in vanilla, lavender and sandalwood. 30 hours burn time each.'),
    ('Home & Kitchen', 'Indoor Potted Plant (Snake Plant)', '🪴', 1999, None, 2, False,
     'Low-maintenance air-purifying plant in a modern ceramic pot. Perfect for bedrooms and offices.'),
    ('Beauty', 'Glow Vitamin C Serum 30ml', '🧴', 3299, 2499, 35, True,
     '15% Vitamin C with hyaluronic acid for brighter, even-toned skin. Suitable for all skin types.'),
    ('Beauty', 'Signature Eau de Parfum 100ml', '🌸', 8999, None, 11, False,
     'A long-lasting floral and woody fragrance with notes of jasmine, amber and musk.'),
    ('Beauty', 'Matte Lipstick Collection', '💄', 2799, 2199, 27, False,
     'Set of 4 creamy, long-wear matte shades enriched with vitamin E. Cruelty-free.'),
    ('Beauty', 'Hydrating Face Mask (Pack of 10)', '🧖', 1499, None, 60, False,
     'Sheet masks with aloe vera and green tea for instant hydration and glow.'),
    ('Sports & Fitness', 'ProGrip Yoga Mat 6mm', '🧘', 3999, 2999, 20, True,
     'Non-slip, extra thick TPE mat with alignment lines and a carry strap. Easy to clean.'),
    ('Sports & Fitness', 'Adjustable Dumbbell Set 20kg', '🏋️', 15999, None, 7, False,
     'Quick-lock adjustable dumbbells from 2.5kg to 20kg. Replace a full rack of weights at home.'),
    ('Sports & Fitness', 'Trail Mountain Bike 27.5"', '🚲', 74999, 67999, 4, True,
     'Aluminium frame, 21-speed Shimano gears, front suspension and dual disc brakes.'),
    ('Sports & Fitness', 'Insulated Water Bottle 1L', '🥤', 1999, 1499, 45, False,
     'Double-wall stainless steel keeps drinks cold for 24h or hot for 12h. Leak-proof lid.'),
    ('Books', 'Atomic Habits (Paperback)', '📘', 2499, 1999, 30, True,
     'A proven framework to build good habits and break bad ones, by James Clear.'),
    ('Books', 'Python Crash Course, 3rd Edition', '🐍', 5499, None, 15, False,
     'A hands-on, project-based introduction to programming with Python.'),
    ('Books', 'The Psychology of Money', '📗', 2299, None, 1, False,
     'Timeless lessons on wealth, greed and happiness by Morgan Housel.'),
    ('Books', 'Deep Work (Paperback)', '📙', 2199, 1799, 0, False,
     'Rules for focused success in a distracted world, by Cal Newport.'),
]

REVIEWERS = [('ayesha_k', 'Ayesha'), ('bilal_r', 'Bilal'), ('hina_s', 'Hina'), ('usman_t', 'Usman'),
             ('sara_m', 'Sara'), ('ali_h', 'Ali')]
COMMENTS = {
    5: ['Absolutely love it, exactly as described!', 'Excellent quality and super fast delivery.',
        'Best purchase this year. Highly recommended.', 'Premium feel and great value for money.'],
    4: ['Very good product, packaging could be better.', 'Works great, delivery took a day longer.',
        'Good quality for the price. Happy with it.'],
    3: ['Decent product, does the job.', 'Okay overall, expected a little more.'],
}
COUPONS = [
    ('WELCOME10', Coupon.PERCENT, 10, 0, None),
    ('SAVE500', Coupon.FIXED, 500, 3000, None),
    ('FLASH20', Coupon.PERCENT, 20, 10000, 100),
]


def make_image(emoji, colours, size=800):
    """Soft gradient tile with a big emoji in the middle (falls back to plain gradient without the emoji font)."""
    top, bottom = (Image.new('RGB', (1, 1), c).getpixel((0, 0)) for c in colours)
    image = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(image)
    for y in range(size):
        t = y / size
        draw.line([(0, y), (size, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    draw.ellipse([size * .18, size * .18, size * .82, size * .82], fill=(255, 255, 255))

    font_path = Path('C:/Windows/Fonts/seguiemj.ttf')
    for candidate in (font_path, Path('/System/Library/Fonts/Apple Color Emoji.ttc'),
                      Path('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf')):
        if candidate.exists():
            try:
                font = ImageFont.truetype(str(candidate), 109 if 'Noto' in candidate.name else 300)
                glyph = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                ImageDraw.Draw(glyph).text((size / 2, size / 2), emoji, font=font, anchor='mm', embedded_color=True)
                bbox = glyph.getbbox()
                if bbox:
                    glyph = glyph.crop(bbox)
                    glyph.thumbnail((int(size * .42), int(size * .42)))
                    image.paste(glyph, ((size - glyph.width) // 2, (size - glyph.height) // 2), glyph)
                break
            except OSError:
                continue

    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=88)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = 'Create a demo catalogue (categories, products with images, reviews and coupon codes).'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete ALL products and categories first')

    def handle(self, *args, **options):
        random.seed(42)  # same demo data every time
        if options['reset']:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING('Deleted existing products and categories.'))

        colours = {}
        categories = {}
        for name, icon, description, gradient in CATEGORIES:
            categories[name], _ = Category.objects.update_or_create(
                name=name, defaults={'icon': icon, 'description': description})
            colours[name] = gradient

        User = get_user_model()
        reviewers = []
        for username, first_name in REVIEWERS:
            user, created = User.objects.get_or_create(username=username, defaults={'first_name': first_name})
            if created:
                user.set_unusable_password()  # demo reviewers can't log in
                user.save()
            reviewers.append(user)

        for category, name, emoji, price, sale, stock, featured, description in PRODUCTS:
            product, created = Product.objects.update_or_create(name=name, defaults={
                'category': categories[category], 'description': description, 'price': Decimal(price),
                'sale_price': Decimal(sale) if sale else None, 'stock': stock, 'is_featured': featured,
            })
            if created or not product.image:
                slug = categories[category].slug + '-' + str(product.pk)
                product.image.save(f'{slug}.jpg', make_image(emoji, colours[category]), save=True)

            if not product.reviews.exists():
                for user in random.sample(reviewers, random.randint(2, 5)):
                    rating = random.choices([5, 4, 3], weights=[6, 3, 1])[0]
                    Review.objects.create(product=product, user=user, rating=rating,
                                          comment=random.choice(COMMENTS[rating]))

        for code, kind, value, minimum, limit in COUPONS:
            Coupon.objects.update_or_create(code=code, defaults={
                'discount_type': kind, 'value': Decimal(value), 'min_order_amount': Decimal(minimum),
                'usage_limit': limit, 'active': True})

        self.stdout.write(self.style.SUCCESS(
            f'Demo store ready: {Category.objects.count()} categories, {Product.objects.count()} products, '
            f'{Review.objects.count()} reviews, coupons: {", ".join(c[0] for c in COUPONS)}'))
