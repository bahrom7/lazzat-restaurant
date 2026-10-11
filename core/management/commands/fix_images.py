"""
python manage.py fix_images
Noto'g'ri (shahar, manzara) rasmlari bor taomlarni to'g'ri ovqat rasmi bilan almashtiradi.
"""
from django.core.management.base import BaseCommand
from core.models import MenuItem

U = "?auto=format&fit=crop&w=400&q=80"

# Taom nomi : to'g'ri Unsplash photo ID
FIXES = {
    # Shahar rasmi edi — to'g'ri ovqat rasmlari
    "Qozon kabob":       "photo-1544025162-d76694265947",  # kabob
    "Mixed Grill Platter":"photo-1555939594-58d7cb561ad1", # grill platter
    "Shashlik mol":       "photo-1555939594-58d7cb561ad1", # grill
    "Shashlik qo'y":      "photo-1555939594-58d7cb561ad1", # grill
    "Tuna Salad":         "photo-1490645935967-10de6ba17061", # salad
    "Sirloin Steak":      "photo-1558030006-450675393462",  # steak

    # Bir xil rasm edi — har biriga o'z rasmi
    "Dimlama":            "photo-1555939594-58d7cb561ad1", # qozon ovqat
    "Halva":              "photo-1559181567-c3190ca9d222", # shirinlik
    "Mastava":            "photo-1547592180-85f173990554", # sho'rva

    # Chicken Steak noto'g'ri edi
    "Chicken Steak":      "photo-1598103442097-8b74394b95c2", # chicken

    # Lagmon va Ramen va Udon bir xil edi
    "Lagmon":             "photo-1569050467447-ce54b3bbc37d", # noodle
    "Ramen":              "photo-1569050467447-ce54b3bbc37d", # ramen
    "Udon Noodle Soup":   "photo-1569050467447-ce54b3bbc37d", # udon

    # Shawarma ikkalasi bir xil - OK, lekin Chicken Shawarma ham bir xil
    "Chicken Shawarma":   "photo-1561651823-34feb02250e4", # shawarma

    # Kompot va Limonad bir xil edi
    "Kompot":             "photo-1556679343-c7306c1976bc", # kompot/drink

    # Manty to'g'ri emas
    "Manty":              "photo-1496116218417-1a781b1c416c", # dumpling

    # Kaymokli Non va Jo'xori non bir xil
    "Kaymokli Non":       "photo-1549931319-a545dcf3bc7c", # non/bread

    # Kabob va Tandir kabob bir xil
    "Tandir kabob":       "photo-1529059997568-3d847b1154f0", # kabob

    # Olivier salat va Avocado salad bir xil edi
    "Olivier Salati":     "photo-1604152135912-04a022e23696", # salat

    # Prawn noto'g'ri
    "Prawn Stir Fry":     "photo-1563379926898-05f4575a45d8", # shrimp
}


class Command(BaseCommand):
    help = "Noto'g'ri rasmlarni to'g'rilaydi"

    def handle(self, *args, **kwargs):
        updated = 0
        for name, photo_id in FIXES.items():
            url = f"https://images.unsplash.com/{photo_id}{U}"
            count = MenuItem.objects.filter(name=name).update(image_url=url)
            if count:
                self.stdout.write(self.style.SUCCESS(f"  ✅ {name}"))
                updated += count
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Topilmadi: {name}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Jami {updated} ta taom rasmi yangilandi"))
