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

from yubiadmin.util.app import App, CollectionApp, render
from yubiadmin.util.system import run, invoke_rc_d
from yubiadmin.util.form import FileForm
from yubiadmin.util.config import parse_block
from yubiadmin.apps.dashboard import panel
from wtforms import Form
from wtforms.fields import TextField
import os
import re

__all__ = [
    'app'
]

CLIENTS_CONFIG_FILE = '/etc/freeradius/clients.conf'


def is_freerad_running():
    status, _ = run('cat /var/run/freeradius/freeradius.pid | xargs kill -0')
    return status == 0


class RadTestForm(Form):
    legend = 'RADIUS test'
    description = """
    This utility allows you to test authentication against the RADIUS server
    using the credentials entered below. By default there will be a client with
    the client secret: testing123, though you can change this under the RADIUS
    Clients tab.
    """
    client_secret = TextField('Client Secret', default='testing123')
    username = TextField('Username')
    password = TextField('Password')


class FreeRadius(App):
    """
    FreeRADIUS

    RADIUS Server
    """

    name = 'freerad'
    sections = ['general', 'clients']
    priority = 60

    @property
    def disabled(self):
        return not os.path.isdir('/etc/freeradius')

    @property
    def dash_panels(self):
        running = is_freerad_running()
        yield panel('FreeRADIUS',
                    'FreeRadius server is %s' %
                    ('running' if running else 'stopped'),
                    '/%s/general' % self.name,
                    'success' if running else 'danger')

    def __init__(self):
        self._clients = RadiusClients()

    def general(self, request):
        alerts = []
        form = RadTestForm()

        if 'username' in request.params:
            form.process(request.params)
            username = form.username.data
            password = form.password.data
            secret = form.client_secret.data

            cmd = 'radtest %s %s localhost 0 %s' % (username, password, secret)
            status, output = run(cmd)
            alert = {'title': 'Command: %s' % cmd}
            alert['message'] = '<pre style="white-space: pre-wrap;">%s</pre>' \
                % output
            if status == 0:
                alert['type'] = 'success'
            elif status == 1:
                alert['type'] = 'warn'
            else:
                alert['type'] = 'error'
                alert['message'] = 'There was an error running the command. ' \
                    'Exit code: %d' % status
            alerts.append(alert)

        return render('freerad/general', form=form, alerts=alerts,
                      running=is_freerad_running())

    def _unused_clients(self, request):
        """
        RADIUS clients
        """
        return self._clients(request)

    def server(self, request):
        if request.params['server'] == 'toggle':
            if is_freerad_running():
                invoke_rc_d('freeradius', 'stop')
            else:
                invoke_rc_d('freeradius', 'start')
        else:
            invoke_rc_d('freeradius', 'restart')

        return self.redirect('/%s/general' % self.name)

    def clients(self, request):
        """
        RADIUS Clients
        """
        return self.render_forms(request, [
            FileForm(CLIENTS_CONFIG_FILE, 'clients.conf',
                     'Changes require the FreeRADIUS server to be restarted.',
                     lang='ini')
        ], script='editor')


CLIENT = re.compile('client\s+(.+)\s+{')
ATTRIBUTE = re.compile('([^\s]+)\s+=\s+([^\s]+)')


def parse_client(name, content):
    data = {}
    for line in content.splitlines():
        line = line.split('#', 1)[0].strip()
        match = ATTRIBUTE.match(line)
        if match:
            key = match.group(1)
            value = match.group(2)
            data[key] = value
    client = {
        'Name': name or data.get('shortname', data.get('ipaddr')),
        'data': data,
        'Attributes': ', '.join(['%s=%s' % (k, v) for (k, v) in data.items()])
    }
    return client


def parse_clients(content):
    lines = content.splitlines()
    index = 0
    skip = 0
    for line in lines:
        if skip > 0:
            skip -= 1
            continue

        match = CLIENT.match(line.strip())
        if match:
            name = match.group(1)
            c_content = parse_block('\n'.join(lines[index + 1:]), '{', '}')
            client = parse_client(name, c_content)
            skip = len(c_content.splitlines())
            client['id'] = index
            client['start'] = index
            client['end'] = index + skip + 2
            index += skip
            yield client

        index += 1


class RadiusClients(CollectionApp):
    base_url = '/freerad/clients'
    item_name = 'Clients'
    caption = 'RADIUS Clients'
    columns = ['Name', 'Attributes']
    template = 'freerad/client_list'

    def _get(self, offset=0, limit=None):
        with open(CLIENTS_CONFIG_FILE, 'r') as f:
            self.content = f.read()

        clients = list(parse_clients(self.content))
        if limit:
            limit += offset
        return clients[offset:limit]

    def _delete(self, ids):
        ids = map(int, ids)
        clients = filter(lambda x: x['id'] in ids, self._get())
        lines = self.content.splitlines()

        for client in reversed(clients):
            del lines[client['start']:client['end']]

        with open(CLIENTS_CONFIG_FILE, 'w') as f:
            f.write(os.linesep.join(lines))

app = FreeRadius()
