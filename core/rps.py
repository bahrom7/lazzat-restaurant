"""
Rock Paper Scissors - in-memory game state
Ishonchli versiya: har o'yinchi o'z natijasini
alohida ko'radi, shundan keyingina keyingi raundga o'tiladi.
"""
import time

ROOMS = {}
ROOM_TTL = 300


def clean_old_rooms():
    now = time.time()
    for r in [k for k, v in ROOMS.items() if now - v['created'] > ROOM_TTL]:
        del ROOMS[r]


def get_room_id(c1, c2):
    return '_'.join(sorted([c1, c2]))


def join_room(my_code, my_name, friend_code):
    clean_old_rooms()
    room_id = get_room_id(my_code, friend_code)

    if room_id not in ROOMS:
        ROOMS[room_id] = {
            'players': {},   # code -> {time, name}
            'rounds':  [],   # [ {c1_code: choice, c2_code: choice, seen: set()} ]
            'created': time.time(),
        }

    room = ROOMS[room_id]
    room['players'][my_code] = {'time': time.time(), 'name': my_name}

    other = [c for c in room['players'] if c != my_code]
    opp_name = room['players'][other[0]]['name'] if other else ''

    return {
        'status':   'ok' if other else 'waiting',
        'room_id':  room_id,
        'opp_name': opp_name,
    }


def save_choice(room_id, code, choice):
    """O'yinchi tanlovini saqlaydi. Har raundda faqat bir marta."""
    if room_id not in ROOMS:
        return False

    room = ROOMS[room_id]
    room['players'][code]['time'] = time.time()

    rounds = room['rounds']

    # Joriy raundda bu o'yinchi allaqachon tanlagan bo'lsa — ignore
    if rounds and code not in rounds[-1].get('seen', set()) and code in rounds[-1]:
        # Natijani hali ko'rmagan, eski tanlov bor — yangi tanlov qilinmasin
        return False

    # Yangi tanlov — raundga qo'shish
    if not rounds or len([k for k in rounds[-1] if k not in ('seen',)]) >= 2:
        # Yangi raund boshlaymiz
        rounds.append({'seen': set()})

    rounds[-1][code] = choice
    return True


def get_state(room_id, my_code):
    """O'yinchi holatini qaytaradi."""
    if room_id not in ROOMS:
        return {'status': 'error', 'disconnected': True}

    room = ROOMS[room_id]

    if my_code in room['players']:
        room['players'][my_code]['time'] = time.time()

    other_codes = [c for c in room['players'] if c != my_code]
    if not other_codes:
        return {'status': 'waiting', 'disconnected': False}

    opp_code = other_codes[0]
    opp_info = room['players'].get(opp_code, {})
    opp_name = opp_info.get('name', opp_code[:6])
    disconnected = (time.time() - opp_info.get('time', 0)) > 15

    rounds = room['rounds']
    if not rounds:
        return {
            'status': 'ok', 'opp_choice': None,
            'opp_name': opp_name, 'disconnected': disconnected,
            'round_num': 0,
        }

    current = rounds[-1]
    opp_choice = current.get(opp_code)
    my_choice  = current.get(my_code)

    # Agar ikkalasi ham tanlagan bo'lsa va men ko'rmagan bo'lsam
    if opp_choice and my_choice and my_code not in current['seen']:
        current['seen'].add(my_code)

    return {
        'status':       'ok',
        'opp_choice':   opp_choice,
        'opp_name':     opp_name,
        'disconnected': disconnected,
        'round_num':    len(rounds),
    }
