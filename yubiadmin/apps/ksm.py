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

    def database(self):
        """
        Database Settings
        """
        return {}

app = YubikeyKsm()
