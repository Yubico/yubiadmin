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

from wtforms import Form
from wtforms.fields import (
    TextField, IntegerField, PasswordField, TextAreaField, HiddenField, Field)
from wtforms.widgets import PasswordInput, TextArea
from wtforms.validators import Optional, NumberRange
from yubiadmin.util.config import RegexHandler, FileConfig, php_inserter

__all__ = [
    'ListField',
    'ConfigForm',
    'FileForm',
    'DBConfigForm'
]


class ListField(Field):
    widget = TextArea()

    def process_formdata(self, values):
        if values:
            self.data = filter(None, [x.strip() for x in values[0].split()])

    def _value(self):
        if self.data:
            return '\n'.join(self.data)
        else:
            return ''

    def validate(self, form, extra_validators=tuple()):
        self.errors = []
        success = True
        field = HiddenField(validators=self.validators, _form=form,
                            _name='item')
        if self.data is None:
            self.data = []
        for value in self.data:
            field.data = value
            if not field.validate(form, extra_validators):
                success = False
                self.errors.extend(field.errors)
        return success


class ConfigForm(Form):
    """
    Form that can load and save data to a config.
    """
    config = None

    def load(self):
        self.config.read()
        for field in self:
            if field.id in self.config:
                field.process_data(self.config[field.id])

    def save(self):
        self.config.read()
        for field in self:
            if field.id in self.config:
                self.config[field.id] = field.data
        self.config.commit()


class FileForm(ConfigForm):
    """
    Form that displays the entire content of a file.
    """
    content = TextAreaField('File')
    attrs = {'content': {'class': 'span9 code editor', 'rows': 25}}

    class Handler(object):
        def read(self, content):
            return content

        def write(self, content, value):
            return value

    def __init__(self, filename, legend=None, description=None, lang=None,
                 *args, **kwargs):
        self.config = FileConfig(filename, [('content', self.Handler())])
        self.legend = legend
        self.description = description
        if lang:
            self.attrs['content']['ace-mode'] = lang
        super(FileForm, self).__init__(*args, **kwargs)
        self.content.label.text = 'File: %s' % filename


class DBConfigForm(ConfigForm):
    """
    Complete form for editing a dbconfig-common generated for PHP.
    """
    legend = 'Database'
    description = 'Settings for connecting to the database.'
    dbtype = TextField('Database type')
    dbserver = TextField('Host')
    dbport = IntegerField('Port', [Optional(), NumberRange(1, 65535)])
    dbname = TextField('Database name')
    dbuser = TextField('Username')
    dbpass = PasswordField('Password',
                           widget=PasswordInput(hide_value=False))

    def db_handler(self, varname, default):
        pattern = r'\$%s=\'(.*)\';' % varname
        writer = lambda x: '$%s=\'%s\';' % (varname, x)
        return RegexHandler(pattern, writer, inserter=php_inserter,
                            default=default)

    def __init__(self, filename, *args, **kwargs):
        if not self.config:
            self.config = FileConfig(
                filename,
                [
                    ('dbtype', self.db_handler(
                        'dbtype', kwargs.pop('dbtype', 'mysql'))),
                    ('dbserver', self.db_handler(
                        'dbserver', kwargs.pop('dbserver', 'localhost'))),
                    ('dbport', self.db_handler(
                        'dbport', kwargs.pop('dbport', ''))),
                    ('dbname', self.db_handler(
                        'dbname', kwargs.pop('dbname', ''))),
                    ('dbuser', self.db_handler(
                        'dbuser', kwargs.pop('dbuser', ''))),
                    ('dbpass', self.db_handler(
                        'dbpass', kwargs.pop('dbpass', ''))),
                ]
            )

        super(DBConfigForm, self).__init__(*args, **kwargs)
