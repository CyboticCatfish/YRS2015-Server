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


from . import app
from .error import InvalidInformation, InvalidUser, InvalidLogin, NoUser, MissingInformation
from .database import levels
from .converters import user_to_xml
from .image import get_and_crop, surf_to_string
from .api import make_error, get_arg

from sqlalchemy import sql
# app.debug = True


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

        try:
            level_id = int(level_id)
        except ValueError:
            raise InvalidInformation("id", "level not foudn")

        res = levels.find_one({"id": level_id})
        if res is None:
            raise InvalidInformation("id", "level not found")
        return render_template("level.html", level=res)

    except MissingInformation as e:
        return make_error(e.message)
    except InvalidInformation as e:
        return make_error(e.message)


@app.route("/levels", methods=["GET"])
def web_levels():
    res = levels.find({"public": True}, {"_id": 1, "name": 1, "creator": 1})

    return render_template("levels.html", levels=res)


@app.route("/login", methods=["GET"])
def web_login():
    try:
        return render_template("login.html", token=request.args["token"])
    except:
        return render_template("login.html")
