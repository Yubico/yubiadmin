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
import re
from jinja2 import Environment, FileSystemLoader
from webob import exc
from webob.dec import wsgify

__all__ = [
    'App',
    'CollectionApp',
    'render',
    'populate_forms',
]

cwd = os.path.dirname(__file__)
base_dir = os.path.abspath(os.path.join(cwd, os.pardir))
template_dir = os.path.join(base_dir, 'templates')
env = Environment(loader=FileSystemLoader(template_dir))


class TemplateBinding(object):
    def __init__(self, template, **kwargs):
        self.template = env.get_template('%s.html' % template)
        self.data = kwargs
        for (key, val) in kwargs.items():
            if isinstance(val, TemplateBinding):
                self.data.update(val.data)

    def extend(self, sub_variable, sub_binding):
        self.data.update(sub_binding.data)
        self.data[sub_variable] = sub_binding

    def __str__(self):
        return self.template.render(self.data)

    @wsgify
    def __call__(self, request):
        return str(self)


def render(tmpl, **kwargs):
    return TemplateBinding(tmpl, **kwargs)


def populate_forms(forms, data):
    if not data:
        for form in forms:
            form.load()
    else:
        errors = False
        for form in forms:
            form.process(data)
            errors = not form.validate() or errors
        if not errors:
            for form in forms:
                form.save()


class App(object):
    name = None
    sections = []
    priority = 50

    def redirect(self, url):
        raise exc.HTTPSeeOther(location=url)

    def render_forms(self, request, forms, template='form',
                     success_msg='Settings updated!', **kwargs):
        alert = None
        if not request.params:
            for form in forms:
                form.load()
        else:
            errors = False
            for form in forms:
                form.process(request.params)
                errors = not form.validate() or errors
            if not errors:
                try:
                    if success_msg:
                        alert = {'type': 'success', 'title': success_msg}
                    for form in forms:
                        form.save()
                except Exception as e:
                    alert = {'type': 'error', 'title': 'Error:',
                             'message': str(e)}
            else:
                alert = {'type': 'error', 'title': 'Invalid data!'}

        return render(template, target=request.path, fieldsets=forms,
                      alert=alert, **kwargs)


ITEM_RANGE = re.compile('(\d+)-(\d+)')


class CollectionApp(App):
    base_url = ''
    caption = 'Items'
    item_name = 'Items'
    columns = []
    template = 'table'
    script = 'table'
    selectable = True

    def _size(self):
        return 0

    def _get(self, offset=0, limit=None):
        return [{}]

    def _select(self, ids):
        return [x for x in self._get() if x['id'] in ids]

    def _delete(self, ids):
        raise Exception('Not implemented!')

    def __call__(self, request):
        sub_cmd = request.path_info_pop()
        if sub_cmd and not sub_cmd.startswith('_') and hasattr(self, sub_cmd):
            return getattr(self, sub_cmd)(request)
        else:
            match = ITEM_RANGE.match(sub_cmd) if sub_cmd else None
            if match:
                offset = int(match.group(1)) - 1
                limit = int(match.group(2)) - offset
            else:
                offset = 0
                limit = 10
        return self.list(offset, limit)

    def list(self, offset, limit):
        items = self._get(offset, limit)
        total = self._size()
        shown = (min(offset + 1, total), min(offset + limit, total))
        if offset > 0:
            st = max(0, offset - limit)
            ed = st + limit
            prev = '%s/%d-%d' % (self.base_url, st + 1, ed)
        else:
            prev = None
        if total > shown[1]:
            next = '%s/%d-%d' % (self.base_url, offset + limit + 1, shown[1]
                                 + limit)
        else:
            next = None

        return render(
            self.template, script=self.script, items=items, offset=offset,
            limit=limit, total=total, shown='%d-%d' % shown, prev=prev,
            next=next, base_url=self.base_url, caption=self.caption,
            cols=self.columns, item_name=self.item_name,
            selectable=self.selectable)

    def delete(self, request):
        ids = [x[5:] for x in request.params if request.params[x] == 'on']
        items = self._select(ids)
        return render('table_delete', ids=','.join(ids), items=items,
                      item_name=self.item_name, base_url=self.base_url)

    def delete_confirm(self, request):
        self._delete(request.params['delete'].split(','))
        return self.redirect(self.base_url)
