
import asyncio
from datetime import datetime
from history import storage_folder

## Periodically clean up expired files

def del_file_by_uuid(uuid, upload_file_map):
    file_path = storage_folder / uuid
    if not file_path.exists():
        return

    try:
        file_path.unlink()
        del upload_file_map[uuid]
        return
    except Exception as e:
        pass

def do_clean_expire_files(upload_file_map):
    to_remove = []
    current_time = int(datetime.now().timestamp())

    for uuid, item in upload_file_map.items():
        if item['expireTime'] < current_time:
            to_remove.append(uuid)
            print('-- to rm:', uuid, item)

    for uuid in to_remove:
        try:
            print('-- do rm:', uuid)
            del_file_by_uuid(uuid, upload_file_map)
            del upload_file_map[uuid]
        except Exception as err:
            pass

## implement func like js setInterval
async def set_interval(func, time_sec, *arg):
    while True:
        func(*arg)
        await asyncio.sleep(time_sec)

def clean_expire_files(upload_file_map):
    print(datetime.now(), '--- clean expire files')
    do_clean_expire_files(upload_file_map)

