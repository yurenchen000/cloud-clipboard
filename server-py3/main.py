
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



from uaparser import UAParser
from pathlib import Path


version = 'py3-1.1.0'

app = Sanic(__name__)
from sanic import Blueprint
bp = Blueprint('bp')



# ----------------------- config
from config import load_config

# print('--name:', __name__)
config = load_config()
if __name__ == '__main__':
    print('--config:', FG.y+json.dumps(config, indent=2)+FG.z)


'''
d={'a':123,'c':123}
o={'b':345, 'a':234}
last = {**d, **o}

TODO:
  default values //done

  file:
    limit,    //done
    expire,   //done
    chunk     //no limit
  text: limit //done
  server:
    history  //done
    auth     //done
    port     //done
    prefix   //done
'''

# ----------------------- msg queue
from history import MsgList

# print('- config.server.history:', config.server.history)
# app.ctx.message_queue = []
app.ctx.message_queue = MsgList(config.server.history)
app.ctx.websockets = set()  # Store WebSocket connections

upload_file_map = {}
device_connected = {}


# ----------------------- history
from history import load_history, save_history
from history import storage_folder, history_path

from file_expire import set_interval, clean_expire_files

## interval 30min
app.add_task(set_interval(clean_expire_files, 30*60, upload_file_map))


# ----------------------- broadcast
from ws_send import ws_send_devices, ws_send_history, broadcast_ws_message

# ----------------------- utils

from utils import hash_murmur3, gen_uuid, gen_thumbnail
from utils import get_remote, get_ua

# ----------------------- Route Handlers

@bp.get('/server')
async def get_server_info(request):
    return sanic_json({
        'server': f"ws://{request.host}{config.server.prefix}/push",
        'auth': config.server.auth,
    })

@bp.post('/text')
async def post_text_message(request):
    body = request.body.decode('utf-8')
    if len(body) > config['text']['limit']:
        return sanic_json({'error': f"文本长度不能超过 {config.text.limit} 字"}, status=400)

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
    save_history(upload_file_map, app.ctx.message_queue)
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
    save_history(upload_file_map, app.ctx.message_queue)
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
        # 'expireTime': int(datetime.now().timestamp()) + 3600  # 1-hour expiration
        'expireTime': int(datetime.now().timestamp()) + config.file.expire
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

    # if file_info['size'] > 10:
    if file_info['size'] > config.file.limit:
        return sanic_json({'code':400, 'result': '文件大小已超过限制', 'msg':''}, status=400) # same as node version

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
    save_history(upload_file_map, app.ctx.message_queue)
    return sanic_json({})



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
    if auth != config.server.auth:
        forbid = '{"event":"forbidden","data":{}}'
        print('---forbid:', FG.z+FG.r+'', f'{ws.remote:21}', ws.ua, FG.z)
        await ws.send(forbid)
        return

    # print("\n----- new conn:", ws, ws.remote, ws.ua, ws.room)
    print("\n----- new conn:", ws.remote, ws.ua, ws.room)
    print( BG.b, len(app.ctx.websockets), FG.z+FG.g+' - new conn', f'{ws.remote:21}', f'{ws.ua:20}', f'Room:{ws.room}', FG.z)

    event_config = {
        'event':'config',
        'data':{
            'version': version,
            'text': config.text,
            'file': config.file
    }}
    await ws.send(json.dumps(event_config))
    await ws_send_history(ws, ws.room, app.ctx.message_queue)
    device_id,room = await ws_send_devices(request, ws, app.ctx.websockets, device_connected)

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
        save_history(upload_file_map, app.ctx.message_queue)
        return response.text('File deleted successfully', status=200)
    except Exception as e:
        return response.text(f'Error deleting file: {e}', status=500)


# ----------------------- staic

bp.static('/', './static', name='ui')  ## need ui2
bp.static('/', './static/index.html', name='ui2', strict_slashes=True)  ## ok

# print('==app:', app, id(app), threading.get_native_id())

# app.blueprint(bp, url_prefix=config['server']['prefix'], index='index.html')
app.blueprint(bp, url_prefix=config.server.prefix)

@app.before_server_start
async def attach_dat(app, loop):
    print('==app:', app, id(app), threading.get_native_id())
    load_history(upload_file_map, app.ctx.message_queue)


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
    port = config.server.port
    # app.run(host="0.0.0.0", port=8000)
    app.run(host="0.0.0.0", port=port)

