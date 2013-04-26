from wtforms import Form, StringField, IntegerField, PasswordField, Field
from wtforms.widgets import PasswordInput, TextArea
from wtforms.validators import Optional, NumberRange
from yubiadmin.util.config import ValueHandler, FileConfig

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
    dbtype = StringField('DB type')
    dbserver = StringField('Host')
    dbport = IntegerField('Port', [Optional(), NumberRange(1, 65535)])
    dbname = StringField('DB name')
    dbuser = StringField('DB username')
    dbpass = PasswordField('DB password',
                           widget=PasswordInput(hide_value=False))

    def db_handler(self, varname, default):
        pattern = r'\$%s=\'(.*)\';' % varname
        writer = lambda x: '$%s=\'%s\';' % (varname, x)
        return ValueHandler(pattern, writer, default=default)

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
