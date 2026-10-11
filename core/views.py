import json
import random
import string
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from .models import (
    Category, MenuItem, Order, OrderItem,
    ContactMessage, Rating, PromoCode, RestaurantSettings
)


# ─── Yordamchi ────────────────────────────────────────────────────────────────

def get_settings():
    obj, _ = RestaurantSettings.objects.get_or_create(id=1)
    return obj


# ─── Frontend sahifalar ───────────────────────────────────────────────────────

def home_view(request):
    categories     = Category.objects.prefetch_related('items').all()
    featured_items = MenuItem.objects.filter(is_available=True).select_related('category')[:8]
    specials       = MenuItem.objects.filter(is_available=True, is_special=True).select_related('category')
    rs             = get_settings()
    return render(request, 'home.html', {
        'categories':     categories,
        'featured_items': featured_items,
        'specials':       specials,
        'is_open':        rs.is_open(),
        'open_time':      rs.open_time.strftime('%H:%M'),
        'close_time':     rs.close_time.strftime('%H:%M'),
    })


def menu_view(request):
    categories   = Category.objects.all()
    all_items    = MenuItem.objects.filter(is_available=True).select_related('category').order_by('category')
    selected_cat = request.GET.get('cat', '')
    rs           = get_settings()
    return render(request, 'menu.html', {
        'categories':   categories,
        'all_items':    all_items,
        'selected_cat': selected_cat,
        'total_items':  all_items.count(),
        'is_open':      rs.is_open(),
    })


def about_view(request):
    return render(request, 'about.html')


def contact_view(request):
    sent = False
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        phone   = request.POST.get('phone', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', 'other')
        message = request.POST.get('message', '').strip()
        if name and phone and message:
            ContactMessage.objects.create(
                name=name, phone=phone, email=email,
                subject=subject, message=message,
            )
            sent = True
    return render(request, 'contact.html', {'sent': sent})


def order_success_view(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item'), id=order_id
    )
    rs = get_settings()
    return render(request, 'order_success.html', {
        'order': order,
        'restaurant_lat': rs.restaurant_lat,
        'restaurant_lng': rs.restaurant_lng,
    })


def order_tracking_view(request, order_id):
    """Zakaz tracking sahifasi — Google Maps bilan"""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__menu_item'), id=order_id
    )
    rs = get_settings()
    return render(request, 'order_tracking.html', {
        'order':          order,
        'restaurant_lat': rs.restaurant_lat,
        'restaurant_lng': rs.restaurant_lng,
    })


# ─── Login / OTP ─────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'login.html')


def send_otp_view(request):
    """POST: email yuboriladi, OTP session ga saqlanadi"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST kerak'}, status=405)

    data  = json.loads(request.body)
    email = data.get('email', '').strip().lower()

    if not email or '@' not in email:
        return JsonResponse({'status': 'error', 'message': "To'g'ri email kiriting"}, status=400)

    # 6 xonali OTP
    otp = ''.join(random.choices(string.digits, k=6))
    request.session['otp_code']    = otp
    request.session['otp_email']   = email
    request.session['otp_expires'] = (timezone.now() + timedelta(minutes=5)).isoformat()

    try:
        send_mail(
            subject='🍽️ Lazzat Restaurant — Kirish kodi',
            message=(
                f"Assalomu alaykum!\n\n"
                f"Sizning kirish kodingiz:\n\n"
                f"  ➡️  {otp}\n\n"
                f"Bu kod 5 daqiqa davomida amal qiladi.\n\n"
                f"Agar siz bu so'rovni yubormagan bo'lsangiz, xabarni e'tiborsiz qoldiring.\n\n"
                f"— Lazzat Restaurant"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return JsonResponse({'status': 'ok', 'message': f"{email} ga kod yuborildi"})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Email yuborishda xato: {str(e)}'}, status=500)


def verify_otp_view(request):
    """POST: OTP tekshiriladi, login qilinadi"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    data  = json.loads(request.body)
    email = data.get('email', '').strip().lower()
    code  = data.get('code', '').strip()

    sess_otp     = request.session.get('otp_code')
    sess_email   = request.session.get('otp_email')
    sess_expires = request.session.get('otp_expires')

    if not sess_otp or not sess_email:
        return JsonResponse({'status': 'error', 'message': 'Avval kod so\'rash kerak'}, status=400)

    if timezone.now().isoformat() > sess_expires:
        return JsonResponse({'status': 'error', 'message': 'Kod muddati tugagan, qayta so\'rang'}, status=400)

    if email != sess_email or code != sess_otp:
        return JsonResponse({'status': 'error', 'message': 'Noto\'g\'ri kod'}, status=400)

    # Foydalanuvchi topiladi yoki yaratiladi
    user, _ = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': email.split('@')[0]}
    )
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    # Session tozalash
    for k in ('otp_code', 'otp_email', 'otp_expires'):
        request.session.pop(k, None)

    return JsonResponse({'status': 'ok', 'redirect': '/'})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'register.html')


@csrf_exempt
def api_register(request):
    """POST /auth/register/ — yangi akkaunt yaratish"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        data       = json.loads(request.body)
        first_name = data.get('first_name', '').strip()
        email      = data.get('email', '').strip().lower()
        password   = data.get('password', '').strip()

        if not first_name or not email or not password:
            return JsonResponse({'status': 'error', 'message': 'Barcha maydonlarni to\'ldiring'}, status=400)
        if '@' not in email:
            return JsonResponse({'status': 'error', 'message': 'Email noto\'g\'ri'}, status=400)
        if len(password) < 6:
            return JsonResponse({'status': 'error', 'message': 'Parol kamida 6 ta belgi bo\'lishi kerak'}, status=400)
        if User.objects.filter(username=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Bu email allaqachon ro\'yxatdan o\'tgan'}, status=400)

        user = User.objects.create_user(
            username=email, email=email,
            password=password, first_name=first_name
        )
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return JsonResponse({'status': 'ok', 'redirect': '/'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_login_password(request):
    """POST /auth/login/ — email + parol bilan kirish"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        from django.contrib.auth import authenticate
        data     = json.loads(request.body)
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return JsonResponse({'status': 'ok', 'redirect': '/'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Email yoki parol noto\'g\'ri'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



def logout_view(request):
    logout(request)
    return redirect('home')

# ─── API ─────────────────────────────────────────────────────────────────────

def api_menu(request):
    """GET /api/menu/"""
    categories = Category.objects.prefetch_related('items').all()
    data = []
    for cat in categories:
        items = []
        for item in cat.items.filter(is_available=True):
            items.append({
                'id':             item.id,
                'name':           item.name,
                'name_ru':        item.name_ru,
                'name_kz':        item.name_kz,
                'description':    item.description,
                'description_ru': item.description_ru,
                'description_kz': item.description_kz,
                'price':          float(item.price),
                'current_price':  float(item.current_price),
                'is_special':     item.is_special,
                'special_price':  float(item.special_price) if item.special_price else None,
                'image_url':      item.image_url,
                'avg_rating':     item.avg_rating,
                'rating_count':   item.rating_count,
            })
        data.append({'id': cat.id, 'name': cat.name, 'icon': cat.icon, 'items': items})
    return JsonResponse({'status': 'ok', 'categories': data})


def api_restaurant_status(request):
    """GET /api/status/ — restoran ochiq/yopiqmi"""
    rs = get_settings()
    return JsonResponse({
        'is_open':    rs.is_open(),
        'open_time':  rs.open_time.strftime('%H:%M'),
        'close_time': rs.close_time.strftime('%H:%M'),
    })


@csrf_exempt
def api_check_promo(request):
    """POST /api/promo/ — promo kod tekshirish"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    data = json.loads(request.body)
    code = data.get('code', '').strip().upper()
    try:
        promo = PromoCode.objects.get(code=code)
        if promo.is_valid():
            return JsonResponse({
                'status':       'ok',
                'discount_pct': promo.discount_pct,
                'message':      f"✅ {promo.discount_pct}% chegirma qo'llandi!"
            })
        else:
            return JsonResponse({'status': 'error', 'message': '❌ Promo kod muddati tugagan yoki noto\'g\'ri'})
    except PromoCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '❌ Bunday promo kod mavjud emas'})


@csrf_exempt
@require_http_methods(['POST'])
def api_create_order(request):
    """POST /api/order/"""
    try:
        body       = json.loads(request.body)
        name       = body.get('customer_name', '').strip()
        phone      = body.get('customer_phone', '').strip()
        address    = body.get('customer_address', '').strip()
        note       = body.get('note', '').strip()
        items      = body.get('items', [])
        promo_code = body.get('promo_code', '').strip().upper()
        cust_lat   = body.get('customer_lat')
        cust_lng   = body.get('customer_lng')

        if not name or not phone or not address:
            return JsonResponse({'status': 'error', 'message': 'Ism, telefon va manzil majburiy'}, status=400)
        if not items:
            return JsonResponse({'status': 'error', 'message': 'Kamida bitta ovqat tanlang'}, status=400)

        DELIVERY_FEE = 5000

        order = Order.objects.create(
            customer_name=name, customer_phone=phone,
            customer_address=address, note=note,
            customer_lat=cust_lat, customer_lng=cust_lng,
            promo_code=promo_code,
        )

        total = 0
        for item_data in items:
            menu_item = MenuItem.objects.get(id=item_data['menu_item_id'], is_available=True)
            qty = max(1, int(item_data.get('quantity', 1)))
            price = menu_item.current_price
            OrderItem.objects.create(order=order, menu_item=menu_item, quantity=qty, price=price)
            total += price * qty

        # Promo kod
        discount = 0
        if promo_code:
            try:
                promo = PromoCode.objects.get(code=promo_code)
                if promo.is_valid():
                    discount = int(total * promo.discount_pct / 100)
                    promo.used_count += 1
                    promo.save()
            except PromoCode.DoesNotExist:
                pass

        total = total - discount + DELIVERY_FEE
        order.total_price     = total
        order.discount_amount = discount
        order.save()

        return JsonResponse({
            'status':       'ok',
            'order_id':     order.id,
            'total_price':  float(total),
            'discount':     float(discount),
            'delivery_fee': DELIVERY_FEE,
        })

    except MenuItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Tanlangan ovqat mavjud emas'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def api_order_status(request, order_id):
    """GET /api/order/<id>/ — zakaz holati + kuryer koordinatasi"""
    try:
        order = Order.objects.prefetch_related('items__menu_item').get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Zakaz topilmadi'}, status=404)

    rs = get_settings()
    return JsonResponse({
        'status': 'ok',
        'order': {
            'id':              order.id,
            'status':          order.status,
            'status_display':  order.get_status_display(),
            'customer_name':   order.customer_name,
            'total_price':     float(order.total_price),
            'created_at':      order.created_at.strftime('%Y-%m-%d %H:%M'),
            'courier_lat':     order.courier_lat,
            'courier_lng':     order.courier_lng,
            'customer_lat':    order.customer_lat,
            'customer_lng':    order.customer_lng,
            'restaurant_lat':  rs.restaurant_lat,
            'restaurant_lng':  rs.restaurant_lng,
            'items': [
                {'name': i.menu_item.name, 'qty': i.quantity, 'subtotal': float(i.subtotal)}
                for i in order.items.all()
            ],
        }
    })


@csrf_exempt
def api_rate_item(request, item_id):
    """POST /api/rate/<id>/ — ovqatga reyting berish"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        data    = json.loads(request.body)
        stars   = int(data.get('stars', 0))
        comment = data.get('comment', '').strip()
        if not 1 <= stars <= 5:
            return JsonResponse({'status': 'error', 'message': '1-5 orasida yulduz bering'}, status=400)
        item = MenuItem.objects.get(id=item_id)
        session_key = request.session.session_key or 'anon'
        # Bir sessiyada bir marta
        Rating.objects.update_or_create(
            menu_item=item, session_key=session_key,
            defaults={'stars': stars, 'comment': comment}
        )
        return JsonResponse({
            'status':      'ok',
            'avg_rating':  item.avg_rating,
            'rating_count': item.rating_count,
        })
    except MenuItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Taom topilmadi'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def rps_game_view(request):
    return render(request, 'rps_game.html')


def rps_check(request):
    """GET: game_code bilan akkauntni tekshirish"""
    from .models import RPSPlayer
    code = request.GET.get('code', '')
    try:
        p = RPSPlayer.objects.get(game_code=code)
        return JsonResponse({'status': 'ok', 'username': p.username, 'score': p.score})
    except RPSPlayer.DoesNotExist:
        return JsonResponse({'status': 'not_found'})


@csrf_exempt
def rps_send_otp(request):
    return JsonResponse({'status': 'error', 'message': 'Email tizimi vaqtincha o\'chirilgan'})


@csrf_exempt
def rps_verify_otp(request):
    return JsonResponse({'status': 'error', 'message': 'Email tizimi vaqtincha o\'chirilgan'})


@csrf_exempt
def rps_register(request):
    """POST: Yangi akkaunt yaratish — ism + parol"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        import hashlib, random, string
        from .models import RPSPlayer

        data     = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or len(username) < 2:
            return JsonResponse({'status': 'error', 'message': "Ism kamida 2 ta belgi bo'lsin"})
        if not password or len(password) < 6:
            return JsonResponse({'status': 'error', 'message': "Parol kamida 6 ta belgi bo'lsin"})
        if RPSPlayer.objects.filter(username__iexact=username).exists():
            return JsonResponse({'status': 'error', 'message': "Bu ism allaqachon band, boshqa ism tanlang"})

        # Parolni hash qilamiz
        pw_hash = hashlib.sha256(password.encode()).hexdigest()

        def gen_code():
            while True:
                c = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not RPSPlayer.objects.filter(game_code=c).exists():
                    return c

        player = RPSPlayer.objects.create(
            username=username,
            password=pw_hash,
            game_code=gen_code(),
        )
        import secrets
        token = secrets.token_hex(16)
        player.session_token = token
        player.last_active   = timezone.now()
        player.save()

        return JsonResponse({
            'status':    'ok',
            'username':  player.username,
            'game_code': player.game_code,
            'token':     token,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def rps_login(request):
    """POST: Kirish — ism + parol"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        import hashlib, secrets
        from .models import RPSPlayer

        data     = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        my_token = data.get('token', '').strip()  # bu qurilmaning joriy tokeni

        if not username or not password:
            return JsonResponse({'status': 'error', 'message': "Ism va parolni kiriting"})

        pw_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            player = RPSPlayer.objects.get(username__iexact=username, password=pw_hash)
        except RPSPlayer.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': "Ism yoki parol noto'g'ri"})

        # Boshqa qurilmadan kirgan bo'lsa tekshirish:
        if player.session_token and player.session_token != my_token and my_token != 'FORCE':
            if player.last_active:
                diff = (timezone.now() - player.last_active).total_seconds()
                if diff < 300:
                    mins = int((300 - diff) / 60)
                    secs = int((300 - diff) % 60)
                    return JsonResponse({
                        'status':  'busy',
                        'message': f"⚠️ Bu akkaunt boshqa qurilmada faol! {mins}:{secs:02d} dan keyin qayta urining yoki avvalgi qurilmadan chiqing."
                    })

        # Token yangilash (eski tokenni o'chirib yangi berish)
        new_token = secrets.token_hex(16)
        player.session_token = new_token
        player.last_active   = timezone.now()
        player.save()

        return JsonResponse({
            'status':    'ok',
            'username':  player.username,
            'game_code': player.game_code,
            'token':     new_token,
            'wins':      player.wins,
            'losses':    player.losses,
            'draws':     player.draws,
            'score':     player.score,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def rps_update_stats(request):
    """POST/OPTIONS: O'yin natijasini saqlash"""
    if request.method == 'OPTIONS':
        from django.http import HttpResponse
        r = HttpResponse()
        r['Access-Control-Allow-Origin']  = '*'
        r['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        r['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if request.method != 'POST':
        return JsonResponse({'status': 'ok'})
    try:
        from .models import RPSPlayer
        data      = json.loads(request.body)
        game_code = data.get('game_code', '')
        result    = data.get('result', '')

        player = RPSPlayer.objects.get(game_code=game_code)
        if result == 'win':
            player.wins  += 1
            player.score += 10
        elif result == 'lose':
            player.losses += 1
            player.score  = max(0, player.score - 3)
        elif result == 'draw':
            player.draws += 1
            player.score += 2
        player.save()
        return JsonResponse({'status': 'ok', 'score': player.score})
    except RPSPlayer.DoesNotExist:
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def rps_logout(request):
    """POST: Chiqish — session token o'chirish"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        from .models import RPSPlayer
        data  = json.loads(request.body)
        code  = data.get('game_code', '')
        token = data.get('token', '')
        RPSPlayer.objects.filter(game_code=code, session_token=token).update(
            session_token='', last_active=None
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def rps_heartbeat(request):
    """POST: Har 60 soniyada faollikni yangilash"""
    if request.method != 'POST':
        return JsonResponse({'status': 'ok'})
    try:
        from .models import RPSPlayer
        data  = json.loads(request.body)
        code  = data.get('game_code', '')
        token = data.get('token', '')
        RPSPlayer.objects.filter(game_code=code, session_token=token).update(
            last_active=timezone.now()
        )
        return JsonResponse({'status': 'ok'})
    except:
        return JsonResponse({'status': 'ok'})
    """POST/OPTIONS: O'yin natijasini saqlash"""
    if request.method == 'OPTIONS':
        from django.http import HttpResponse
        r = HttpResponse()
        r['Access-Control-Allow-Origin']  = '*'
        r['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        r['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    if request.method != 'POST':
        return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'error'}, status=405)
    try:
        from .models import RPSPlayer
        data      = json.loads(request.body)
        game_code = data.get('game_code', '')
        result    = data.get('result', '')  # 'win' | 'lose' | 'draw'

        player = RPSPlayer.objects.get(game_code=game_code)
        if result == 'win':
            player.wins  += 1
            player.score += 10
        elif result == 'lose':
            player.losses += 1
            player.score  = max(0, player.score - 3)
        elif result == 'draw':
            player.draws += 1
            player.score += 2
        player.save()
        return JsonResponse({'status': 'ok', 'score': player.score})
    except RPSPlayer.DoesNotExist:
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def rps_rating(request):
    """GET: Rating ro'yxati"""
    from .models import RPSPlayer
    players = RPSPlayer.objects.order_by('-score')[:50]
    data = []
    for i, p in enumerate(players, 1):
        total = p.wins + p.losses + p.draws
        winrate = round(p.wins / total * 100) if total > 0 else 0
        data.append({
            'rank':     i,
            'username': p.username,
            'score':    p.score,
            'wins':     p.wins,
            'losses':   p.losses,
            'draws':    p.draws,
            'winrate':  winrate,
            'total':    total,
        })
    return JsonResponse({'status': 'ok', 'players': data})


@csrf_exempt
def rps_chat_send(request):
    """POST: Xabar yuborish"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        from .models import RPSPlayer, RPSMessage
        data  = json.loads(request.body)
        code  = data.get('game_code', '')
        token = data.get('token', '')
        text  = data.get('text', '').strip()
        room  = data.get('room', 'global')

        if not text or len(text) > 300:
            return JsonResponse({'status': 'error', 'message': 'Xabar bo\'sh yoki juda uzun'})

        player = RPSPlayer.objects.get(game_code=code, session_token=token)
        msg = RPSMessage.objects.create(sender=player, room=room, text=text)
        return JsonResponse({
            'status': 'ok',
            'id': msg.id,
            'username': player.username,
            'text': msg.text,
            'time': msg.created_at.strftime('%H:%M'),
        })
    except RPSPlayer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sessiya tugagan, qayta kiring'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def rps_chat_get(request):
    """GET: Xabarlarni olish"""
    from .models import RPSMessage
    room     = request.GET.get('room', 'global')
    after_id = int(request.GET.get('after', 0))

    msgs = RPSMessage.objects.filter(room=room, id__gt=after_id).select_related('sender')[:50]
    data = [{
        'id':       m.id,
        'username': m.sender.username,
        'text':     m.text,
        'time':     m.created_at.strftime('%H:%M'),
    } for m in msgs]
    return JsonResponse({'status': 'ok', 'messages': data})


@csrf_exempt
def rps_join(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    from .rps import join_room
    data = json.loads(request.body)
    result = join_room(
        data.get('my_code', ''),
        data.get('my_name', 'Player'),
        data.get('friend_code', '')
    )
    return JsonResponse(result)


@csrf_exempt
def rps_choice(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    from .rps import save_choice
    data = json.loads(request.body)
    save_choice(data.get('room', ''), data.get('code', ''), data.get('choice', ''))
    return JsonResponse({'status': 'ok'})


def rps_state(request):
    from .rps import get_state
    room_id = request.GET.get('room', '')
    code    = request.GET.get('code', '')
    return JsonResponse(get_state(room_id, code))


def health_check(request):
    return JsonResponse({'status': 'ok'})
