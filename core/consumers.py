import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer

# Xonalar: { room_id: { players: [channel1, channel2], choices: {} } }
rooms = {}


class RPSConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.group   = f'rps_{self.room_id}'

        # Xona yaratish yoki ulash
        if self.room_id not in rooms:
            rooms[self.room_id] = {'players': [], 'choices': {}, 'scores': {}}

        room = rooms[self.room_id]

        if len(room['players']) >= 2:
            await self.accept()
            await self.send(json.dumps({'type': 'error', 'msg': 'Room is full!'}))
            await self.close()
            return

        room['players'].append(self.channel_name)
        self.player_num = len(room['players'])  # 1 yoki 2
        room['scores'][self.channel_name] = 0

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        await self.send(json.dumps({
            'type':       'joined',
            'player_num': self.player_num,
            'room_id':    self.room_id,
        }))

        # Ikkinchi o'yinchi ulandi — o'yin boshlana oladi
        if len(room['players']) == 2:
            await self.channel_layer.group_send(self.group, {
                'type': 'game_start',
            })

    async def disconnect(self, code):
        room = rooms.get(self.room_id)
        if room and self.channel_name in room['players']:
            room['players'].remove(self.channel_name)
            room['choices'].pop(self.channel_name, None)
            await self.channel_layer.group_send(self.group, {
                'type': 'player_left',
            })
        await self.channel_layer.group_discard(self.group, self.channel_name)
        if self.room_id in rooms and not rooms[self.room_id]['players']:
            del rooms[self.room_id]

    async def receive(self, text_data):
        data = json.loads(text_data)
        room = rooms.get(self.room_id)
        if not room:
            return

        if data['type'] == 'choice':
            room['choices'][self.channel_name] = data['choice']

            # Ikki o'yinchi ham tanladi
            if len(room['choices']) == 2:
                players  = room['players']
                ch1, ch2 = players[0], players[1]
                c1 = room['choices'].get(ch1)
                c2 = room['choices'].get(ch2)

                res1 = get_result(c1, c2)
                res2 = get_result(c2, c1)

                if res1 == 'win':
                    room['scores'][ch1] = room['scores'].get(ch1, 0) + 1
                elif res2 == 'win':
                    room['scores'][ch2] = room['scores'].get(ch2, 0) + 1

                await self.channel_layer.group_send(self.group, {
                    'type':    'round_result',
                    'ch1':     ch1,
                    'ch2':     ch2,
                    'choice1': c1,
                    'choice2': c2,
                    'result1': res1,
                    'result2': res2,
                    'score1':  room['scores'].get(ch1, 0),
                    'score2':  room['scores'].get(ch2, 0),
                })
                room['choices'] = {}

    # ── Channel layer event handlers ──────────────────────────

    async def game_start(self, event):
        await self.send(json.dumps({'type': 'game_start'}))

    async def player_left(self, event):
        await self.send(json.dumps({'type': 'player_left'}))

    async def round_result(self, event):
        # Har o'yinchiga o'z natijasini yuboramiz
        is_p1    = self.channel_name == event['ch1']
        my_ch    = event['ch1']    if is_p1 else event['ch2']
        opp_ch   = event['ch2']    if is_p1 else event['ch1']
        my_c     = event['choice1'] if is_p1 else event['choice2']
        opp_c    = event['choice2'] if is_p1 else event['choice1']
        my_res   = event['result1'] if is_p1 else event['result2']
        my_score = event['score1']  if is_p1 else event['score2']
        opp_score= event['score2']  if is_p1 else event['score1']

        await self.send(json.dumps({
            'type':      'round_result',
            'my_choice': my_c,
            'opp_choice':opp_c,
            'result':    my_res,
            'my_score':  my_score,
            'opp_score': opp_score,
        }))


def get_result(me, opp):
    if me == opp:
        return 'draw'
    wins = {'rock': 'scissors', 'scissors': 'paper', 'paper': 'rock'}
    return 'win' if wins[me] == opp else 'lose'
