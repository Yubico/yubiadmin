from wtforms import Form, IntegerField

__all__ = [
    'app'
]


class MiscForm(Form):
    legend = 'Misc'
    default_timeout = IntegerField('Default Timeout')


class SyncLevelsForm(Form):
    legend = 'Sync Levels'
    sync_default = IntegerField('Default')
    sync_secure = IntegerField('Secure')
    sync_fast = IntegerField('Fast')


class YubikeyVal(object):
    """
    YubiKey Validation Server

    YubiKey OTP validation server
    """

    name = 'val'
    sections = ['general', 'database', 'syncpool', 'ksms']

    def general(self, **kwargs):
        """
        General
        """
        if kwargs:
            # Save
            print kwargs
        return {
            'fieldsets': [SyncLevelsForm(kwargs), MiscForm(kwargs)]
        }

    def database(self):
        """
        Database Settings
        """
        return {}

    def syncpool(self):
        """
        Sync pool
        """
        return {}

    def ksms(self):
        """
        Key Store Modules
        """
        return {}

app = YubikeyVal()
