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

from webob import exc
from webob.dec import wsgify
from collections import OrderedDict
from yubiadmin.util.app import render
from yubiadmin.apps import apps


def inspect_app(app):
    if app.__doc__:
        doc = app.__doc__.strip()
        if '\n' in doc:
            title, desc = doc.split('\n', 1)
            desc = desc.strip()
        else:
            title = desc = doc
    else:
        title = desc = app.__class__.__name__

    return {
        'name': app.name,
        'title': title,
        'description': desc,
        'disabled': bool(getattr(app, 'disabled', False)),
        'hidden': bool(getattr(app, 'hidden', False))
    }


class YubiAdmin(object):
    @wsgify
    def __call__(self, request):
        module_name = request.path_info_pop()

        apps_data = OrderedDict()
        for app in apps:
            app_data = inspect_app(app)
            apps_data[app_data['name']] = (app, app_data)
        modules = [data for (_, data) in apps_data.values()]

        if not module_name:
            module_name = 'dashboard'

        if not module_name in apps_data:
            raise exc.HTTPNotFound

        app, module = apps_data[module_name]

        if module['disabled']:
            raise exc.HTTPNotFound

        request.environ['yubiadmin.response'] = render(
            'content',
            modules=modules,
            module=module,
            title='YubiAdmin - %s' % module_name
        )

        resp = app(request)
        if not resp:
            return request.environ['yubiadmin.response']
        return resp

application = YubiAdmin()
