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

from sqlalchemy import create_engine, MetaData, sql
from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, Binary, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = create_engine("sqlite:///data.db")


def get_count(query):
    count_q = query.statement.with_only_columns([func.count()]).order_by(None)
    count = query.session.execute(count_q).scalar()
    return count


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), primary_key=True)
    value = Column(String(128))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(32), unique=True)
    username = Column(String(32))
    passhash = Column(Binary(32))
    public = Column(Boolean)

    def to_xml(self):
        return "<user name='%s'>" % self.username


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), primary_key=True)
    owner = Column(ForeignKey(User.id))
    public = Column(Boolean)


class GroupLink(Base):
    __tablename__ = "grouplinks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(ForeignKey(User.id))
    group = Column(ForeignKey(Group.id))


class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator = Column(ForeignKey(User.id))
    name = Column(String(32))
    timestamp = Column(Integer)
    public = Column(Boolean)


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey(User.id))
    token = Column(Binary(32))
    expire = Column(DateTime)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey(User.id))
    level_id = Column(ForeignKey(Level.id))


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey(User.id))
    level_id = Column(ForeignKey(Level.id))
    score = Column(Integer)



Base.metadata.create_all(engine)

Session = sessionmaker()
Session.configure(bind=engine)
