import os
from importlib import import_module

apps = []
__all__ = ['apps']

for filename in os.listdir(os.path.dirname(__file__)):
    if filename.endswith('.py') and not filename.startswith('__'):
        module = import_module('yubiadmin.apps.%s' % filename[:-3])
        __all__.append(module)
        if hasattr(module, 'app'):
            apps.append(module.app)
