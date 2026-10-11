"""
python manage.py remove_broken_images
Rasmi yuklanmaydigan taomlarni o'chiradi.
"""
import urllib.request
import concurrent.futures
from django.core.management.base import BaseCommand
from core.models import MenuItem


def check_url(item):
    """URL ishlaydimi tekshiradi. (id, name, ok) qaytaradi."""
    try:
        req = urllib.request.Request(
            item.image_url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        r = urllib.request.urlopen(req, timeout=6)
        ct = r.headers.get('Content-Type', '')
        ok = 'image' in ct
    except Exception:
        ok = False
    return item.id, item.name, ok


class Command(BaseCommand):
    help = "Rasmi yuklanmaydigan taomlarni topib o'chiradi"

    def handle(self, *args, **kwargs):
        items = list(MenuItem.objects.exclude(image_url=''))
        self.stdout.write(f"🔍 {len(items)} ta taom tekshirilmoqda...")

        broken_ids = []
        broken_names = []

        # 20 ta parallel thread bilan tezlashtirish
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            futures = {ex.submit(check_url, item): item for item in items}
            done = 0
            for future in concurrent.futures.as_completed(futures):
                item_id, name, ok = future.result()
                done += 1
                if not ok:
                    broken_ids.append(item_id)
                    broken_names.append(name)
                    self.stdout.write(self.style.WARNING(f"  ❌ {name}"))
                else:
                    self.stdout.write(f"  ✅ {name}")

        if broken_ids:
            MenuItem.objects.filter(id__in=broken_ids).delete()
            self.stdout.write(self.style.SUCCESS(
                f"\n🗑️  {len(broken_ids)} ta taom o'chirildi: {', '.join(broken_names)}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Hamma rasm ishlayapti! Hech narsa o'chirilmadi."))

        self.stdout.write(f"📦 Qolgan taomlar: {MenuItem.objects.count()} ta")
