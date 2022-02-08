
import os, warnings

from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy import event, create_engine, exc
from sqlalchemy.ext.declarative import declarative_base

from api import config

def add_engine_pidguard(engine):

    """
    Add multiprocessing guards.

    Forces a connection to be reconnected if it is detected
    as having been shared to a sub-process.

    """

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        connection_record.info['pid'] = os.getpid()

    @event.listens_for(engine, "checkout")
    def checkout(dbapi_connection, connection_record, connection_proxy):
        pid = os.getpid()
        if connection_record.info['pid'] != pid:
            # substitute log.debug() or similar here as desired
            warnings.warn(
                "Parent process %(orig)s forked (%(newproc)s) with an open "
                "database connection, "
                "which is being discarded and recreated." %
                {"newproc": pid, "orig": connection_record.info['pid']})
            connection_record.connection = connection_proxy.connection = None
            raise exc.DisconnectionError(
                "Connection record belongs to pid %s, "
                "attempting to check out in pid %s" %
                (connection_record.info['pid'], pid)
            )



# engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo = False, isolation_level="AUTOCOMMIT")

# session_factory = sessionmaker(bind=engine)

# session = session_factory()

# Base.metadata.create_all(engine)

# session.commit()

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, convert_unicode=True)
add_engine_pidguard(engine)
session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = session.query_property()
Base.metadata.create_all(engine)
Base.metadata.bind = engine

#engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

#add_engine_pidguard(engine)

#session = sessionmaker(engine)

#Session = scoped_session(session)

#Base = declarative_base()

#Base.query = session.query_property()

