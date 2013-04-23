__all__ = [
    'app'
]


class YubikeyKsm(object):
    """
    YubiKey Key Storage Module

    YubiKey KSM server
    """

    name = 'ksm'
    sections = ['general', 'database', 'ksms']

    def general(self):
        """
        General
        """
        return {}

    def database(self):
        """
        Database Settings
        """
        return {}

    def ksms(self):
        """
        Key Store Modules
        """
        return {}

app = YubikeyKsm()
