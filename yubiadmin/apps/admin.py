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

from threading import Timer
from wtforms.fields import IntegerField, TextField, PasswordField
from wtforms.widgets import PasswordInput
from wtforms.validators import NumberRange, IPAddress
from yubiadmin.util.app import App
from yubiadmin.util.config import python_handler, FileConfig
from yubiadmin.util.form import ConfigForm
from yubiadmin.util.system import invoke_rc_d

__all__ = [
    'app'
]


admin_config = FileConfig(
    '/etc/yubico/admin/yubiadmin.conf',
    [
        ('interface', python_handler('INTERFACE', '127.0.0.1')),
        ('port', python_handler('PORT', 8080)),
        ('username', python_handler('USERNAME', 'yubiadmin')),
        ('password', python_handler('PASSWORD', 'yubiadmin')),
    ]
)


class ConnectionForm(ConfigForm):
    legend = 'Connection'
    description = 'Server network interface settings'
    config = admin_config

    interface = TextField('Listening Interface', [IPAddress()])
    port = IntegerField('Listening Port', [NumberRange(1, 65535)])


class CredentialsForm(ConfigForm):
    legend = 'Credentials'
    description = 'Credentials for accessing YubiAdmin'
    config = admin_config

    username = TextField('Username', [])
    password = PasswordField('Password',
                             widget=PasswordInput(hide_value=False))


class YubiAdmin(App):
    """
    YubiAdmin

    Web based configuration server.
    """

    name = 'admin'
    priority = 10
    sections = ['general']

    def general(self, request):
        return self.render_forms(request,
                                 [ConnectionForm(), CredentialsForm()],
                                 template='admin/general')

    def restart(self, request):
        if 'now' in request.params:
            invoke_rc_d('yubiadmin', 'restart')
        else:
            timer = Timer(1, invoke_rc_d, args=('yubiadmin', 'restart'))
            timer.start()
        return self.redirect('/%s/general' % self.name)


app = YubiAdmin()
