# Code404_Server - The serverside stuff and site for Code404_Server
# Copyright (C) 2015 Mitame, Doctor_N
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class NoUser(BaseException):
    message = "No user was specified"

    def __init__(self):
        BaseException.__init__(self)


class InvalidUser(BaseException):
    message = "User was not valid"

    def __init__(self):
        BaseException.__init__(self)


class MissingInformation(BaseException):

    def __init__(self, field_name):
        BaseException.__init__(self)
        self.message = "Missing field '%s'." % field_name


class InvalidInformation(BaseException):

    def __init__(self, field_name, reason):
        BaseException.__init__(self)
        self.message = "Field '%s' is invalid: '%s'" %(field_name, reason)

class InvalidLogin(BaseException):
    message = "Username and password did not match"
