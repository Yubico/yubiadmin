__all__ = [
    'app'
]


class YubikeyVal(object):
    """
    YubiKey Validation server

    YubiKey OTP validation server
    """

    name = 'val'
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

app = YubikeyVal()
