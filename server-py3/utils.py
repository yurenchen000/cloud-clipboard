
from uaparser import UAParser

def hash_murmur3(data, seed=0):
    import mmh3
    return mmh3.hash(data, seed, signed=False)

def gen_uuid():
    # from uuid import uuid4
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

