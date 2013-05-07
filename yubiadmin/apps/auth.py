# Copyright (c) 2013 Yubico AB
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from wtforms.fields import SelectField, TextField, PasswordField, BooleanField
from wtforms.widgets import PasswordInput
from wtforms.validators import NumberRange, IPAddress
from yubiadmin.util.app import App
from yubiadmin.util.config import python_handler, FileConfig
from yubiadmin.util.form import ConfigForm, FileForm

__all__ = [
    'app'
]

AUTH_CONFIG_FILE = '/etc/yubico/auth/yubiauth.conf'


auth_config = FileConfig(
    AUTH_CONFIG_FILE,
    [
        ('client_id', python_handler('YKVAL_CLIENT_ID', 11004)),
        ('client_secret', python_handler('YKVAL_CLIENT_SECRET',
                                         '5Vm3Zp2mUTQHMo1DeG9tdojpc1Y=')),
        ('auto_provision', python_handler('AUTO_PROVISION', True)),
        ('allow_empty', python_handler('ALLOW_EMPTY_PASSWORDS', False)),
        ('security_level', python_handler('SECURITY_LEVEL', 1)),
        ('yubikey_id', python_handler('YUBIKEY_IDENTIFICATION', False)),
        ('use_hsm', python_handler('USE_HSM', False)),
        ('hsm_device', python_handler('YHSM_DEVICE', 'yhsm://localhost:5348')),
    ]
)


class SecurityForm(ConfigForm):
    legend = 'Security'
    description = 'Security Settings for YubiAuth'
    config = auth_config

    auto_provision = BooleanField(
        'Auto Provision YubiKeys',
        description="""
        When enabled, an attempt to authenticate a user that doesn't have a
        YubiKey assigned with a valid YubiKey OTP, will cause that YubiKey to
        become automatically assigned to the user.
        """
    )
    yubikey_id = BooleanField(
        'Allow YubiKey Identification',
        description="""
        Allow users to authenticate using their YubiKey as identification,
        omitting the username.
        """
    )
    allow_empty = BooleanField(
        'Allow Empty Passwords',
        description="""
        Allow users with no password to log in without providing a password.
        When set to False, a user with no password will be unable to log in.
        """
    )
    security_level = SelectField(
        'Security Level',
        coerce=int,
        choices=[(0, 'Never'), (1, 'When Provisioned'), (2, 'Always')],
        description="""
        Defines who is required to provide a YubiKey OTP when logging in.
        The available levels are:
        Never - OTPs are not required to authenticate, by anyone.

        When Provisioned - OTPs are required by all users that have a
        YubiKey assigned to them.

        Always - OTPs are required by all users. If no YubiKey has been
        assigned, that user cannot log in, unless auto-provisioning is enabled.
        """
    )


class HSMForm(ConfigForm):
    legend = 'YubiHSM'
    description = 'Settings for the YubiHSM hardware device'
    config = auth_config

    use_hsm = BooleanField(
        'Use a YubiHSM',
        description='Check this if you have a YubiHSM to be used by YubiAuth.'
    )
    hsm_device = TextField('YubiHSM device')


class YubiAuth(App):
    """
    YubiAuth

    Web based configuration server.
    """

    name = 'auth'
    sections = ['general', 'advanced']

    def general(self, request):
        """
        General
        """
        return self.render_forms(request, [SecurityForm(), HSMForm()])

    def advanced(self, request):
        """
        Advanced
        """
        return self.render_forms(request, [
            FileForm(AUTH_CONFIG_FILE, 'Configuration')
        ])

    # Pulls the tab to the right:
    advanced.advanced = True


app = YubiAuth()
