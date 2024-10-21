

import json
from datetime import datetime
from pathlib import Path

history_path = Path('history.json')
storage_folder = Path('./uploads')

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

# ----------------------- history
## filter-out expire items @load
def save_history(upload_file_map, message_queue):
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
        message['data'] for message in message_queue
        if message['data']['type'] != 'file' or message['data']['expire'] > current_time
    ]
    with open(history_path, 'w') as f:
        json.dump({
            'file': filtered_files,
            'receive': filtered_messages
        }, f)


## filter-out expire items @save
def load_history(upload_file_map, message_queue):
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
                message_queue.append({
                    'event': 'receive',
                    'data': {
                        # 'id': len(message_queue),
                        'id': message_queue.nextid,
                        **msg
                    }
                })
                # print('++append', msg)

            # print('---- file map:', upload_file_map)
            # print('--que:', message_queue, id(message_queue))

