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

from yubiadmin.util.app import App, render
from yubiadmin.util.system import run
from wtforms import Form
from wtforms.fields import TextField, PasswordField
import os

__all__ = [
    'app'
]

CLIENTS_CONFIG_FILE = '/etc/freeradius/clients.conf'


class RadTestForm(Form):
    legend = 'RADIUS test'
    username = TextField('Username')
    password = PasswordField('Password')


class FreeRadius(App):
    """
    FreeRADIUS

    RADIUS Server
    """

    name = 'freerad'
    sections = ['general', 'clients']

    @property
    def disabled(self):
        return not os.path.isdir('/etc/freeradius')

    def general(self, request):
        """
        General
        """
        alerts = []
        if 'username' in request.params:
            username = request.params['username']
            password = request.params.get('password', '')
            cmd = 'radtest %s %s localhost 0 testing123' % (username, password)
            status, output = run(cmd)
            alert = {'title': cmd, 'message': '<pre>%s</pre>' % output}
            if status == 0:
                alert['type'] = 'success'
            elif status == 1:
                alert['type'] = 'warn'
            else:
                alert['type'] = 'error'
                alert['message'] = 'There was an error running the command. ' \
                    'Exit code: %d' % status
            alerts.append(alert)

        return render('freerad/general', form=RadTestForm(), alerts=alerts)

    def clients(self, request):
        """
        RADIUS clients
        """
        return ''

app = FreeRadius()
