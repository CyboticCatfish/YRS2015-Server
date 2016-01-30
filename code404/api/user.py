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

import re
import pymongo
import time
from hashlib import sha256
from flask import request
from binascii import b2a_hex, a2b_hex
from os import urandom, mkdir


from . import db, get_arg, get_header, make_error, make_status
from .. import app
from ..error import InvalidLogin, MissingInformation, InvalidInformation, NoUser

users = db["users"]
users.create_index("username", unique=True)


def get_user():
    try:
        user_id = int(get_arg("user_id"))
    except:
        raise InvalidUser()

    user_name = get_arg("user_name")


    if user_id is None and user_name is None:
        raise NoUser()
    elif user_id is not None:
        res = users.find_one({"id": user_id})
        return res
    elif user_name is not None:
        res = users.find_one({"name": user_name})
        return res

def get_user_from_id(user_id):
    res = users.find_one({"id": user_id})
    return res


def get_user_from_token(token=None):
    if token is None:
        token = get_header("token")
        if token is None:
            token = request.form["token"]
            if token is None:
                raise MissingInformation("token")

    token_bin = a2b_hex(token)
    res = users.find_one({
        "tokens.code": token,
        "tokens.expires": {
            "$lt": time.time()
        }
    })

    return res


def hash_password(password, salt):
    hasher = sha256()
    hasher.update(password.encode("utf8"))
    hasher.update(salt)
    pass_hash = hasher.digest()
    return pass_hash


def gen_pass_hash(password):
    salt = urandom(16)
    return {
        "hash": hash_password(password, salt),
        "salt": salt
    }


def login(username, password):
    user = users.find_one({
        "username": username.lower()
    })

    if user:
        pass_hash = hash_password(password, user["salt"])
        if pass_hash == user["pass_hash"]:
            return user

    raise InvalidLogin()


def make_token(username, valid_time=(60*60*24*30)):
    username = username.lower()

    hasher = sha256()
    hasher.update(urandom(32))
    token = hasher.digest()

    expire = time.time() + valid_time

    users.update({"login": username}, {"$push": {"tokens": {"code": token, "expires": expire}}})

    return token

def create_user(username, display_name, password, public):
    # check login is valid
    username = username.lower()

    # max 15 chars
    if len(username) > 32:
        raise InvalidInformation("username", "Must be less than 32 characters.")

    # alphanumerics only
    if re.match("[^a-z0-9]", username):
        raise InvalidInformation("username", "Can only contain alphanumeric characters")

    # check screen name is valid
    if len(display_name) > 32:
        raise InvalidInformation("display_name", "Must be less than 32 characters")

    # check password is valid
    if len(password) > 1024:
        raise InvalidInformation("password", "Must be less than 1024 characters")

    # check public is valid
    if public == "on":
        public = 1
    else:
        public = 0

    # hash dat pass
    hash_salt = gen_pass_hash(password)
    pass_hash = hash_salt["hash"]
    salt = hash_salt["salt"]

    # push to DB
    try:
        res = users.insert({
            "username": username,
            "display_name": display_name,
            "salt": salt,
            "pass_hash": pass_hash,
            "public": public,
            "subscriptions": [],
            "tokens": []
        })
    except pymongo.errors.DuplicateKeyError as e:
        print(e)
        raise Exception("Multiple users")

    try:
        mkdir("/".join(("level", str(username))))
    except FileExistsError as e:
        pass  # This shouldn't happen, but it happens a lot while debugging.

    return make_status("success", "User created")

@app.route("/user/create", methods=["POST"])
def api_create_user():
    try:
        username = request.form["username"]
        display_name = request.form["display_name"]
        password = request.form["password"]
        public = request.form["public"]

        if username is None:
            raise MissingInformation("username")
        if name is None:
            raise MissingInformation("name")
        if password is None:
            raise MissingInformation("password")

    except MissingInformation as e:
        return make_error(e.message)

    try:
        create_user(username, display_name, password, public)
        return make_status("success", "User created")
    except Exception as e:
        return make_error(e.message)



@app.route("/user/login", methods=["POST"])
def get_token():
    try:
        username = request.form["username"]
        password = request.form["password"]
        if username is None:
            raise MissingInformation("username")
        if password is None:
            raise MissingInformation("password")
    except MissingInformation as e:
        return make_error(e.message)

    user = login(username, password)
    token = make_token(user)
    token_hex = b2a_hex(token)

    return make_status("success", "Logged in", data={"token": token_hex})


@app.route("/user/subscriptions", methods=["GET", "POST"])
def get_subscriptions():
    try:
        token = get_header("token")
    except MissingInformation as e:
        return make_error(e.message)

    try:
        user = get_user_from_token(token)
    except InvalidInformation as e:
        return make_error(e.message)

    x = ",".join(user["subscriptions"])
    return x
