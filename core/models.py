from django.db import models
from django.utils import timezone


class Category(models.Model):
    name    = models.CharField(max_length=100, verbose_name='Nomi (UZ)')
    name_ru = models.CharField(max_length=100, blank=True, verbose_name='Nomi (RU)')
    name_kz = models.CharField(max_length=100, blank=True, verbose_name='Nomi (KZ)')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='Nomi (EN)')
    name_tr = models.CharField(max_length=100, blank=True, verbose_name='Nomi (TR)')
    name_ar = models.CharField(max_length=100, blank=True, verbose_name='Nomi (AR)')
    name_ko = models.CharField(max_length=100, blank=True, verbose_name='Nomi (KO)')
    name_zh = models.CharField(max_length=100, blank=True, verbose_name='Nomi (ZH)')
    icon    = models.CharField(max_length=10, default='🍽️')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'


class MenuItem(models.Model):
    category       = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name           = models.CharField(max_length=200, verbose_name='Nomi (UZ)')
    name_ru        = models.CharField(max_length=200, blank=True, verbose_name='Nomi (RU)')
    name_kz        = models.CharField(max_length=200, blank=True, verbose_name='Nomi (KZ)')
    name_en        = models.CharField(max_length=200, blank=True, verbose_name='Nomi (EN)')
    name_tr        = models.CharField(max_length=200, blank=True, verbose_name='Nomi (TR)')
    name_ar        = models.CharField(max_length=200, blank=True, verbose_name='Nomi (AR)')
    name_ko        = models.CharField(max_length=200, blank=True, verbose_name='Nomi (KO)')
    name_zh        = models.CharField(max_length=200, blank=True, verbose_name='Nomi (ZH)')
    description    = models.TextField(blank=True, verbose_name='Tavsif (UZ)')
    description_ru = models.TextField(blank=True, verbose_name='Tavsif (RU)')
    description_kz = models.TextField(blank=True, verbose_name='Tavsif (KZ)')
    description_en = models.TextField(blank=True, verbose_name='Tavsif (EN)')
    description_tr = models.TextField(blank=True, verbose_name='Tavsif (TR)')
    description_ar = models.TextField(blank=True, verbose_name='Tavsif (AR)')
    description_ko = models.TextField(blank=True, verbose_name='Tavsif (KO)')
    description_zh = models.TextField(blank=True, verbose_name='Tavsif (ZH)')
    price          = models.DecimalField(max_digits=8, decimal_places=2)
    image_url      = models.URLField(blank=True)
    is_available   = models.BooleanField(default=True)
    is_special     = models.BooleanField(default=False, verbose_name='Maxsus taom (aksiya)')
    special_price  = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Aksiya narxi')
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.price} so'm"

    @property
    def avg_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return round(sum(r.stars for r in ratings) / len(ratings), 1)

    @property
    def rating_count(self):
        return self.ratings.count()

    @property
    def current_price(self):
        if self.is_special and self.special_price:
            return self.special_price
        return self.price

    class Meta:
        verbose_name = 'Menyu elementi'
        verbose_name_plural = 'Menyu elementlari'


class Rating(models.Model):
    menu_item   = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='ratings')
    stars       = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment     = models.TextField(blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.menu_item.name} — {self.stars}*"

    class Meta:
        verbose_name = 'Reyting'
        verbose_name_plural = 'Reytinglar'
        ordering = ['-created_at']


class PromoCode(models.Model):
    code         = models.CharField(max_length=30, unique=True, verbose_name='Kod')
    discount_pct = models.PositiveSmallIntegerField(verbose_name='Chegirma (%)')
    is_active    = models.BooleanField(default=True, verbose_name='Faol')
    valid_until  = models.DateTimeField(null=True, blank=True, verbose_name='Amal qilish muddati')
    usage_limit  = models.PositiveIntegerField(default=0, verbose_name='Foydalanish chegarasi (0=cheksiz)')
    used_count   = models.PositiveIntegerField(default=0, verbose_name='Ishlatilgan marta')

    def is_valid(self):
        if not self.is_active:
            return False
        if self.valid_until and timezone.now() > self.valid_until:
            return False
        if self.usage_limit > 0 and self.used_count >= self.usage_limit:
            return False
        return True

    def __str__(self):
        return f"{self.code} — {self.discount_pct}%"

    class Meta:
        verbose_name = 'Promo kod'
        verbose_name_plural = 'Promo kodlar'


class RestaurantSettings(models.Model):
    open_time          = models.TimeField(default='09:00', verbose_name='Ochilish vaqti')
    close_time         = models.TimeField(default='22:00', verbose_name='Yopilish vaqti')
    is_manually_closed = models.BooleanField(default=False, verbose_name="Qo'lda yopiq")
    restaurant_lat     = models.FloatField(default=41.2995, verbose_name='Restoran lat')
    restaurant_lng     = models.FloatField(default=69.2401, verbose_name='Restoran lng')
    restaurant_address = models.CharField(max_length=300, default="Toshkent sh., Chilonzor tumani, Bunyodkor ko'chasi 12-uy")

    def is_open(self):
        if self.is_manually_closed:
            return False
        now = timezone.localtime().time()
        return self.open_time <= now <= self.close_time

    def __str__(self):
        return "Restoran sozlamalari"

    class Meta:
        verbose_name = 'Restoran sozlamasi'
        verbose_name_plural = 'Restoran sozlamalari'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   '⏳ Kutilmoqda'),
        ('confirmed', '✅ Tasdiqlandi'),
        ('preparing', '👨‍🍳 Tayyorlanmoqda'),
        ('on_way',    '🚴 Yolda'),
        ('delivered', '🎉 Yetkazildi'),
        ('cancelled', '❌ Bekor qilindi'),
    ]
    customer_name    = models.CharField(max_length=200)
    customer_phone   = models.CharField(max_length=20)
    customer_address = models.TextField()
    customer_lat     = models.FloatField(null=True, blank=True)
    customer_lng     = models.FloatField(null=True, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note             = models.TextField(blank=True)
    promo_code       = models.CharField(max_length=30, blank=True)
    discount_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    courier_lat      = models.FloatField(null=True, blank=True)
    courier_lng      = models.FloatField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Zakaz #{self.id} - {self.customer_name} ({self.get_status_display()})"

    class Meta:
        verbose_name = 'Zakaz'
        verbose_name_plural = 'Zakazlar'
        ordering = ['-created_at']


class OrderItem(models.Model):
    order     = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity  = models.PositiveIntegerField(default=1)
    price     = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity

    class Meta:
        verbose_name = 'Zakaz elementi'
        verbose_name_plural = 'Zakaz elementlari'


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('order',    '📦 Zakaz haqida'),
        ('quality',  '⭐ Sifat haqida'),
        ('delivery', '🚚 Yetkazish haqida'),
        ('other',    '💬 Boshqa'),
    ]
    name       = models.CharField(max_length=200, verbose_name='Ism')
    phone      = models.CharField(max_length=20, verbose_name='Telefon')
    email      = models.EmailField(blank=True, verbose_name='Email')
    subject    = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='other', verbose_name='Mavzu')
    message    = models.TextField(verbose_name='Xabar')
    is_read    = models.BooleanField(default=False, verbose_name="O'qildi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yuborilgan vaqt')

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"

    class Meta:
        verbose_name = 'Xabar'
        verbose_name_plural = 'Xabarlar'
        ordering = ['-created_at']


class RPSPlayer(models.Model):
    username      = models.CharField(max_length=50, unique=True, verbose_name='Ism')
    password      = models.CharField(max_length=128, default='', verbose_name='Parol')
    game_code     = models.CharField(max_length=10, unique=True, verbose_name="O'yin kodi")
    wins          = models.PositiveIntegerField(default=0, verbose_name="G'alabalar")
    losses        = models.PositiveIntegerField(default=0, verbose_name="Mag'lubiyatlar")
    draws         = models.PositiveIntegerField(default=0, verbose_name='Durranglar')
    score         = models.IntegerField(default=0, verbose_name='Ball (rating)')
    session_token = models.CharField(max_length=64, blank=True, default='', verbose_name='Session token')
    last_active   = models.DateTimeField(null=True, blank=True, verbose_name='Oxirgi faollik')
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} — {self.score} ball"

    class Meta:
        verbose_name = "RPS O'yinchi"
        verbose_name_plural = "RPS O'yinchilar"
        ordering = ['-score']


class RPSMessage(models.Model):
    """Chat xabarlari"""
    sender     = models.ForeignKey(
        RPSPlayer, on_delete=models.CASCADE,
        related_name='sent_messages', verbose_name='Yuboruvchi'
    )
    room       = models.CharField(max_length=50, default='global', verbose_name='Xona')
    text       = models.TextField(verbose_name='Xabar')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.text[:40]}"

    class Meta:
        verbose_name = 'Chat xabari'
        verbose_name_plural = 'Chat xabarlari'
        ordering = ['created_at']
