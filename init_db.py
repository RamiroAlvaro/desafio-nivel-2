from sqlalchemy import create_engine, MetaData

from aiohttp_desafio.settings import BASE_DIR, get_config
from aiohttp_desafio.db import state, city

DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"

ADMIN_DB_URL = DSN.format(
    user='postgres', password='postgres', database='postgres',
    host='localhost', port=5432
)

admin_engine = create_engine(ADMIN_DB_URL, isolation_level='AUTOCOMMIT')

USER_CONFIG_PATH = BASE_DIR / 'config' / 'desafio-nivel-2.yaml'
USER_CONFIG = get_config(['-c', USER_CONFIG_PATH.as_posix()])
USER_DB_URL = DSN.format(**USER_CONFIG['postgres'])
user_engine = create_engine(USER_DB_URL)

TEST_CONFIG_PATH = BASE_DIR / 'config' / 'desafio-nivel-2_test.yaml'
TEST_CONFIG = get_config(['-c', TEST_CONFIG_PATH.as_posix()])
TEST_DB_URL = DSN.format(**TEST_CONFIG['postgres'])
test_engine = create_engine(TEST_DB_URL)


def setup_db(config):

    db_name = config['database']
    db_user = config['user']
    db_pass = config['password']

    conn = admin_engine.connect()
    conn.execute("DROP DATABASE IF EXISTS %s" % db_name)
    conn.execute("DROP ROLE IF EXISTS %s" % db_user)
    conn.execute("CREATE USER %s WITH PASSWORD '%s'" % (db_user, db_pass))
    conn.execute("CREATE DATABASE %s ENCODING 'UTF8'" % db_name)
    conn.execute("GRANT ALL PRIVILEGES ON DATABASE %s TO %s" %
                 (db_name, db_user))
    conn.close()


def teardown_db(config):

    db_name = config['database']
    db_user = config['user']

    conn = admin_engine.connect()
    conn.execute("""
      SELECT pg_terminate_backend(pg_stat_activity.pid)
      FROM pg_stat_activity
      WHERE pg_stat_activity.datname = '%s'
        AND pid <> pg_backend_pid();""" % db_name)
    conn.execute("DROP DATABASE IF EXISTS %s" % db_name)
    conn.execute("DROP ROLE IF EXISTS %s" % db_user)
    conn.close()


def create_tables(engine=test_engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[state, city])


def drop_tables(engine=test_engine):
    meta = MetaData()
    meta.drop_all(bind=engine, tables=[state, city])


def sample_data(engine=test_engine):
    conn = engine.connect()
    conn.execute(state.insert(), [
        {'state_name': 'Minas Gerais'},
        {'state_name': 'Rio Grande do Sul'},

    ])
    conn.execute(city.insert(), [
        {'city_name': 'Belo Horizonte', 'state_id': 1},
        {'city_name': 'Sabará', 'state_id': 1},
        {'city_name': 'Caxias do Sul', 'state_id': 2},
    ])
    conn.close()


if __name__ == '__main__':
    setup_db(USER_CONFIG['postgres'])
    create_tables(engine=user_engine)
    sample_data(engine=user_engine)
    # drop_tables()
    # teardown_db(USER_CONFIG['postgres'])
