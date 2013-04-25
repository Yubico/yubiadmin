import re
from wtforms.fields import IntegerField, StringField, Field
from wtforms.widgets import TextInput
from wtforms.validators import NumberRange
from yubiadmin.util import App, DBConfigForm, ConfigForm, FileConfig

__all__ = [
    'app'
]


def yk_read(varname, prefix='', suffix='', flags=None):
    regex = r'(?m)^(?!#)\$baseParams\[\'__YKVAL_%s__\'\]\s*=' \
            '\s*%s(.*?)%s\s*;\s*$' % (varname, prefix, suffix)
    if flags:
        regex = '(?%s)' % flags + regex
    return regex


def yk_write(varname, prefix='', suffix=''):
    return lambda x: '$baseParams[\'__YKVAL_%s__\'] = %s%s%s;' % \
        (varname, prefix, x, suffix)


def yk_read_str(varname):
    return yk_read(varname, '[\'"]', '[\'"]')


def yk_write_str(varname):
    return yk_write(varname, '"', '"')


class SyncLevelsForm(ConfigForm):
    legend = 'Sync Levels'

    sync_default = IntegerField('Default', [NumberRange(1, 100)])
    sync_secure = IntegerField('Secure', [NumberRange(1, 100)])
    sync_fast = IntegerField('Fast', [NumberRange(1, 100)])

    config = FileConfig(
        '/home/dain/yubico/yubiadmin/ykval-config.php',
        [
            (
                'sync_default',
                yk_read('SYNC_DEFAULT_LEVEL'),
                yk_write('SYNC_DEFAULT_LEVEL'),
                60
            ), (
                'sync_secure',
                yk_read('SYNC_SECURE_LEVEL'),
                yk_write('SYNC_SECURE_LEVEL'),
                40
            ), (
                'sync_fast',
                yk_read('SYNC_FAST_LEVEL'),
                yk_write('SYNC_FAST_LEVEL'),
                1
            ),

        ]
    )


class MiscForm(ConfigForm):
    legend = 'Misc'
    default_timeout = IntegerField('Default Timeout', [NumberRange(0)])

    config = FileConfig(
        '/home/dain/yubico/yubiadmin/ykval-config.php',
        [(
            'default_timeout',
            yk_read('SYNC_DEFAULT_TIMEOUT'),
            yk_write('SYNC_DEFAULT_TIMEOUT'),
            1
        )]
    )


class ListField(Field):
    COMMENT = re.compile(r'/\*.*?\*/')
    VALUE = re.compile(r'\s*[\'"](.*)[\'"]\s*')
    widget = TextInput()

    def process_formdata(self, values):
        if values:
            self.data = filter(None, [x.strip() for x in values[0].split(',')])

    def process_data(self, value):
        if value:
            data = []
            value = self.COMMENT.sub('', value)
            for val in value.split(','):
                match = self.VALUE.match(val)
                if match:
                    data.append(match.group(1))
            self.data = data
        else:
            self.data = []

    def _value(self):
        if self.data:
            return ', '.join(self.data)
        else:
            return ''


def yk_array_write(varname):
    str_write = yk_write(varname, 'array(', ')')
    return lambda xs: str_write(', '.join(['"%s"' % x for x in xs]))


class SyncPoolForm(ConfigForm):
    legend = 'Sync Settings'
    sync_interval = IntegerField('Sync Interval', [NumberRange(1)])
    resync_timeout = IntegerField('Resync Timeout', [NumberRange(1)])
    old_limit = IntegerField('Old Limit', [NumberRange(1)])
    sync_pool = ListField('Servers')
    sync_pool_add = StringField('Add Server')

    config = FileConfig(
        '/home/dain/yubico/yubiadmin/ykval-config.php',
        [
            (
                'sync_interval',
                yk_read('SYNC_INTERVAL'),
                yk_write('SYNC_INTERVAL'),
                10
            ), (
                'resync_timeout',
                yk_read('SYNC_RESYNC_TIMEOUT'),
                yk_write('SYNC_RESYNC_TIMEOUT'),
                30
            ), (
                'old_limit',
                yk_read('SYNC_OLD_LIMIT'),
                yk_write('SYNC_OLD_LIMIT'),
                10
            ), (
                'sync_pool',
                yk_read('SYNC_POOL', 'array\(', '\)', 's'),
                yk_array_write('SYNC_POOL'),
                ''
            )
        ]
    )

    def validate(self):
        if super(SyncPoolForm, self).validate():
            if self.sync_pool_add.data:
                self.sync_pool.data.append(self.sync_pool_add.data)
                self.sync_pool_add.process_data(None)
            return True
        return False

COMMENT = re.compile(r'/\*.*?\*/')


def remove_comments(content):
    return COMMENT.sub('', content)


class YubikeyVal(App):
    """
    YubiKey Validation Server

    YubiKey OTP validation server
    """

    name = 'val'
    sections = ['general', 'database', 'syncpool', 'ksms']

    def general(self, request):
        """
        General
        """
        return self.render_forms(request, [SyncLevelsForm(), MiscForm()])

    def database(self, request):
        """
        Database Settings
        """
        return self.render_forms(request, [
            DBConfigForm('/home/dain/yubico/yubiadmin/config-db.php')])

    def syncpool(self, request):
        """
        Sync pool
        """
        sync_pool_form = SyncPoolForm()
        form_page = self.render_forms(request, [sync_pool_form])

        print 'Sync pool: %s' % \
            remove_comments(sync_pool_form.config['sync_pool'])
        return form_page

    def ksms(self, request):
        """
        Key Store Modules
        """
        return 'Not yet implemented.'

app = YubikeyVal()
