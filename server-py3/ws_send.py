
import json
import asyncio
from sanic.exceptions import WebsocketClosed
from uaparser import UAParser

import os
import hashlib

from utils import hash_murmur3

device_hash_seed = int(hashlib.sha256(os.urandom(32)).hexdigest(), 16) % 2**32

async def ws_send(ws, msg, ws_list):
    try:
        await ws.send(msg)
    except (ConnectionResetError, WebsocketClosed):
        # print('--ws rm2:', ws_list, ws, ws.remote)
        # ws_list.remove(ws)
        ws_list.discard(ws)
        # print('--ws ==:', ws_list, ws)
        # print( BG.b, len(ws_list), FG.z+FG.r+' - conn close', f'{ws.remote:21}', ws.ua, FG.z)
        await ws.close()


def broadcast_ws_message(ws_list, message, room):
    # room = room or ''
    # print('---broadcast room:', room, type(room))
    # print('--- pub ws send ', datetime.now().strftime('%F %T.%f'))
    # for ws in ws_list:
        # print(' --ws room:', ws.room, type(ws.room))
    tasks = [ws_send(ws, message, ws_list) for ws in ws_list if ws.room == room]
    asyncio.gather(*tasks)
    # print('--- pub ws after', datetime.now().strftime('%F %T.%f'))


## send history to NEW ws
async def ws_send_history(ws, room, message_queue):
    # print('--- send hist for client:', room, type(room))
    for message in message_queue:
        msg_room = message.get('data', {}).get('room', '') or ''
        # print('-- msg room:', msg_room, type(msg_room))
        if msg_room == room:  ## only to ROOM
            msg = json.dumps(message)
            await ws.send(msg)

## send devices to ALL ws
async def ws_send_devices(request, ws, ws_list, device_connected):
    room = request.args.get('room', '')
    user_agent = request.headers.get('user-agent')
    ip = request.ip
    port = request.port
    # print('--send device:', ip, port, ws.remote)
    device_id = hash_murmur3(f"{ip}:{port} {user_agent}".encode(), seed=device_hash_seed)
    device_parsed = UAParser(user_agent)
    # print('--device_id:', device_id)
    # print('--ua_parsed:', device_parsed)

    device_meta = {
        'type': (device_parsed.device['type'] or '').strip(),
        'device': f"{device_parsed.device['vendor'] or ''} {device_parsed.device['model'] or ''}".strip(),
        'os': f"{device_parsed.os['name'] or ''} {device_parsed.os['version'] or ''}".strip(),
        'browser': f"{device_parsed.browser['name'] or ''} {device_parsed.browser['version'] or ''}".strip(),
    }

    ## notify self (old event)
    for id, meta in device_connected.items():
        await ws.send(json.dumps({
            'event': 'connect',
            'data': {
                'id': id,
                **meta,
            },
        }))

    device_connected[device_id] = device_meta

    ## notify ALL (this event) or ROOM
    broadcast_ws_message(ws_list, json.dumps({
        'event': 'connect',
        'data': {
            'id': device_id,
            **device_meta,
        },
    }), room)

    return device_id, room
