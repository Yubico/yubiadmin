from wtforms import Form
from wtforms.fields import StringField, IntegerField
from wtforms.validators import NumberRange

__all__ = [
    'app'
]


class MiscForm(Form):
    legend = 'Misc'
    default_timeout = IntegerField('Default Timeout', [NumberRange(0)],
                                   default=1)

    def load(self):
        self.default_timeout.process_data(5)

    def save(self):
        pass


class SyncLevelsForm(Form):
    legend = 'Sync Levels'
    sync_default = IntegerField('Default', [NumberRange(1, 100)], default=60)
    sync_secure = IntegerField('Secure', [NumberRange(1, 100)], default=40)
    sync_fast = IntegerField('Fast', [NumberRange(1, 100)], default=1)

    def load(self):
        # TODO: Read config file
        self.sync_default.process_data(40)
        self.sync_secure.process_data(51)
        self.sync_fast.process_data(1)

    def save(self):
        # TODO: Save data t config file
        pass


class DatabaseForm(Form):
    legend = 'Database'
    connection_string = StringField('Connection String', default=1)
    attrs = {'connection_string': {'class': 'input-xxlarge'}}

    def load(self):
        self.connection_string.process_data(
            'mysql:dbname=ykval;host=127.0.0.1')

    def save(self):
        pass


class YubikeyVal(object):
    """
    YubiKey Validation Server

    YubiKey OTP validation server
    """

    name = 'val'
    sections = ['general', 'database', 'syncpool', 'ksms']

    def _populate_forms(self, forms, data):
        if not data:
            for form in forms:
                form.load()
        else:
            errors = False
            for form in forms:
                form.process(data)
                errors = form.validate() or errors
            if not errors:
                for form in forms:
                    form.save()

    def general(self, request):
        """
        General
        """
        forms = [
            SyncLevelsForm(),
            MiscForm()
        ]

        self._populate_forms(forms, request.params)

        return {'fieldsets': forms}

    def database(self, request):
        """
        Database Settings
        """
        forms = [DatabaseForm()]

        self._populate_forms(forms, request.params)

        return {'fieldsets': forms}

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
