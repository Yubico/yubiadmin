from wtforms.fields import IntegerField
from wtforms.validators import NumberRange
from yubiadmin.util import App, DBConfigForm, ConfigForm, FileConfig

__all__ = [
    'app'
]


def yk_read_str(varname):
    return r'\$baseParams\[\'__YKVAL_%s__\'\] = [\'"](.*)[\'"];' % varname


def yk_write_str(varname):
    return lambda x: '$baseParams[\'__YKVAL_%s__\'] = "%s";' % (varname, x)


def yk_read_int(varname):
    return r'\$baseParams\[\'__YKVAL_%s__\'\] = (\d+);' % varname


def yk_write_int(varname):
    return lambda x: '$baseParams[\'__YKVAL_%s__\'] = %s;' % (varname, x)


def db_read(varname):
    return r'\$db%s=\'(.*)\';' % varname


def db_write(varname):
    return lambda x: '$db%s=\'%s\';' % (varname, x)


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
                yk_read_int('SYNC_DEFAULT_LEVEL'),
                yk_write_int('SYNC_DEFAULT_LEVEL'),
                60
            ), (
                'sync_secure',
                yk_read_int('SYNC_SECURE_LEVEL'),
                yk_write_int('SYNC_SECURE_LEVEL'),
                40
            ), (
                'sync_fast',
                yk_read_int('SYNC_FAST_LEVEL'),
                yk_write_int('SYNC_FAST_LEVEL'),
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
            yk_read_int('SYNC_DEFAULT_TIMEOUT'),
            yk_write_int('SYNC_DEFAULT_TIMEOUT'),
            1
        )]
    )


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
        return 'Not yet implemented.'

    def ksms(self, request):
        """
        Key Store Modules
        """
        return 'Not yet implemented.'

app = YubikeyVal()
