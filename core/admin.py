from django.contrib import admin
from .models import (
    Category, MenuItem, Order, OrderItem,
    ContactMessage, Rating, PromoCode, RestaurantSettings
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category', 'price', 'special_price', 'is_special', 'is_available', 'avg_rating')
    list_filter   = ('category', 'is_available', 'is_special')
    list_editable = ('price', 'special_price', 'is_special', 'is_available')
    search_fields = ('name',)

    def avg_rating(self, obj):
        r = obj.avg_rating
        return f"{r} ⭐ ({obj.rating_count})" if r else "—"
    avg_rating.short_description = 'Reyting'


class OrderItemInline(admin.TabularInline):
    model     = OrderItem
    extra     = 0
    readonly_fields = ('subtotal',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'customer_name', 'customer_phone', 'status', 'total_price', 'promo_code', 'created_at')
    list_filter   = ('status',)
    list_editable = ('status',)
    search_fields = ('customer_name', 'customer_phone')
    readonly_fields = ('created_at', 'total_price', 'discount_amount')
    inlines       = [OrderItemInline]
    # Kuryer joylashuvini admin paneldan yangilash
    fieldsets = (
        ('Mijoz', {'fields': ('customer_name', 'customer_phone', 'customer_address', 'note')}),
        ('Zakaz', {'fields': ('status', 'total_price', 'promo_code', 'discount_amount', 'created_at')}),
        ('📍 Joylashuv', {'fields': ('customer_lat', 'customer_lng', 'courier_lat', 'courier_lng')}),
    )


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'stars', 'comment', 'created_at')
    list_filter  = ('stars',)
    readonly_fields = ('created_at',)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display  = ('code', 'discount_pct', 'is_active', 'valid_until', 'usage_limit', 'used_count')
    list_editable = ('is_active',)


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    list_display = ('open_time', 'close_time', 'is_manually_closed', 'is_open_now')

    def is_open_now(self, obj):
        return '🟢 Ochiq' if obj.is_open() else '🔴 Yopiq'
    is_open_now.short_description = 'Hozir'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ('name', 'phone', 'get_subject', 'short_msg', 'is_read', 'created_at')
    list_filter   = ('subject', 'is_read')
    list_editable = ('is_read',)
    search_fields = ('name', 'phone', 'message')
    readonly_fields = ('name', 'phone', 'email', 'subject', 'message', 'created_at')

    def get_subject(self, obj):
        return obj.get_subject_display()
    get_subject.short_description = 'Mavzu'

    def short_msg(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
    short_msg.short_description = 'Xabar'
