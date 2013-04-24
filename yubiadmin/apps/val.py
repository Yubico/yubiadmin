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

    def general(self, request):
        """
        General
        """
        sync_form = SyncLevelsForm(request.params)
        misc_form = MiscForm(request.params)
        return {
            'fieldsets': [sync_form, misc_form]
        }

    def database(self, request):
        """
        Database Settings
        """
        return {}

    def syncpool(self, request):
        """
        Sync pool
        """
        return {}

    def ksms(self, request):
        """
        Key Store Modules
        """
        return {}

app = YubikeyVal()
