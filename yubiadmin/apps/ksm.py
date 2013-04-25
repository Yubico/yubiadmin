from yubiadmin.util import App, DBConfigForm

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
        return self.render_forms(request, [
            DBConfigForm('/etc/yubico/ksm/config-db.php')])

app = YubikeyKsm()
