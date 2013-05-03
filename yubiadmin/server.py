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
    cls = app.__class__
    doc = app.__doc__.strip()
    title, desc = doc.split('\n', 1)
    desc = desc.strip()
    sections = [{
        'name': section,
        'title': getattr(app, section).__doc__.strip(),
        'advanced': bool(getattr(getattr(app, section), 'advanced', False))
    } for section in cls.sections]

    return {
        'name': cls.name,
        'title': title,
        'description': desc,
        'sections': sections,
        'disabled': bool(getattr(app, 'disabled', False))
    }


class YubiAdmin(object):
    def __init__(self):
        self.apps = OrderedDict()
        for app in apps:
            app_data = inspect_app(app)
            self.apps[app_data['name']] = (app, app_data)
        self.modules = [data for (_, data) in self.apps.values()]

    @wsgify
    def __call__(self, request):
        module_name = request.path_info_pop()
        section_name = request.path_info_pop()

        if not module_name:
            return render('index', modules=self.modules)

        if not module_name in self.apps:
            raise exc.HTTPNotFound

        app, module = self.apps[module_name]
        if not section_name:
            section_name = module['sections'][0]['name']
            raise exc.HTTPSeeOther(location=request.path + '/' + section_name)

        if not hasattr(app, section_name):
            raise exc.HTTPNotFound

        section = next((section for section in module['sections']
                       if section['name'] == section_name), None)

        return render(
            'app_base',
            modules=self.modules,
            module=module,
            section=section,
            title='YubiAdmin - %s - %s' % (module_name, section_name),
            page=getattr(app, section_name)(request)
        )

application = YubiAdmin()
