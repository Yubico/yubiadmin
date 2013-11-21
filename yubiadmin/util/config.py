# Copyright (c) 2013 Yubico AB
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import re
import errno
import csv
import logging
from collections import MutableMapping, OrderedDict

__all__ = [
    'RegexHandler',
    'FileConfig',
    'strip_comments',
    'php_inserter',
    'python_handler',
    'python_list_handler',
    'parse_block',
    'parse_value'
]

log = logging.getLogger(__name__)

PHP_BLOCKS = re.compile('(?ms)<\?php(.*?)\s*\?>')
QUOTED_STR = re.compile(r'\s*[\'"](.*)[\'"]\s*')
COMMENTS = re.compile(
    r'#.*?$|//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE
)


def php_inserter(content, value):
    match = PHP_BLOCKS.search(content)
    if match:
        content = PHP_BLOCKS.sub(
            '<?php\g<1>\n%s\n?>' % (value), content)
    else:
        if content:
            content += os.linesep
        content += '<?php\n%s\n?>' % (value)
    return content


def python_handler(varname, default):
    pattern = r'(?sm)^\s*%s\s*=\s*(.*?)\s*$' % varname
    reader = lambda match: parse_value(match.group(1))
    writer = lambda x: '%s = %r' % (varname, str(x) if isinstance(x, unicode)
                                    else x)
    return RegexHandler(pattern, writer, reader, default=default)


class python_list_handler:
    def __init__(self, varname, default):
        self.pattern = re.compile(r'(?m)^\s*%s\s*=\s*\[' % varname)
        self.varname = varname
        self.default = default

    def _get_block(self, content):
        match = self.pattern.search(content)
        if match:
            return parse_block(content[match.end():], '[', ']')
        return None

    def read(self, content):
        block = self._get_block(content)
        if block:
            block = re.sub(r'(?m)\s+', '', block)
            parts = next(csv.reader([block], skipinitialspace=True), [])
            return [strip_quotes(x) for x in parts]
        else:
            return self.default

    def write(self, content, value):
        block = self._get_block(content)
        value = ('%s = [\n' % self.varname +
                 '\n'.join(['    "%s",' % x for x in value]) +
                 '\n]')
        if block:
            match = self.pattern.search(content)
            start = content[:match.start()]
            end = content[match.end() + len(block) + 1:]
            return start + value + end
        else:
            return '%s\n%s' % (content, value)


def strip_comments(text, ):
    def replacer(match):
        s = match.group(0)
        if s[0] in ['/', '#']:
            return ''
        else:
            return s
    return COMMENTS.sub(replacer, text)


def strip_quotes(value):
    match = QUOTED_STR.match(value)
    if match:
        return match.group(1)
    return value


def parse_block(content, opening='(', closing=')'):
    level = 0
    index = 0
    for c in content:
        if c == opening:
            level += 1
        elif c == closing:
            level -= 1
        if level < 0:
            return content[:index]
        index += 1
    return content


def parse_value(valrepr):
    try:
        return int(valrepr)
    except ValueError:
        pass
    try:
        return float(valrepr)
    except ValueError:
        pass
    val_lower = valrepr.lower()
    if val_lower == 'true':
        return True
    elif val_lower == 'false':
        return False
    elif val_lower in ['none', 'null']:
        return None
    return strip_quotes(valrepr)


class RegexHandler(object):
    def __init__(self, pattern, writer, reader=lambda x: x.group(1),
                 inserter=lambda x, y: '%s\n%s' % (x, y),
                 default=None):
        self.pattern = re.compile(pattern)
        self.writer = writer
        self.reader = reader
        self.inserter = inserter
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
            new_content = self.pattern.sub(self.writer(value), content, 1)
            if self.read(content) == self.read(new_content):
                #Value remains unchanged, don't re-write it.
                return content
            else:
                return new_content
        else:
            return self.inserter(content, self.writer(value))


class FileConfig(MutableMapping):
    """
    Maps key-value pairs to a backing config file.
    You can manually edit the file by modifying self.content.
    """
    def __init__(self, filename, params=[]):
        self.filename = filename
        self.params = OrderedDict()
        for param in params:
            self.add_param(*param)

    def read(self):
        try:
            with open(self.filename, 'r') as file:
                self.content = unicode(file.read())
        except IOError as e:
            log.error(e)
            self.content = u''
            #Initialize all params from default values.
            for key in self.params:
                self[key] = self[key]

    def commit(self):
        if not os.path.isfile(self.filename):
            dir = os.path.dirname(self.filename)
            try:
                os.makedirs(dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise e
        with open(self.filename, 'w+') as file:
            #Fix all linebreaks
            file.write(os.linesep.join(self.content.splitlines()))

    def add_param(self, key, handler):
        self.params[key] = handler

    def __iter__(self):
        return self.params.__iter__()

    def __len__(self):
        return len(self.params)

    def __getitem__(self, key):
        return self.params[key].read(self.content)

    def __setitem__(self, key, value):
        self.content = self.params[key].write(self.content, value)

    def keys(self):
        return self.params.keys()

    def __delitem__(self, key):
        del self.params[key]
