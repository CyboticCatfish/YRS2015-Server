#!/usr/bin/env python3
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

from flask import Flask, request, make_response, render_template
from sqlalchemy import sql, asc, desc
from hashlib import sha256
from datetime import datetime, timedelta
from os import urandom, _exists, mkdir
from binascii import b2a_hex, a2b_hex
from io import BytesIO
import re
import random


from . import app
from .error import InvalidInformation, InvalidUser, InvalidLogin, NoUser, MissingInformation
from .database import engine, User, Level, Token, Subscription, Score
from .converters import user_to_xml
from .image import get_and_crop, surf_to_string

# app.debug = True


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
        raise error.InvalidUser()

    user_name = get_arg("user_name")


    if user_id is None and user_name is None:
        raise NoUser()
    elif user_id is not None:
        x = sql.select([User]).where(User.id == user_id).limit(1)
        conn = engine.connect()
        for row in conn.execute(x):
            return row
    elif user_name is not None:
        return "test"


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
    conn = engine.connect()
    query = sql.select(User).where(User.id == user_id).limit(1)
    for row in conn.execute(query):
        return row
    else:
        return None


def get_user_id_from_token(token=None):
    if token is None:
        token = get_header("token")
        if token is None:
            token = request.form["token"]
            if token is None:
                raise MissingInformation("token")

    token_bin = a2b_hex(token)
    conn = engine.connect()
    query = sql.select([Token.__table__])\
        .limit(1)\
        .order_by(asc(Token.expire))\
        .where(Token.token == token_bin)

    rows = conn.execute(query).fetchall()

    for row in rows:
        try:
            if row[Token.expire] < datetime.now():
                raise InvalidInformation("token", "Token has expired")
            else:
                return row["user_id"]
        except:
            return row["user_id"]
    else:
        raise InvalidInformation("token", "Not a valid token.")


def login(username, password):

    hasher = sha256()
    hasher.update(password.encode("utf8"))
    pass_hash = hasher.digest()

    conn = engine.connect()
    query = sql.select([User.__table__]).where(
        (User.login == username.lower())
        & (User.passhash == pass_hash)
    )

    for row in conn.execute(query).fetchall():
        print(row.passhash)
        return row
    else:
        return None


@app.route("/", methods=["GET"])
def hello_world():
    return render_template("home.html")


@app.route("/submit", methods=["GET"])
def submit_level():
    return render_template("submit.html")


@app.route("/signup", methods=["GET"])
def signup_form():
    return render_template("signup.html")

@app.route("/download", methods=["GET"])
def download():
    return render_template("download.html")

@app.route("/level", methods=["GET"])
def web_level():
    try:
        level_id = get_arg("id")
        if level_id is None:
            raise MissingInformation("id")
        conn = engine.connect()
        query = sql.select([Level]).where(Level.id == level_id)
        rows = conn.execute(query)

        for row in rows.fetchall():
            # print(row)
            return render_template("level.html", level=row)
        else:
            raise InvalidInformation("id", "Not found")
    except MissingInformation as e:
        return make_error(e.message)
    except InvalidInformation as e:
        return make_error(e.message)


@app.route("/levels", methods=["GET"])
def web_levels():
    conn = engine.connect()
    query = sql.select([Level.name, Level.creator, Level.id]).limit(50)
    res = conn.execute(query)

    levels = []
    for row in res.fetchall():
        query = sql.select([User.username]).where(User.id == row["creator"])
        res2 = conn.execute(query)
        for row2 in res2.fetchall():
            levels.append({
                "id": row["id"],
                "name": row["name"],
                "user": row2["username"]
            })
            break
        continue

    return render_template("levels.html", levels=levels)


@app.route("/login", methods=["GET"])
def web_login():
    try:
        return render_template("login.html", token=request.args["token"])
    except:
        return render_template("login.html")


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
            raise InvalidInformation("id", "Not a number.")
    except InvalidInformation as e:
        return make_error(e.message)

    # perform query
    try:
        conn = engine.connect()
        query = sql.select([Level.creator, Level.timestamp, Level.name]).where(Level.id == level_id).limit(1)
        rows = conn.execute(query)
        for row in rows.fetchall():
            print(row[2])
            return open("levels/%s/%s-%s.lvl" % (row[0], row[2], row[1])).read()
        else:
            raise InvalidInformation("id", "No level exists with this ID")
    except InvalidInformation as e:
        return make_error(e.message)


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
        user_id = get_user_id_from_token(token)
    except InvalidInformation as e:
        return make_error(e.message)

    print(level_id, user_id)

    conn = engine.connect()
    query = sql.insert(
        Subscription,
        values={Subscription.level_id: level_id,
                Subscription.user_id: user_id}
    )
    x = conn.execute(query)
    # if x:
    #     print("1")
    # else:
    #     print("2")

    return make_status("success", "Subscribed to level")


@app.route("/level/submit", methods=["POST"])
def upload_level():
    try:
        user_id = get_user_id_from_token()
    except MissingInformation as e:
        return make_error(e.message)
    except InvalidInformation as e:
        return make_error(e.message)
    try:
        name = request.form["level-name"]
        public = request.form["public"]
        if name is None:
            raise MissingInformation("level-name")
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

    timestamp = datetime.now()

    f = request.files["level"]
    f.save("levels/%s/%s-%s.lvl" % (user_id, name, timestamp))

    f = request.files["image"]
    f.save("levels/%s/%s-%s.png" % (user_id, name, timestamp))

    conn = engine.connect()
    query = sql.insert(Level.__table__,
                       values={
                           Level.creator: user_id,
                           Level.name: name,
                           Level.timestamp: timestamp,
                           Level.public: public
                       }
    )
    conn.execute(query)

    query = sql.select([Level.id]).where(
        (Level.name == name) &
        (Level.timestamp == timestamp)
    ).limit(1)
    res = conn.execute(query)
    level_id = None
    for row in res.fetchall():
        level_id = row["id"]

    if level_id is None:
        return make_error(level_id)

    query = sql.insert(Subscription.__table__,
                       values={
                           Subscription.level_id: level_id,
                           Subscription.user_id: user_id
                       }
                       )
    conn.execute(query)

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

    conn = engine.connect()
    try:
        query = sql.select([Level.creator, Level.name]).where(Level.id == level_id).limit(1)
        res = conn.execute(query)
        row = res.fetchone()
        user_id = row["creator"]
        level_name = row["name"]

    except InvalidInformation as e:
        return make_error(e.message)

    query = sql.select([User.username]).where(User.id == user_id).limit(1)
    print(query)
    res = conn.execute(query)
    user_name = res.fetchone()["username"]

    x = ",".join((level_name, user_name))
    print(x)
    return x


@app.route("/level/get/image", methods=["GET"])
def get_level_image():
    try:
        level_id = get_arg("id")
        size = (int(get_arg("x")), int(get_arg("y")))

        if level_id is None:
            raise MissingInformation("id")
        try:
            level_id = int(level_id)
        except ValueError:
            raise InvalidInformation("id", "Not an integer")

        conn = engine.connect()
        query = sql.select([Level.name, Level.creator, Level.timestamp])\
            .where(Level.id == level_id).limit(1)
        res = conn.execute(query)
        rows = res.fetchall()
        if len(rows) != 1:
            raise InvalidInformation("id", "Not a level")

        for row in rows:
            imagepath = "levels/%s/%s-%s.png" % (str(row["creator"]), str(row["name"]), str(row["timestamp"]))
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


@app.route("/level/get/list", methods=["GET"])
def get_level_list():
    try:
        user = get_user()
    except NoUser as e:
        return make_error(e.message)
    except InvalidUser as e:
        return make_error(e.message)

    return make_status("success", "Got user", user_to_xml(user))


@app.route("/level/scoreboard/submit", methods=["POST"])
def post_level_score():
    user_id = get_user_id_from_token()
    level_id = int(request.form["level_id"])
    score = int(request.form["score"])

    conn = engine.connect()
    query = sql.insert(Score.__table__,
               values={
                   Score.user_id: user_id,
                   Score.level_id: level_id,
                   Score.score: score
               })

    conn.execute(query)

    return "true"



@app.route("/user/create", methods=["POST"])
def create_user():
    conn = engine.connect()
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

        # check unique
        query = sql.select([User.id])\
            .where(User.login == user_login)
        print(query)
        res = conn.execute(query)
        if bool(len(res.fetchall())):
            raise InvalidInformation("login", "Login is in use")

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
    # hash password
    hasher = sha256()
    hasher.update(password.encode("utf8"))

    pass_hash = hasher.digest()

    # push to DB
    query = sql.insert(User.__table__,
        values={
            User.login: user_login,
            User.username: name,
            User.passhash: pass_hash,
            User.public: public
        }
    )

    res = conn.execute(query)

    query = sql.select([User.id]).where(User.login == user_login)
    res = conn.execute(query)

    for rows in res.fetchall():
        mkdir("/".join(("level", str(rows["id"]))))

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
    hasher.update(urandom(16))
    token = hasher.digest()

    expire = datetime.now() + timedelta(weeks=52)

    conn = engine.connect()
    query = sql.insert(Token.__table__, values={
        Token.token: token,
        Token.user_id: user.id,
        Token.expire: expire
    })

    res = conn.execute(query)

    token_hex = b2a_hex(token)

    return token_hex


@app.route("/user/subscriptions", methods=["GET", "POST"])
def get_subscriptions():
    try:
        token = get_header("token")
        if token is None:
            user_id = get_arg("user_id")
            if user_id is None:
                token = request.form["token"]
                if token is None:
                    raise MissingInformation("user_id")
        else:
            user_id = None
    except MissingInformation as e:
        return make_error(e.message)

    try:
        if user_id is None:
            user_id = get_user_id_from_token(token)
    except InvalidInformation as e:
        return make_error(e.message)

    conn = engine.connect()
    query = sql.select([Subscription.level_id])\
        .where(Subscription.user_id == user_id)\
        .limit(50)

    res = conn.execute(query)

    x = ",".join(str(row["level_id"]) for row in res.fetchall())
    return x


if __name__ == "__main__":
    # context = ("server.crt", "server.key")
    app.run("0.0.0.0", 80)
