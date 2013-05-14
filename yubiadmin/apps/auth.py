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
from wtforms import Form
from wtforms.fields import (SelectField, TextField, BooleanField, IntegerField,
                            PasswordField)
from wtforms.widgets import PasswordInput
from wtforms.validators import NumberRange, URL, EqualTo, Regexp, Optional
from yubiadmin.util.app import App, render
from yubiadmin.util.config import (python_handler, python_list_handler,
                                   FileConfig)
from yubiadmin.util.form import ConfigForm, FileForm, ListField
try:
    from yubiauth import YubiAuth
    from yubiauth.core.model import User
except:
    YubiAuth = None

__all__ = [
    'app'
]

AUTH_CONFIG_FILE = '/etc/yubico/auth/yubiauth.conf'
YKVAL_SERVERS = [
    'https://api.yubico.com/wsapi/2.0/verify',
    'https://api2.yubico.com/wsapi/2.0/verify',
    'https://api3.yubico.com/wsapi/2.0/verify',
    'https://api4.yubico.com/wsapi/2.0/verify',
    'https://api5.yubico.com/wsapi/2.0/verify'
]


auth_config = FileConfig(
    AUTH_CONFIG_FILE,
    [
        ('server_list', python_list_handler('YKVAL_SERVERS', YKVAL_SERVERS)),
        ('client_id', python_handler('YKVAL_CLIENT_ID', 11004)),
        ('client_secret', python_handler('YKVAL_CLIENT_SECRET',
                                         '5Vm3Zp2mUTQHMo1DeG9tdojpc1Y=')),
        ('auto_provision', python_handler('AUTO_PROVISION', True)),
        ('allow_empty', python_handler('ALLOW_EMPTY_PASSWORDS', False)),
        ('security_level', python_handler('SECURITY_LEVEL', 1)),
        ('yubikey_id', python_handler('YUBIKEY_IDENTIFICATION', False)),
        ('use_hsm', python_handler('USE_HSM', False)),
        ('hsm_device', python_handler('YHSM_DEVICE', 'yhsm://localhost:5348')),
        ('db_config', python_handler('DATABASE_CONFIGURATION',
                                     'sqlite:///:memory:')),
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


class DatabaseForm(ConfigForm):
    legend = 'Database'
    description = 'Settings for connecting to the database'
    config = auth_config
    attrs = {'db_config': {'class': 'input-xxlarge'}}

    db_config = TextField(
        'Connection String',
        description="""
        SQLAlchemy connection string. For full details on syntax and supported
        database engines, see this section of the <a
        href="http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html"
        >SQLAlchemy documentation</a>.
        Example: <code>postgresql://yubiauth:password@localhost/yubiauth</code>
        """
    )


class ValidationServerForm(ConfigForm):
    legend = 'Validation Servers'
    description = 'Configure servers used for YubiKey OTP validation'
    config = auth_config
    attrs = {
        'client_secret': {'class': 'input-xxlarge'},
        'server_list': {'rows': 5, 'class': 'input-xxlarge'}
    }

    client_id = IntegerField('Client ID', [NumberRange(0)])
    client_secret = TextField('API key')
    server_list = ListField(
        'Validation Server URLs', [URL()],
        description="""
        List of URLs to YubiKey validation servers.
        Example: <code>http://example.com/wsapi/2.0/verify</code>
        """)


class YubiAuthApp(App):
    """
    YubiAuth

    Web based configuration server.
    """

    name = 'auth'
    sections = ['general', 'database', 'validation', 'advanced']
    disabled = not os.path.isfile(AUTH_CONFIG_FILE)

    def __init__(self):
        if YubiAuth:
            self._users = YubiAuthUsers()
            self.sections.insert(3, 'users')

    def general(self, request):
        """
        General
        """
        return self.render_forms(request, [SecurityForm(), HSMForm()])

    def database(self, request):
        """
        Database
        """
        return self.render_forms(request, [DatabaseForm()])

    def validation(self, request):
        """
        Validation Server(s)
        """
        return self.render_forms(request, [ValidationServerForm()])

    def advanced(self, request):
        """
        Advanced
        """
        return self.render_forms(request, [
            FileForm(AUTH_CONFIG_FILE, 'Configuration')
        ])

    def users(self, request):
        """
        Manage Users
        """
        return self._users(request) if YubiAuth else ""

    # Pulls the tab to the right:
    advanced.advanced = True


class CreateUserForm(Form):
    legend = 'Create new User'
    username = TextField('Username')
    password = PasswordField('Password',
                             widget=PasswordInput(hide_value=False))
    verify = PasswordField('Verify password',
                           [EqualTo('password')],
                           widget=PasswordInput(hide_value=False))

    def __init__(self, auth, **kwargs):
        super(CreateUserForm, self).__init__(**kwargs)
        self.auth = auth

    def load(self):
        pass

    def save(self):
        self.auth.create_user(self.username.data, self.password.data)
        self.auth.commit()
        self.username.data = None
        self.password.data = None
        self.verify.data = None


class SetPasswordForm(Form):
    legend = 'Change Password'
    password = PasswordField('New password',
                             [Optional()],
                             widget=PasswordInput(hide_value=False))
    verify = PasswordField('Verify password',
                           [EqualTo('password')],
                           widget=PasswordInput(hide_value=False))

    def __init__(self, user, auth, **kwargs):
        super(SetPasswordForm, self).__init__(**kwargs)
        self.user = user
        self.auth = auth

    def load(self):
        pass

    def save(self):
        if self.password.data:
            self.user.set_password(self.password.data)
            self.auth.commit()
            self.password.data = None
            self.verify.data = None


class AssignYubiKeyForm(Form):
    legend = 'Assign YubiKey'
    assign = TextField('Assign YubiKey',
                       [Regexp(r'^[cbdefghijklnrtuv]{1,64}$'),
                           Optional()])

    def __init__(self, user, auth, **kwargs):
        super(AssignYubiKeyForm, self).__init__(**kwargs)
        self.user = user
        self.auth = auth

    def load(self):
        pass

    def save(self):
        if self.assign.data:
            self.user.assign_yubikey(self.assign.data)
            self.assign.data = None
            self.auth.commit()


class YubiAuthUsers(App):
    user_range = re.compile('(\d+)-(\d+)')

    def __init__(self):
        self.auth = YubiAuth()

    def __call__(self, request):
        sub_cmd = request.path_info_pop()
        if sub_cmd == 'create':
            return self.create(request)
        elif sub_cmd == 'delete':
            return self.delete(request)
        elif sub_cmd == 'delete_confirm':
            return self.delete_confirm(request)
        elif sub_cmd == 'user':
            return self.show_user(request)
        else:
            match = self.user_range.match(sub_cmd) if sub_cmd else None
            if match:
                offset = int(match.group(1)) - 1
                limit = int(match.group(2)) - offset
            else:
                offset = 0
                limit = 10
        return self.list_users(offset, limit)

    def create(self, request):
        return self.render_forms(request, [CreateUserForm(self.auth)],
                                 success_msg='User created!')

    def delete(self, request):
        ids = [int(x[5:]) for x in request.params if request.params[x] == 'on']
        users = self.auth.session.query(User.name, User.id) \
            .filter(User.id.in_(ids)).all()
        return render('auth/delete', users=users)

    def delete_confirm(self, request):
        ids = [int(x) for x in request.params['delete'].split(',')]
        self.auth.session.query(User).filter(User.id.in_(ids)).delete('fetch')
        self.auth.commit()
        return self.redirect('/auth/users')

    def list_users(self, offset, limit):
        users = self.auth.session.query(User).order_by(User.name) \
            .offset(offset).limit(limit)
        num_users = self.auth.session.query(User).count()
        shown = (min(offset + 1, num_users), min(offset + limit, num_users))
        if offset > 0:
            st = max(0, offset - limit)
            ed = st + limit
            prev = '/auth/users/%d-%d' % (st + 1, ed)
        else:
            prev = None
        if num_users > shown[1]:
            next = '/auth/users/%d-%d' % (offset + limit + 1, shown[1] + limit)
        else:
            next = None

        return render(
            'auth/list', script='auth', users=users, offset=offset,
            limit=limit, num_users=num_users, shown='%d-%d' % shown, prev=prev,
            next=next)

    def show_user(self, request):
        id = int(request.path_info_pop())
        user = self.auth.get_user(id)
        if 'unassign' in request.params:
            del user.yubikeys[request.params['unassign']]
            self.auth.commit()
        msg = None
        if 'password' in request.params:
            msg = 'Password set!'
        return self.render_forms(request,
                                 [SetPasswordForm(user, self.auth),
                                 AssignYubiKeyForm(user, self.auth)],
                                 'auth/user', user=user,
                                 success_msg=msg)


app = YubiAuthApp()
