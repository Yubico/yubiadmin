from yubiadmin.util.app import App
from yubiadmin.util.form import DBConfigForm

__all__ = [
    'app'
]


class YubikeyKsm(App):
    """
    YubiKey Key Storage Module

    YubiKey KSM server
    """

    name = 'ksm'
    sections = ['database']

    def database(self, request):
        """
        Database Settings
        """
        dbform = DBConfigForm('/etc/yubico/ksm/config-db.php',
                              dbname='ykksm', dbuser='ykksmreader')
        return self.render_forms(request, [dbform])

app = YubikeyKsm()
