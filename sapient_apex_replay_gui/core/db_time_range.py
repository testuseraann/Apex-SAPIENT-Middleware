#
# Copyright (c) 2019-2024 Roke Manor Research Ltd
#

"""Small helper to look up the time range covered by a replay database, used to prefill the start
and end time fields in the GUI once a file has been selected."""

from sqlalchemy import create_engine, text

from sapient_apex_server.time_util import datetime_int_to_str


def query_time_range(filename: str):
    """Returns (start_time, end_time) as ISO strings covering all messages in the given database.

    end_time is set to just after the last message's timestamp, since Database.get_messages() in
    sapient_apex_replay.replay treats end_time as exclusive of that boundary.

    :raises ValueError: if the database contains no messages.
    """
    engine = create_engine(f"sqlite:///{filename}")
    try:
        with engine.connect() as connection:
            min_time, max_time = connection.execute(
                text(
                    "SELECT MIN(timestamp_received), MAX(timestamp_received) FROM Message "
                    "WHERE error_severity IS NULL"
                )
            ).fetchone()
    finally:
        engine.dispose()
    if min_time is None or max_time is None:
        raise ValueError("Database contains no messages")
    return datetime_int_to_str(min_time), datetime_int_to_str(max_time + 1_000_000)
