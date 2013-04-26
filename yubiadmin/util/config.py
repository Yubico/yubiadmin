import os
import re
from UserDict import DictMixin

__all__ = [
    'ValueHandler',
    'FileConfig'
]


class ValueHandler(object):
    def __init__(self, pattern, writer, reader=lambda x: x.group(1),
                 default=None):
        self.pattern = re.compile(pattern)
        self.writer = writer
        self.reader = reader
        self.default = default

    def read(self, content):
        match = self.pattern.search(content)
        if match:
            return self.reader(match)
        return self.default

    def write(self, content, value):
        if value is None:
            value = ''
        if self.pattern.search(content):
            content = self.pattern.sub(self.writer(value), content, 1)
        else:
            content += os.linesep + self.writer(value)
        return content


class FileConfig(DictMixin):
    """
    Maps key-value pairs to a backing config file.
    You can manually edit the file by modifying self.content.
    """
    def __init__(self, filename, params=[]):
        self.filename = filename
        self.params = {}
        for param in params:
            self.add_param(*param)

    def read(self):
        try:
            with open(self.filename, 'r') as file:
                self.content = file.read()
        except IOError as e:
            print e
            self.content = ''

    def commit(self):
        with open(self.filename, 'w+') as file:
            file.write(self.content)

    def add_param(self, key, handler):
        self.params[key] = handler

    def __getitem__(self, key):
        return self.params[key].read(self.content)

    def __setitem__(self, key, value):
        self.content = self.params[key].write(self.content, value)

    def keys(self):
        return self.params.keys()

    def __delitem__(self, key):
        del self.params[key]
