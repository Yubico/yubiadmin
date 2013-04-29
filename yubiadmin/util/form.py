from wtforms import Form
from wtforms.fields import (
    TextField, IntegerField, PasswordField, HiddenField, Field)
from wtforms.widgets import PasswordInput, TextArea
from wtforms.validators import Optional, NumberRange
from yubiadmin.util.config import ValueHandler, FileConfig, php_inserter

__all__ = [
    'ListField',
    'ConfigForm',
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
        return ValueHandler(pattern, writer, inserter=php_inserter,
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
