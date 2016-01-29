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

from . import app
from .error import MissingInformation, InvalidLogin, InvalidUser, InvalidInformation, NoUser
from .database import users, levels

from flask import request
from hashlib import sha256
from os import urandom, _exists, mkdir
from binascii import b2a_hex, a2b_hex
# from io import BytesIO
import re
import random
import time

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


def escape_xml(text):
    return text.replace("<", "&lt;").replace(">", "&gt;")


def make_status(status, message, data=None):
    response = "<?xml version='1.0'?>"
    response += "<response status='%s'>" % status
    response += "<message>"
    response += escape_xml(message)
    response += "</message>"
    if data:
        response += "<data>" + str(data) + "</data>"
    response += "</response>"
    return response


def make_error(message):
    # return make_response(make_status("failed", message), 500)
    print(message)
    return "undefined"


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

def login(username, password):
    res = users.find_one({
        "login": username.lower()
    })

    hasher = sha256()
    hasher.update(password.encode("utf8"))
    hasher.update(res["salt"])
    pass_hash = hasher.hexdigest()

    if pass_hash == res["pass_hash"]:
        return res
    else:
        return None


@app.route("/level/get", methods=["GET"])
def get_level():
    # get arguments
    try:
        level_id = get_arg("id")

        if level_id is None:
            raise MissingInformation("id")
    except MissingInformation as e:
        return make_error(e.message)

    # check arguments
    try:
        try:
            level_id = int(level_id)
        except ValueError:
            raise InvalidInformation("id", "Not an integer.")
    except InvalidInformation as e:
        return make_error(e.message)

    # perform query
    res = levels.find_one({"id": level_id})
    if res is None:
        make_error(InvalidInformation("id", "No level exists with this ID").message)
    else:
        return open("levels/%s/%s-%s.lvl" % (row[0], row[2], row[1])).read()

@app.route("/level/subscribe", methods=["POST"])
def subscribe_to_level():
    try:
        token = request.form["token"]
        level_id = request.form["id"]

        if token is None:
            raise MissingInformation("token")
        if level_id is None:
            raise MissingInformation("id")
    except MissingInformation as e:
        return make_error(e.message)

    try:
        user = get_user_from_token(token)
    except InvalidInformation as e:
        return make_error(e.message)

    users.update_one(
        {"_id": user["_id"]},
        {"$push": {"subscriptions": level_id}}
    )

    return make_status("success", "Subscribed to level")



@app.route("/level/submit", methods=["POST"])
def upload_level():
    try:
        user = get_user_from_token()
    except MissingInformation as e:
        return make_error(e.message)
    except InvalidInformation as e:
        return make_error(e.message)
    try:
        name = request.form["level-name"]
        public = request.form["public"]

        if name is None:
            raise MissingInformation("level-name")
        elif re.match("/|^\.\.?", name):
            raise InvalidInformation("level-name", "Contains banned character sequences")

        if public is None:
            public = True
        else:
            try:
                public = bool(int(public))
            except ValueError:
                if public == "on":
                    public = True
                elif public == "off":
                    public = False
                else:
                    raise InvalidInformation("public", "Not a number.")
    except MissingInformation as e:
        return make_error(e.message)
    except InvalidInformation as e:
        return make_error(e.message)

    timestamp = time.time()

    f = request.files["level"]
    f.save("levels/%s/%s-%s.lvl" % (user["login"], name, str(timestamp)))

    f = request.files["image"]
    f.save("levels/%s/%s-%s.png" % (user["login"], name, str(timestamp)))

    level_id = levels.insert_one({
        "creator": user["login"],
        "name": name,
        "timestamp": timestamp,
        "public": public
    })

    if level_id is None:
        return make_error(level_id)

    users.update(user, {"$push": {"subscriptions": level_id}})

    return make_status("success", "Level saved.", str(level_id))


@app.route("/level/get/details", methods=["GET"])
def get_level_details():
    try:
        level_id = get_arg("id")
        if level_id is None:
            raise MissingInformation("id")
    except MissingInformation as e:
        return make_error(e.message)

    try:
        try:
            level_id = int(level_id)
        except ValueError:
            raise InvalidInformation("id", "Must be integer")
    except InvalidInformation as e:
        return make_error(e.message)

    level = levels.find_one({"_id": level_id})
    creator = users.find_one({"login": creator})

    x = ",".join((level["name"], user["name"]))
    return x


@app.route("/level/get/image", methods=["GET"])
def get_level_image():
    try:
        level_id = get_arg("id")
        size = (int(get_arg("x")), int(get_arg("y")))

        if level_id is None:
            raise MissingInformation("id")

        level = levels.find_one({"_id": id})
        if level is None:
            raise InvalidInformation("id", "level not found")


        imagepath = "levels/%s/%s-%s.png" % (level["creator"], level["name"], str(level["timestamp"]))

        if not _exists(imagepath):
            imagepath = "static/images/logo.png"

        if any(x is None for x in size):
            cropped = open(imagepath).read()

        else:
            cropped = get_and_crop(imagepath, size)
            cropped = surf_to_string(cropped)

        return make_response(
            cropped,
            200,
            {"Content-type": "image/png"}
        )
    except InvalidInformation as e:
        return make_error(e.message)
    except MissingInformation as e:
        return make_error(e.message)

# # DOESN'T DO WHAT IT SAYS IT DOES [STOP]
# # DO NOT TRUST [STOP]
# # WHY DID I EVEN WRITE THIS [STOP]
# @app.route("/level/get/list", methods=["GET"])
# def get_level_list():
#     try:
#         user = get_user()
#     except NoUser as e:
#         return make_error(e.message)
#     except InvalidUser as e:
#         return make_error(e.message)
#
#     return make_status("success", "Got user", user_to_xml(user))


# No error checking FTW! And no validity checking... /posts 2^64 as score/
@app.route("/level/scoreboard/submit", methods=["POST"])
def post_level_score():
    user = get_user_from_token()
    level_id = request.form["level_id"]
    score = int(request.form["score"])

    levels.update_one(
        {"_id": level_id},
        {"$push": {"scores":
            {
                user: {
                    "score": score,
                    "timestamp": timestamp
                }
            }
        }}
    )

    return "true"


@app.route("/user/create", methods=["POST"])
def create_user():
    try:
        user_login = request.form["login"]
        name = request.form["name"]
        password = request.form["password"]
        public = request.form["public"]

        if login is None:
            raise MissingInformation("login")
        if name is None:
            raise MissingInformation("name")
        if password is None:
            raise MissingInformation("password")

    except MissingInformation as e:
        return make_error(e.message)

    try:
        # check login is valid
        user_login = user_login.lower()

        # max 15 chars
        if len(user_login) > 15:
            raise InvalidInformation("login", "Must be less than 15 characters.")

        # alphanumerics only
        if re.match("[^a-z0-9]", user_login):
            raise InvalidInformation("login", "Can only contain alphanumeric characters")

        # check screen name is valid
        if len(name) > 32:
            raise InvalidInformation("name", "Must be less than 32 characters")

        # check password is valid
        if len(password) > 15:
            raise InvalidInformation("passwrd", "Must be less than 15 characters")

        # check public is valid
        if public == "on":
            public = 1
        else:
            public = 0

    except InvalidInformation as e:
        return make_error(e.message)

    # all information is valid

    # hash dat pass
    hasher = sha256()
    salt = urandom(16)

    hasher.update(password.encode("utf8"))
    hasher.update(salt)
    pass_hash = hasher.hexdigest()

    # push to DB
    res = users.insert({
        "login": user_login,
        "name": name,
        "salt": salt,
        "pass_hash": pass_hash,
        "public": public,
        "subscriptions": [],
        "tokens": []
    })

    mkdir("/".join(("level", str(login))))

    return make_status("success", "User created")


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

    try:
        username = username.lower()
        user = login(username, password)
        if user is None:
            raise InvalidLogin
    except InvalidLogin as e:
        return make_error(e.message)

    hasher = sha256()
    hasher.update(urandom(32))
    token = hasher.hexdigest()

    expire = time.time() + (60*60*24*7*52)  # 52 weeks later

    users.update(user, {"$push": {"tokens": {"code": token, "expires": expire}}})

    token_hex = b2a_hex(token)

    return token_hex


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
