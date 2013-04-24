__all__ = [
    'app'
]


class YubikeyKsm(object):
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
        return {}

app = YubikeyKsm()
