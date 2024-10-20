
import os
import json
import asyncio
import threading

# from sanic.request import File
from sanic.response import json as sanic_json
# from sanic.websocket import WebSocketProtocol
from sanic import Sanic, response
from sanic import Request, Websocket
from sanic.exceptions import WebsocketClosed

from datetime import datetime
from color import FG,BG

import hashlib

from uuid import uuid4
from uaparser import UAParser
from pathlib import Path


# Config
config = {
    'server': {
        # 'prefix': '/api',
        'prefix': '',
        # 'auth': False,
        'auth': 'hello',
    },
    'text': {
        'limit': 1048576,  # 1MB
    }
}
version = 'py3-1.1.0'

app = Sanic(__name__)
from sanic import Blueprint
bp = Blueprint('bp')

history_path = Path('history.json')
storage_folder = Path('./uploads')

# ----------------------- config

def load_config(file_path='config.json'):
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} contains invalid JSON.")
        return None

config = load_config()
print('--config:', FG.y+json.dumps(config, indent=2)+FG.z)

# ----------------------- msg queue

class MsgList(list):
    def __init__(self):
        super().__init__()
        self.nextid = 0

    def append(self, item):
        super().append(item)
        # print('--hist append:', self.nextid, item)
        self.nextid += 1
        item_id = item.get('data', {}).get('id', 0)
        if self.nextid <= item_id:
            self.nextid = item_id + 1
        # print('  nextid:', self.nextid)

# app.ctx.message_queue = []
app.ctx.message_queue = MsgList()
upload_file_map = {}

device_connected = {}
device_hash_seed = int(hashlib.sha256(os.urandom(32)).hexdigest(), 16) % 2**32

# ----------------------- history

## filter-out expire items @load
def save_history():
    current_time = int(datetime.now().timestamp())
    filtered_files = [
        {
            'name': file['name'],
            'uuid': file['uuid'],
            'size': file['size'],
            'uploadTime': file['uploadTime'],
            'expireTime': file['expireTime'],
        } for file in upload_file_map.values() if file['expireTime'] > current_time
    ]
    filtered_messages = [
        message['data'] for message in app.ctx.message_queue
        if message['data']['type'] != 'file' or message['data']['expire'] > current_time
    ]
    with open(history_path, 'w') as f:
        json.dump({
            'file': filtered_files,
            'receive': filtered_messages
        }, f)

## filter-out expire items @save
def load_history():
    if history_path.exists():
        with open(history_path, 'r') as f:
            history_data = json.load(f)
            current_time = int(datetime.now().timestamp())

            # Load historical files
            for file in history_data['file']:
                if Path(storage_folder / file['uuid']).exists() and file['expireTime'] > current_time:
                    upload_file_map[file['uuid']] = file

            # Load historical messages
            for msg in history_data['receive']:
                if msg['type'] == 'file' and msg['cache'] not in upload_file_map:
                    continue
                app.ctx.message_queue.append({
                    'event': 'receive',
                    'data': {
                        # 'id': len(app.ctx.message_queue),
                        'id': app.ctx.message_queue.nextid,
                        **msg
                    }
                })
                # print('++append', msg)

            # print('---- file map:', upload_file_map)
            # print('--que:', app.ctx.message_queue, id(app.ctx.message_queue))


## Periodically clean up expired files

def del_file_by_uuid(uuid):
    file_path = storage_folder / uuid
    if not file_path.exists():
        return

    try:
        file_path.unlink()
        del upload_file_map[uuid]
        return
    except Exception as e:
        pass

def do_clean_expire_files():
    to_remove = []
    current_time = int(datetime.now().timestamp())

    for uuid, item in upload_file_map.items():
        if item['expireTime'] < current_time:
            to_remove.append(uuid)
            print('-- to rm:', uuid, item)

    for uuid in to_remove:
        try:
            print('-- do rm:', uuid)
            del_file_by_uuid(uuid)
            del upload_file_map[uuid]
        except Exception as err:
            pass

## implement func like js setInterval
async def set_interval(func, time_sec):
    while True:
        func()
        await asyncio.sleep(time_sec)

def clean_expire_files():
    print(datetime.now(), '--- clean expire files')
    do_clean_expire_files()

## interval 30min
app.add_task(set_interval(clean_expire_files, 30*60))


# ----------------------- broadcast
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


# ----------------------- utils

def hash_murmur3(data, seed=0):
    import mmh3
    return mmh3.hash(data, seed, signed=False)

def gen_uuid():
    # uuid = str(uuid4())
    import secrets
    uuid = secrets.token_hex(16)
    return uuid

def gen_thumbnail(img_path):
    import base64
    from io import BytesIO
    from PIL import Image

    img = Image.open(img_path)
    # print('mode:', img.mode, img.size)

    width, height = img.size
    # print('WxH:', width, height)
    if min(width, height) > 64:
        ratio = 64 / min(width, height)
        width, height = int(width * ratio), int(height * ratio)
    # print('WxH:', width, height)

    img.thumbnail((width, height), Image.ANTIALIAS)
    img = img.convert("RGB")
    # img.save('thumbnail.jpg', 'JPEG')
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70, optimize=True)
    img_binary = buffer.getvalue()
    img_base64 = base64.b64encode(img_binary).decode('utf-8')

    return f"data:image/jpeg;base64,{img_base64}"

def get_remote(request):
    # print('headers  :', request.headers)
    # print('forwarded:', request.forwarded)
    ip,port = request.transport.get_extra_info('peername')
    remote = request.headers.get('X-Forwarded-Remote', f'{ip}:{port}')
    return remote

def get_ua(request):
    user_agent = request.headers.get('user-agent')
    ua_obj = UAParser(user_agent)
    return '{} / {}'.format(ua_obj.os['name'], ua_obj.browser['name'])



# ----------------------- Route Handlers

@bp.get('/server')
async def get_server_info(request):
    return sanic_json({
        'server': f"ws://{request.host}{config['server']['prefix']}/push",
        'auth': config['server']['auth'],
    })

@bp.post('/text')
async def post_text_message(request):
    body = request.body.decode('utf-8')
    if len(body) > config['text']['limit']:
        return sanic_json({'error': f"文本长度不能超过 {config['text']['limit']} 字"}, status=400)

    # Escape HTML special characters
    body = body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    body = body.replace('"', '&quot;').replace("'", '&#039;')

    message = {
        'event': 'receive',
        'data': {
            # 'id': len(app.ctx.message_queue),
            'id': app.ctx.message_queue.nextid,
            'type': 'text',
            'room': request.args.get('room', ''),
            'content': body,
        }
    }
    app.ctx.message_queue.append(message)

    broadcast_ws_message(app.ctx.websockets, json.dumps(message), request.args.get('room', ''))
    save_history()
    return sanic_json({})

@bp.delete('/revoke/<message_id:int>')
async def revoke_message(request, message_id):
    idx = next((i for i, msg in enumerate(app.ctx.message_queue) if msg['data']['id'] == message_id), None)
    if idx is None:
        return sanic_json({'error': '不存在的消息 ID'}, status=400)

    app.ctx.message_queue.pop(idx)
    revoke_message = {
        'event': 'revoke',
        'data': {
            'id': message_id,
            'room': request.args.get('room', '')
        }
    }
    broadcast_ws_message(app.ctx.websockets, json.dumps(revoke_message), request.args.get('room', ''))
    save_history()
    return sanic_json({})


@bp.post('/upload')
async def upload_file(request):
    filename = request.body.decode('utf-8')
    uuid = gen_uuid()
    file_info = {
        'name': filename,
        'uuid': uuid,
        'size': 0,  # Will be updated on chunk upload
        'uploadTime': int(datetime.now().timestamp()),
        'expireTime': int(datetime.now().timestamp()) + 3600  # 1-hour expiration
    }
    upload_file_map[uuid] = file_info

    resp = {"code":200, "msg":"", "result": {'uuid': uuid}}
    return sanic_json(resp)

@bp.post('/upload/chunk/<uuid>')
async def upload_file_chunk(request, uuid):
    if uuid not in upload_file_map:
        return sanic_json({'error': '无效的 UUID'}, status=400)

    data = request.body
    file_info = upload_file_map[uuid]
    file_info['size'] += len(data)

    # Append data to file storage
    file_path = storage_folder / uuid
    with open(file_path, 'ab') as f:
        f.write(data)

    return sanic_json({})


@bp.post('/upload/finish/<uuid>')
async def finish_upload(request, uuid):
    if uuid not in upload_file_map:
        return sanic_json({'error': '无效的 UUID'}, status=400)

    file_info = upload_file_map[uuid]
    file_path = storage_folder / uuid

    message = {
        'event': 'receive',
        'data': {
            # 'id': len(app.ctx.message_queue),
            'id': app.ctx.message_queue.nextid,
            'type': 'file',
            'room': request.args.get('room', ''),
            'name': file_info['name'],
            'size': file_info['size'],
            'cache': file_info['uuid'],
            'expire': file_info['expireTime']
        }
    }

    # generating thumbnail if it's an image
    try:
        if file_info['size'] > 33554432:  # too large
            pass
        else:
            loop = asyncio.get_event_loop()
            thumbnail_b64 = await loop.run_in_executor(None, gen_thumbnail, file_path)
            # print('--thumb:', thumbnail_b64)
            # file_info['thumbnail'] = thumbnail_b64
            message['data']['thumbnail'] = thumbnail_b64
    except Exception as e:
        print(f"Thumbnail generation error: {e}")

    app.ctx.message_queue.append(message)

    broadcast_ws_message(app.ctx.websockets, json.dumps(message), request.args.get('room', ''))
    save_history()
    return sanic_json({})

async def ws_send_history(ws, room):
    # print('--- send hist for client:', room, type(room))
    for message in app.ctx.message_queue:
        msg_room = message.get('data', {}).get('room', '') or ''
        # print('-- msg room:', msg_room, type(msg_room))
        if msg_room == room:  ## only to ROOM
            msg = json.dumps(message)
            await ws.send(msg)



async def ws_send_devices(request, ws):
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
    broadcast_ws_message(app.ctx.websockets, json.dumps({
        'event': 'connect',
        'data': {
            'id': device_id,
            **device_meta,
        },
    }), room)

    return device_id, room


@bp.websocket('/push')
async def ws_push(request, ws):
    print('==app:', app, id(app), threading.get_native_id())
    # print('==app.ctx:', app.ctx, id(app.ctx))
    # print('--que:', app.ctx.message_queue, id(app.ctx.message_queue))
    app.ctx.websockets.add(ws)

    ws.remote = get_remote(request)
    ws.ua = get_ua(request)
    ws.room = request.args.get('room', '')
    auth = request.args.get('auth', False)

    global config
    if auth != config.get('server').get('auth', False):
        forbid = '{"event":"forbidden","data":{}}'
        print('---forbid:', FG.z+FG.r+'', f'{ws.remote:21}', ws.ua, FG.z)
        await ws.send(forbid)
        return

    # print("\n----- new conn:", ws, ws.remote, ws.ua, ws.room)
    print("\n----- new conn:", ws.remote, ws.ua, ws.room)
    print( BG.b, len(app.ctx.websockets), FG.z+FG.g+' - new conn', f'{ws.remote:21}', f'{ws.ua:20}', f'Room:{ws.room}', FG.z)

    # s_config = '{"event":"config","data":{"version":"py3-1.0.0","text":{"limit":4096},"file":{"expire":3600,"chunk":2097152,"limit":67108864}}}'
    # await ws.send(s_config)
    event_config = {
        'event':'config',
        'data':{
            'version': version,
            'text': config.get('text', None),
            'file': config.get('file', None)
    }}
    await ws.send(json.dumps(event_config))
    await ws_send_history(ws, ws.room)
    device_id,room = await ws_send_devices(request, ws)

    try:
        # i = 0
        while True:
            # i+=1
            # print('-- recv', i)
            await ws.recv()
    except (Exception, asyncio.exceptions.CancelledError) as e:
        print(f"WebSocket error:", e)
    finally:
        ## send to ALL or ROOM
        broadcast_ws_message(app.ctx.websockets, json.dumps({
            'event': 'disconnect',
            'data': {
                'id': device_id,
            },
        }), room)
        del device_connected[device_id]
        # print('--ws rm1:', app.ctx.websockets, ws, ws.ws_proto)
        # print('--ws rm1:', app.ctx.websockets, ws, ws.remote)
        print( BG.b, len(app.ctx.websockets), FG.z+FG.r+' - conn close', f'{ws.remote:21}', ws.ua, FG.z)
        # app.ctx.websockets.remove(ws)
        app.ctx.websockets.discard(ws)


@bp.get('/file/<uuid>')
async def get_file(request, uuid):
    file_info = upload_file_map.get(uuid)
    if not file_info:
        return response.text('File not found', status=404)

    file_path = storage_folder / uuid
    if not file_path.exists():
        return response.text('File not found', status=404)

    return await response.file(file_path)

@bp.delete('/file/<uuid>')
async def del_file(request, uuid):
    file_info = upload_file_map.get(uuid)
    if not file_info:
        return response.text('File not found', status=404)

    file_path = storage_folder / uuid
    if not file_path.exists():
        return response.text('File not found', status=404)

    try:
        file_path.unlink()
        del upload_file_map[uuid]
        save_history()
        return response.text('File deleted successfully', status=200)
    except Exception as e:
        return response.text(f'Error deleting file: {e}', status=500)


# ----------------------- staic

bp.static('/', './static', name='ui')  ## need ui2
bp.static('/', './static/index.html', name='ui2', strict_slashes=True)  ## ok

app.ctx.websockets = set()  # Store WebSocket connections
# print('==app:', app, id(app), threading.get_native_id())

# app.blueprint(bp, url_prefix=config['server']['prefix'], index='index.html')
app.blueprint(bp, url_prefix=config['server']['prefix'])

@app.before_server_start
async def attach_dat(app, loop):
    print('==app:', app, id(app), threading.get_native_id())
    load_history()


def dump_urls():
    print(f'-------- urls:{FG.g}')
    if hasattr(app.router, 'routes_names'):
        for handler, (rule, router) in app.router.routes_names.items():
            # print('urls: ', rule, router, handler)
            print('  %-20s %s ' % (handler, rule))
    else:
        lst = list(app.router.routes)
        lst.sort(key=lambda o:o.path)
        # lst.sort(key=lambda o:o.name, reverse=1)
        for k in lst:
            print('  %-20s %s ' % (k.name.partition('.')[2], '/'+k.path))
    print(f'{FG.z}--------')


if __name__ == "__main__":
    dump_urls()

    # print('==app:', app, id(app), threading.get_native_id())
    # print('==app.ctx:', app.ctx, id(app.ctx))
    # print('== ws:', app.ctx.websockets)
    port = config.get('server', {}).get('port', 8000)
    # app.run(host="0.0.0.0", port=8000)
    app.run(host="0.0.0.0", port=port)

