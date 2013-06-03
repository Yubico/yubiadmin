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

import os
import subprocess
from webob import Response
from threading import Timer
from yubiadmin.util.app import App, render
from yubiadmin.util.system import run

__all__ = [
    'app'
]


def get_updates():
    s, o = run("apt-get upgrade -s | awk -F'[][() ]+' '/^Inst/{print $2}'")
    packages = o.splitlines()
    return packages


def needs_restart():
    return os.path.isfile('/var/run/reboot-required')


def reboot():
    run('reboot')


class Updater(object):
    def __init__(self):
        self.proc = subprocess.Popen(['apt-get', '-y', 'dist-upgrade'],
                                     stdout=subprocess.PIPE)

    def __iter__(self):
        yield '<strong>Performing update, this may take a while...</strong>' \
            '<br/>'
        while True:
            line = self.proc.stdout.readline()
            if line:
                yield line + '<br />'
            else:
                yield '<br /><strong>Update complete!</strong>'
                yield '<script type="text/javascript">' \
                    'window.location.replace("/sys");</script>'
                break


class SystemApp(App):
    """
    YubiX System
    """
    sections = ['general']
    priority = 30

    @property
    def disabled(self):
        return not os.path.isdir('/usr/share/yubix')

    @property
    def hidden(self):
        return self.disabled

    def general(self, request):
        alerts = []
        if needs_restart():
            alerts.append({'message': 'The machine needs to reboot.',
                           'type': 'error'})
        return render('/sys/general', alerts=alerts, updates=get_updates())

    def update(self, request):
        if get_updates():
            return Response(app_iter=Updater())
        else:
            alerts = [{'message': 'Software is up to date!'}]
            return render('/sys/general', alerts=alerts)

    def reboot(self, request):
        if 'now' in request.params:
            run('reboot')
        else:
            timer = Timer(1, run, args=('reboot',))
            timer.start()
        alerts = [{'type': 'warn', 'message': 'Rebooting System...'}]
        return self.render('/sys/general', alerts=alerts)


app = SystemApp()
