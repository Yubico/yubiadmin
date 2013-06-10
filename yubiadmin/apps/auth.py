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
import requests
from wtforms import Form
from wtforms.fields import (SelectField, TextField, BooleanField, IntegerField,
                            PasswordField)
from wtforms.widgets import PasswordInput
from wtforms.validators import (NumberRange, URL, EqualTo, Regexp, Optional,
                                Email)
from yubiadmin.util.app import App, CollectionApp
from yubiadmin.util.system import invoke_rc_d
from yubiadmin.util.config import (python_handler, python_list_handler,
                                   FileConfig)
from yubiadmin.util.form import ConfigForm, FileForm, ListField
import logging as log
try:
    from yubiauth import YubiAuth
except:
    YubiAuth = None
User = None

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
YKVAL_DEFAULT_ID = 11004
YKVAL_DEFAULT_SECRET = '5Vm3Zp2mUTQHMo1DeG9tdojpc1Y='


auth_config = FileConfig(
    AUTH_CONFIG_FILE,
    [
        ('server_list', python_list_handler('YKVAL_SERVERS', YKVAL_SERVERS)),
        ('client_id', python_handler('YKVAL_CLIENT_ID', YKVAL_DEFAULT_ID)),
        ('client_secret', python_handler('YKVAL_CLIENT_SECRET',
                                         YKVAL_DEFAULT_SECRET)),
        ('auto_provision', python_handler('AUTO_PROVISION', True)),
        ('allow_empty', python_handler('ALLOW_EMPTY_PASSWORDS', False)),
        ('security_level', python_handler('SECURITY_LEVEL', 1)),
        ('yubikey_id', python_handler('YUBIKEY_IDENTIFICATION', False)),
        ('use_hsm', python_handler('USE_HSM', False)),
        ('hsm_device', python_handler('YHSM_DEVICE', 'yhsm://localhost:5348')),
        ('db_config', python_handler('DATABASE_CONFIGURATION',
                                     'sqlite:///:memory:')),
        ('user_registration', python_handler('ENABLE_USER_REGISTRATION',
                                             True)),
        ('user_deletion', python_handler('ALLOW_USER_DELETE', False)),
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
        When not checked, a user with no password will be unable to log in.
        """
    )
    user_registration = BooleanField(
        'Enable User Registration',
        description="""
        Allow users to register themselves using the YubiAuth client interface.
        """
    )
    user_deletion = BooleanField(
        'Enable User Deletion',
        description="""
        Allow users to delete their own account using the YubiAuth client
        interface.
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


class GetApiKeyForm(Form):
    legend = 'Get a YubiCloud API key'
    description = """
    To validate YubiKey OTPS against the YubiCloud, you need to get a free API
    key. You need to authenticate yourself using a Yubikey One-Time Password
    and provide your e-mail address as a reference.
    """
    email = TextField('E-mail address', [Email()])
    otp = TextField('YubiKey OTP', [Regexp(r'^[cbdefghijklnrtuv]{1,64}$')])
    attrs = {'otp': {'class': 'input-xxlarge'}}

    @staticmethod
    def extract_param(matches, predicate):
        while len(matches) > 0:
            elem = matches.pop(0)
            if predicate(elem):
                return elem

    def save(self):
        email = self.email.data
        otp = self.otp.data
        log.info('Attempting to register a new YubiCloud API key. '
                 'Email: %s, OTP: %s' % (email, otp))
        response = requests.post(
            'https://upgrade.yubico.com/getapikey/?format=json', data=
            {'email': email, 'otp': otp})
        data = response.json()
        if data['status']:
            log.info('Registered YubiCloud Client with ID: %d', data['id'])
            auth_config.read()
            auth_config['client_id'] = data['id']
            auth_config['client_secret'] = data['key']
            auth_config.commit()
        else:
            log.error('Failed registering new YubiCloud client: %s',
                      data['error'])
            raise Exception(data['error'])


class YubiAuthApp(App):
    """
    YubiAuth

    Web based configuration server.
    """

    name = 'auth'
    sections = ['general', 'database', 'validation', 'advanced']
    priority = 40

    @property
    def disabled(self):
        return not os.path.isfile(AUTH_CONFIG_FILE)

    @property
    def sections(self):
        if not YubiAuth:
            return ['general', 'database', 'validation', 'advanced']
        return ['general', 'database', 'validation', 'users', 'advanced']

    def general(self, request):
        return self.render_forms(request, [SecurityForm(), HSMForm()],
                                 template='auth/general')

    def reload(self, request):
        invoke_rc_d('apache2', 'reload')
        return self.redirect('/auth/general')

    def database(self, request):
        return self.render_forms(request, [DatabaseForm()])

    def validation(self, request):
        """
        Validation Server(s)
        """
        form = ValidationServerForm()
        resp = self.render_forms(request, [form])
        print 'Using: %s, %s' % (form.client_id.data, form.client_secret)
        if form.client_id.data == YKVAL_DEFAULT_ID and \
                form.client_secret.data == YKVAL_DEFAULT_SECRET:
            resp.data['alerts'].append(
                {
                    'type': 'warning',
                    'title': 'WARNING: Default Client ID used!<br />',
                    'message': 'As the default key is publically known, it is '
                    'not as secure as using a unique API key.\n'
                    '<a href="/auth/getapikey" class="btn btn-primary">'
                    'Generate unique API Key</a>'
                })
        return resp

    def getapikey(self, request):
        return self.render_forms(request, [GetApiKeyForm()], success_msg=
                                 "API Key registered!")

    def advanced(self, request):
        return self.render_forms(request, [
            FileForm(AUTH_CONFIG_FILE, 'Configuration', lang='python')
        ], script='editor')

    def users(self, request):
        """
        Manage Users
        """
        global User
        if User is None:
            from yubiauth.core.model import User as _user
            User = _user

        with YubiAuth() as auth:
            app = YubiAuthUsers(auth)
            return app(request).prerendered

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

    def save(self):
        with YubiAuth() as auth:
            auth.create_user(self.username.data, self.password.data)
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

    def __init__(self, user_id, **kwargs):
        super(SetPasswordForm, self).__init__(**kwargs)
        self.user_id = user_id

    def load(self):
        pass

    def save(self):
        if self.password.data:
            with YubiAuth() as auth:
                user = auth.get_user(self.user_id)
                user.set_password(self.password.data)
            self.password.data = None
            self.verify.data = None


class AssignYubiKeyForm(Form):
    legend = 'Assign YubiKey'
    assign = TextField('Assign YubiKey',
                       [Regexp(r'^[cbdefghijklnrtuv]{1,64}$'),
                           Optional()])

    def __init__(self, user_id, **kwargs):
        super(AssignYubiKeyForm, self).__init__(**kwargs)
        self.user_id = user_id

    def load(self):
        pass

    def save(self):
        if self.assign.data:
            with YubiAuth() as auth:
                user = auth.get_user(self.user_id)
                user.assign_yubikey(self.assign.data)
            self.assign.data = None


class YubiAuthUsers(CollectionApp):
    base_url = '/auth/users'
    item_name = 'Users'
    caption = 'YubiAuth Users'
    columns = ['Username', 'YubiKeys']
    template = 'auth/list'

    def __init__(self, auth):
        self.auth = auth

    def _size(self):
        return self.auth.session.query(User).count()

    def _get(self, offset=0, limit=None):
        users = self.auth.session.query(User).order_by(User.name) \
            .offset(offset).limit(limit)

        return map(lambda user: {
            'id': user.id,
            'label': user.name,
            'Username': '<a href="/auth/users/show/%d">%s</a>' % (user.id,
                                                                  user.name),
            'YubiKeys': ', '.join(user.yubikeys.keys())
        }, users)

    def _labels(self, ids):
        users = self.auth.session.query(User.name) \
            .filter(User.id.in_(map(int, ids))).all()
        return map(lambda x: x[0], users)

    def _delete(self, ids):
        self.auth.session.query(User) \
            .filter(User.id.in_(map(int, ids))).delete('fetch')

    def create(self, request):
        return self.render_forms(request, [CreateUserForm()],
                                 success_msg='User created!')

    def show(self, request):
        id = int(request.path_info_pop())
        user = self.auth.get_user(id)
        if 'unassign' in request.params:
            del user.yubikeys[request.params['unassign']]
        msg = None
        if request.params.get('password', None):
            msg = 'Password set!'
        elif request.params.get('assign', None):
            msg = 'YubiKey assigned!'
        elif request.params.get('unassign', None):
            msg = 'YubiKey unassigned!'
        return self.render_forms(request,
                                 [SetPasswordForm(user.id),
                                 AssignYubiKeyForm(user.id)],
                                 'auth/user', user=user.data,
                                 success_msg=msg)


app = YubiAuthApp()
