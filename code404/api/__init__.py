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

from pymongo import MongoClient
from flask import jsonify

db_client = MongoClient()

db = db_client["code404"]

def get_arg(name):
    try:
        return request.args.get(name)
    except IndexError:
        return None


def get_header(name):
    try:
        return request.headers[name]
    except KeyError:
        return None


def escape_xml(text):
    return text.replace("<", "&lt;").replace(">", "&gt;")


def make_status(status, message, data=None):
    response = jsonify({
        "status": status,
        "message": message,
        "data": data
    })
    return response


def make_error(message, code=400):
    return make_response(make_status("failed", message), code)


from . import (
    level,
    user
)
