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
    username = Column(String(32), unique=True)
    login = Column(String(32))
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


Base.metadata.create_all(engine)

Session = sessionmaker()
Session.configure(bind=engine)

