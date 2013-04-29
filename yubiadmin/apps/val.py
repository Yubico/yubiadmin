import re
import os
import subprocess
from wtforms.fields import IntegerField
from wtforms.validators import NumberRange, IPAddress, URL
from yubiadmin.util.app import App
from yubiadmin.util.config import ValueHandler, FileConfig, php_inserter
from yubiadmin.util.form import ConfigForm, DBConfigForm, ListField

__all__ = [
    'app'
]

COMMENT = re.compile(r'/\*.*?\*/')
VALUE = re.compile(r'\s*[\'"](.*)[\'"]\s*')


def yk_pattern(varname, prefix='', suffix='', flags=None):
    regex = r'(?m)^(?!#)\$baseParams\[\'__YKVAL_%s__\'\]\s*=' \
            '\s*%s(.*?)%s\s*;\s*$' % (varname, prefix, suffix)
    if flags:
        regex = '(?%s)' % flags + regex
    return regex


def yk_write(varname, prefix='', suffix=''):
    return lambda x: '$baseParams[\'__YKVAL_%s__\'] = %s%s%s;' % \
        (varname, prefix, x, suffix)


def yk_handler(varname, default):
    return ValueHandler(yk_pattern(varname), yk_write(varname),
                        inserter=php_inserter, default=default)


def strip_quotes(value):
    match = VALUE.match(value)
    if match:
        return match.group(1)
    return value


def strip_comments(value):
    return COMMENT.sub('', value)


def yk_parse_arraystring(value):
    value = strip_comments(value).strip()
    return filter(None, [strip_quotes(x) for x in value.split(',')])


def yk_array_handler(varname):
    pattern = yk_pattern(varname, 'array\(', '\)', 's')
    str_write = yk_write(varname, 'array(' + os.linesep, os.linesep + ')')
    writer = lambda xs: str_write((',' + os.linesep)
                                  .join(['\t"%s"' % x for x in xs]))
    reader = lambda match: yk_parse_arraystring(match.group(1))
    return ValueHandler(pattern, writer, reader, php_inserter, [])


def run(cmd):
    p = subprocess.Popen(['sh', '-c', cmd], stdout=subprocess.PIPE)
    return p.wait(), p.stdout.read()


def invoke_rc_d(cmd):
    if run('which invoke-rd.d')[0] == 0:
        return run('invoke-rc.d ykval-queue %s' % cmd)
    else:
        return run('/etc/init.d/ykval-queue %s' % cmd)


def is_daemon_running():
    return invoke_rc_d('status')[0] == 0


def restart_daemon():
    invoke_rc_d('restart')


ykval_config = FileConfig(
    '/etc/yubico/val/ykval-config.php',
    [
        ('sync_default', yk_handler('SYNC_DEFAULT_LEVEL', 60)),
        ('sync_secure', yk_handler('SYNC_SECURE_LEVEL', 40)),
        ('sync_fast', yk_handler('SYNC_FAST_LEVEL', 1)),
        ('default_timeout', yk_handler('SYNC_DEFAULT_TIMEOUT', 1)),
        ('sync_interval', yk_handler('SYNC_INTERVAL', 10)),
        ('resync_timeout', yk_handler('SYNC_RESYNC_TIMEOUT', 30)),
        ('old_limit', yk_handler('SYNC_OLD_LIMIT', 10)),
        ('sync_pool', yk_array_handler('SYNC_POOL')),
        ('allowed_sync_pool', yk_array_handler('ALLOWED_SYNC_POOL'))
    ]
)


class SyncLevelsForm(ConfigForm):
    legend = 'Sync Levels'
    description = 'Percentage of syncing required for pre-defined levels.'
    config = ykval_config

    sync_default = IntegerField('Default Level', [NumberRange(1, 100)])
    sync_secure = IntegerField('Secure Level', [NumberRange(1, 100)])
    sync_fast = IntegerField('Fast Level', [NumberRange(1, 100)])


class MiscForm(ConfigForm):
    legend = 'Misc'
    config = ykval_config

    default_timeout = IntegerField('Default Timeout', [NumberRange(0)])


class SyncPoolForm(ConfigForm):
    legend = 'Daemon Settings'
    config = ykval_config
    attrs = {
        'sync_pool': {'rows': 5, 'class': 'input-xlarge'},
        'allowed_sync_pool': {'rows': 5, 'class': 'input-xlarge'}
    }

    sync_interval = IntegerField(
        'Sync Interval', [NumberRange(1)],
        description='How often (in seconds) to sync with other server.')
    resync_timeout = IntegerField('Resync Timeout', [NumberRange(1)])
    old_limit = IntegerField('Old Limit', [NumberRange(1)])
    sync_pool = ListField(
        'Sync Pool URLs', [URL()],
        description='List of URLs to other servers in the sync pool.')
    allowed_sync_pool = ListField(
        'Allowed Sync IPs', [IPAddress()],
        description='List of IP-addresses of other servers that are ' +
        'allowed to sync with this server.')

    def save(self):
        super(SyncPoolForm, self).save()
        if is_daemon_running():
            restart_daemon()


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
        dbform = DBConfigForm('/etc/yubico/val/config-db.php',
                              dbname='ykval', dbuser='ykval_verifier')
        return self.render_forms(request, [dbform])

    def syncpool(self, request):
        """
        Sync Pool
        """
        form_page = self.render_forms(request, [SyncPoolForm()],
                                      template='val/syncpool',
                                      daemon_running=is_daemon_running())
        return form_page

    def daemon(self, request):
        if request.params['daemon'] == 'toggle':
            if is_daemon_running():
                invoke_rc_d('stop')
            else:
                invoke_rc_d('start')
        else:
            restart_daemon()

        return self.redirect('/%s/syncpool' % self.name)

    def ksms(self, request):
        """
        Key Store Modules
        """
        return 'Not yet implemented.'

app = YubikeyVal()
