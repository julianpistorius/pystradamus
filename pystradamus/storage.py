import atexit
import logging
import sqlite3 as lite
from functools import wraps

log = logging.getLogger(__name__)

__con = None # module local for our db connection

def requires_init(f):
    """Provides a simple guard against functions in this module being called
    without an initialized database
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not __con:
            raise RuntimeError("You must call `storage.init` before using any "\
                    "methods in the module")
        f(*args, **kwargs)
    return wrapper

def init(dbname):
    """Connects to a sqlite3 database at dbpath and initializes the schema if
    neeeded
    """
    log.debug("initializing db from %s", dbname)
    global __con
    __con = lite.connect(dbname)
    with __con:
        __con.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    jira_key text NOT NULL PRIMARY KEY,
                    jira_username text,
                    estimate text,
                    seconds_in_progress int
                )""")
    atexit.register(__con.close)

@requires_init
def add_or_update_evidence(ev):
    """Given a populated Evidence object, insert or replace it in the database
    """
    log.debug("adding/updating evidence %s", ev)
    cur = __con.cursor()
    cur.execute("""
            INSERT OR REPLACE INTO evidence (
                jira_key
                ,jira_username
                ,estimate
                ,seconds_in_progress
            ) VALUES (?, ?, ?, ?)
        """, (ev.ticket_id, ev.username, ev.estimate,
            ev.elapsed_time.total_seconds()))
    __con.commit()
    cur.close()
