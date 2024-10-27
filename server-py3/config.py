import json
import sys

cfg_default = {
    "server": {
        "host": '0.0.0.0',
        "port": 9501,
        "prefix": '',     # server prefix
        "history": 10,
        "auth": False,    # bool or string
    },
    "text": {
        "limit": 4096
    },
    "file": {
        "expire": 3600,    # 1 hour
        "chunk": 2097152,  # 2 MB
        "limit": 268435456 # 256 MB
    }
}

# https://stackoverflow.com/a/57316993/4896468
class DotDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Recursively turn nested dicts into DotDicts
        for key, value in self.items():
            if type(value) is dict:
                self[key] = DotDict(value)

    def __setitem__(self, key, item):
        if type(item) is dict:
            item = DotDict(item)
        super().__setitem__(key, item)

    def __getitem__(self, key):
        return self.get(key, None)
        # try:
        #     return dict.__getitem__(self, key)
        # except KeyError:
        #     return None

    __setattr__ = __setitem__
    # __getattr__ = dict.__getitem__
    __getattr__ = __getitem__



config_path = 'config.json'
cfg_default = DotDict(cfg_default)

def type_default(obj, _def):
    if isinstance(obj, type(_def)):
        return obj
    else:
        return _def

def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"load_config err: file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"load_config err: file contains invalid JSON: {file_path}")
        return {}

def load_config():
    global config_path
    # config_path = 'config.json' if len(sys.argv)<2 else sys.argv[1]

    if len(sys.argv)>1:
        config_path = sys.argv[1]

    print('load_config from', config_path)

    cfg_loaded = DotDict(load_json(config_path))
    cfg_last = {
        'server': {**cfg_default.server, **type_default(cfg_loaded.server, {})},
        'file'  : {**cfg_default.file,   **type_default(cfg_loaded.file,   {})},
        'text'  : {**cfg_default.text,   **type_default(cfg_loaded.text,   {})}
    }

    config = DotDict(cfg_last)
    if config.server.auth == '':
        config.server.auth = False

    return config

## test
if __name__ == '__main__':
    c = load_config()
    print('conf:', c)
