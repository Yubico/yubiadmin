import sys
import os
import imp
import errno
from yubiadmin import default_settings

__all__ = [
    'settings'
]

SETTINGS_FILE = os.getenv('YUBIADMIN_SETTINGS',
                          '/etc/yubico/admin/yubiadmin.conf')

VALUES = {
    #Web interface
    'USERNAME': 'user',
    'PASSWORD': 'pass',
    'INTERFACE': 'iface',
    'PORT': 'port'
}


def parse(conf, settings={}):
    for confkey, settingskey in VALUES.items():
        try:
            settings[settingskey] = conf.__getattribute__(confkey)
        except AttributeError:
            pass
    return settings


settings = parse(default_settings)

dont_write_bytecode = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    user_settings = imp.load_source('user_settings', SETTINGS_FILE)
    settings = parse(user_settings, settings)
except IOError, e:
    if not e.errno in [errno.ENOENT, errno.EACCES]:
        raise e
finally:
    sys.dont_write_bytecode = dont_write_bytecode
