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

from distutils.core import Command
from distutils.errors import DistutilsSetupError
import os
import re
from datetime import date


class release(Command):
    description = "create and release a new version"
    user_options = [
        ('keyid', None, "GPG key to sign with"),
        ('skip-tests', None, "skip running the tests"),
    ]
    boolean_options = ['skip-tests']

    def initialize_options(self):
        self.keyid = None
        self.skip_tests = 0

    def finalize_options(self):
        self.cwd = os.getcwd()
        self.fullname = self.distribution.get_fullname()

    def _verify_version(self):
        version = self.distribution.get_version()
        with open('NEWS', 'r') as news_file:
            line = news_file.readline()
        now = date.today().strftime('%Y-%m-%d')
        if not re.search(r'Version %s \(released %s\)' % (version, now), line):
            raise DistutilsSetupError("Incorrect date/version in NEWS!")

    def _verify_tag(self):
        if os.system('git tag | grep -q "^%s\$"' % self.fullname) == 0:
            raise DistutilsSetupError(
                "Tag '%s' already exists!" % self.fullname)

    def _sign(self):
        sign_opts = ['--detach-sign', 'dist/%s.tar.gz' % self.fullname]
        if self.keyid:
            sign_opts.insert(1, '--default-key ' + self.keyid)
        self.execute(os.system, ('gpg ' + (' '.join(sign_opts)),))

        if os.system('gpg --verify dist/%s.tar.gz.sig' % self.fullname) != 0:
            raise DistutilsSetupError("Error verifying signature!")

    def _tag(self):
        tag_opts = ['-s', '-m ' + self.fullname, self.fullname]
        if self.keyid:
            tag_opts[0] = '-u ' + self.keyid
        self.execute(os.system, ('git tag ' + (' '.join(tag_opts)),))

    def run(self):
        if os.getcwd() != self.cwd:
            raise DistutilsSetupError("Must be in package root!")

        self._verify_version()
        self._verify_tag()

        self.execute(os.system, ('git2cl > ChangeLog',))

        if not self.skip_tests:
            self.run_command('check')
            self.run_command('test')

        self.run_command('sdist')  # upload --sign --identity keyid

        self._sign()
        self._tag()
