import logging

from decouple import config

import schemas
from chalicelib.core import sessions_mobs, events

# from chalicelib.utils import sql_helper as sh

if config("EXP_SESSIONS_SEARCH", cast=bool, default=False):
    from chalicelib.core import sessions_exp as sessions
else:
    from chalicelib.core import sessions

from chalicelib.utils import pg_client, helper, ch_client, exp_ch_helper

logger = logging.getLogger(__name__)


def get_by_url(project_id, data: schemas.GetHeatmapPayloadSchema):
    args = {"startDate": data.startTimestamp, "endDate": data.endTimestamp,
            "project_id": project_id, "url": data.url}
    constraints = ["main_events.project_id = toUInt16(%(project_id)s)",
                   "(main_events.url_hostpath = %(url)s OR main_events.url_path = %(url)s)",
                   "main_events.datetime >= toDateTime(%(startDate)s/1000)",
                   "main_events.datetime <= toDateTime(%(endDate)s/1000)",
                   "main_events.event_type='CLICK'",
                   "isNotNull(main_events.normalized_x)"]
    query_from = f"{exp_ch_helper.get_main_events_table(data.startTimestamp)} AS main_events"
    has_click_rage_filter = False
    # TODO: is this used ?
    # if len(data.filters) > 0:
    #     for i, f in enumerate(data.filters):
    #         if f.type == schemas.FilterType.issue and len(f.value) > 0:
    #             has_click_rage_filter = True
    #             query_from += """INNER JOIN events_common.issues USING (timestamp, session_id)
    #                            INNER JOIN issues AS mis USING (issue_id)
    #                            INNER JOIN LATERAL (
    #                                 SELECT COUNT(1) AS real_count
    #                                  FROM events.clicks AS sc
    #                                           INNER JOIN sessions as ss USING (session_id)
    #                                  WHERE ss.project_id = 2
    #                                    AND (sc.url = %(url)s OR sc.path = %(url)s)
    #                                    AND sc.timestamp >= %(startDate)s
    #                                    AND sc.timestamp <= %(endDate)s
    #                                    AND ss.start_ts >= %(startDate)s
    #                                    AND ss.start_ts <= %(endDate)s
    #                                    AND sc.selector = clicks.selector) AS r_clicks ON (TRUE)"""
    #             constraints += ["mis.project_id = %(project_id)s",
    #                             "issues.timestamp >= %(startDate)s",
    #                             "issues.timestamp <= %(endDate)s"]
    #             f_k = f"issue_value{i}"
    #             args = {**args, **sh.multi_values(f.value, value_key=f_k)}
    #             constraints.append(sh.multi_conditions(f"%({f_k})s = ANY (issue_types)",
    #                                                    f.value, value_key=f_k))
    #             constraints.append(sh.multi_conditions(f"mis.type = %({f_k})s",
    #                                                    f.value, value_key=f_k))

    if data.click_rage and not has_click_rage_filter:
        constraints.append("""(issues.session_id IS NULL 
                                OR (issues.datetime >= toDateTime(%(startDate)s/1000)
                                    AND issues.datetime <= toDateTime(%(endDate)s/1000)
                                    AND issues.project_id = toUInt16(%(project_id)s)
                                    AND issues.event_type = 'ISSUE'
                                    AND issues.project_id = toUInt16(%(project_id)s
                                    AND mis.project_id = toUInt16(%(project_id)s
                                    AND mis.type='click_rage'))))""")
        query_from += """ LEFT JOIN experimental.events AS issues ON (main_events.session_id=issues.session_id)
                       LEFT JOIN experimental.issues AS mis ON (issues.issue_id=mis.issue_id)"""
    with ch_client.ClickHouseClient() as cur:
        query = cur.format(f"""SELECT main_events.normalized_x AS normalized_x, 
                                            main_events.normalized_y AS normalized_y
                                FROM {query_from}
                                WHERE {" AND ".join(constraints)}
                                LIMIT 500;""", args)
        logger.debug("---------")
        logger.debug(query)
        logger.debug("---------")
        try:
            rows = cur.execute(query)

        except Exception as err:
            logger.warning("--------- HEATMAP 2 SEARCH QUERY EXCEPTION CH -----------")
            logger.warning(query)
            logger.warning("--------- PAYLOAD -----------")
            logger.warning(data)
            logger.warning("--------------------")
            raise err

        return helper.list_to_camel_case(rows)


def get_x_y_by_url_and_session_id(project_id, session_id, data: schemas.GetHeatmapBasePayloadSchema):
    args = {"project_id": project_id, "session_id": session_id, "url": data.url}
    constraints = ["main_events.project_id = toUInt16(%(project_id)s)",
                   "main_events.session_id = %(session_id)s",
                   "(main_events.url_hostpath = %(url)s OR main_events.url_path = %(url)s)",
                   "main_events.event_type='CLICK'",
                   "isNotNull(main_events.normalized_x)"]
    query_from = f"{exp_ch_helper.get_main_events_table(0)} AS main_events"

    with ch_client.ClickHouseClient() as cur:
        query = cur.format(f"""SELECT main_events.normalized_x AS normalized_x, 
                                                main_events.normalized_y AS normalized_y
                                    FROM {query_from}
                                    WHERE {" AND ".join(constraints)};""", args)
        logger.debug("---------")
        logger.debug(query)
        logger.debug("---------")
        try:
            rows = cur.execute(query)
        except Exception as err:
            logger.warning("--------- HEATMAP-session_id SEARCH QUERY EXCEPTION CH -----------")
            logger.warning(query)
            logger.warning("--------- PAYLOAD -----------")
            logger.warning(data)
            logger.warning("--------------------")
            raise err

        return helper.list_to_camel_case(rows)


def get_selectors_by_url_and_session_id(project_id, session_id, data: schemas.GetHeatmapBasePayloadSchema):
    args = {"project_id": project_id, "session_id": session_id, "url": data.url}
    constraints = ["main_events.project_id = toUInt16(%(project_id)s)",
                   "main_events.session_id = %(session_id)s",
                   "(main_events.url_hostpath = %(url)s OR main_events.url_path = %(url)s)",
                   "main_events.event_type='CLICK'"]
    query_from = f"{exp_ch_helper.get_main_events_table(0)} AS main_events"

    with ch_client.ClickHouseClient() as cur:
        query = cur.format(f"""SELECT main_events.selector AS selector, 
                                            COUNT(1) AS count
                                    FROM {query_from}
                                    WHERE {" AND ".join(constraints)}
                                    GROUP BY 1
                                    ORDER BY count DESC;""", args)
        logger.debug("---------")
        logger.debug(query)
        logger.debug("---------")
        try:
            rows = cur.execute(query)
        except Exception as err:
            logger.warning("--------- HEATMAP-session_id SEARCH QUERY EXCEPTION CH -----------")
            logger.warning(query)
            logger.warning("--------- PAYLOAD -----------")
            logger.warning(data)
            logger.warning("--------------------")
            raise err

        return helper.list_to_camel_case(rows)


if not config("EXP_SESSIONS_SEARCH", cast=bool, default=False):
    # this part is identical to FOSS
    SESSION_PROJECTION_COLS = """s.project_id,
    s.session_id::text AS session_id,
    s.start_ts,
    s.duration"""


    def search_short_session(data: schemas.HeatMapSessionsSearch, project_id, user_id,
                             include_mobs: bool = True, exclude_sessions: list[str] = [],
                             _depth: int = 3):
        no_platform = True
        no_location = True
        for f in data.filters:
            if f.type == schemas.FilterType.platform:
                no_platform = False
                break
        for f in data.events:
            if f.type == schemas.EventType.location:
                no_location = False
                if len(f.value) == 0:
                    f.operator = schemas.SearchEventOperator._is_any
                break
        if no_platform:
            data.filters.append(schemas.SessionSearchFilterSchema(type=schemas.FilterType.platform,
                                                                  value=[schemas.PlatformType.desktop],
                                                                  operator=schemas.SearchEventOperator._is))
        if no_location:
            data.events.append(schemas.SessionSearchEventSchema2(type=schemas.EventType.location,
                                                                 value=[],
                                                                 operator=schemas.SearchEventOperator._is_any))

        data.filters.append(schemas.SessionSearchFilterSchema(type=schemas.FilterType.events_count,
                                                              value=[0],
                                                              operator=schemas.MathOperator._greater))

        full_args, query_part = sessions.search_query_parts(data=data, error_status=None, errors_only=False,
                                                            favorite_only=data.bookmarked, issue=None,
                                                            project_id=project_id, user_id=user_id)
        full_args["exclude_sessions"] = tuple(exclude_sessions)
        if len(exclude_sessions) > 0:
            query_part += "\n AND session_id NOT IN (%(exclude_sessions)s)"
        with pg_client.PostgresClient() as cur:
            data.order = schemas.SortOrderType.desc
            data.sort = 'duration'
            main_query = cur.mogrify(f"""SELECT *
                                         FROM (SELECT {SESSION_PROJECTION_COLS}
                                               {query_part}
                                               ORDER BY {data.sort} {data.order.value}
                                               LIMIT 20) AS raw
                                         ORDER BY random()
                                         LIMIT 1;""", full_args)
            logger.debug("--------------------")
            logger.debug(main_query)
            logger.debug("--------------------")
            try:
                cur.execute(main_query)
            except Exception as err:
                logger.warning("--------- CLICK MAP SHORT SESSION SEARCH QUERY EXCEPTION -----------")
                logger.warning(main_query.decode('UTF-8'))
                logger.warning("--------- PAYLOAD -----------")
                logger.warning(data.model_dump_json())
                logger.warning("--------------------")
                raise err

            session = cur.fetchone()
        if session:
            if include_mobs:
                session['domURL'] = sessions_mobs.get_urls(session_id=session["session_id"], project_id=project_id)
                session['mobsUrl'] = sessions_mobs.get_urls_depercated(session_id=session["session_id"])
                if _depth > 0 and len(session['domURL']) == 0 and len(session['mobsUrl']) == 0:
                    return search_short_session(data=data, project_id=project_id, user_id=user_id,
                                                include_mobs=include_mobs,
                                                exclude_sessions=exclude_sessions + [session["session_id"]],
                                                _depth=_depth - 1)
                elif _depth == 0 and len(session['domURL']) == 0 and len(session['mobsUrl']) == 0:
                    logger.info("couldn't find an existing replay after 3 iterations for heatmap")

            session['events'] = get_page_events(session_id=session["session_id"])
        else:
            logger.debug("No session found for heatmap")

        return helper.dict_to_camel_case(session)


    def get_selected_session(project_id, session_id):
        with pg_client.PostgresClient() as cur:
            main_query = cur.mogrify(f"""SELECT {SESSION_PROJECTION_COLS}
                                         FROM public.sessions AS s
                                         WHERE session_id=%(session_id)s;""", {"session_id": session_id})
            logger.debug("--------------------")
            logger.debug(main_query)
            logger.debug("--------------------")
            try:
                cur.execute(main_query)
            except Exception as err:
                logger.warning("--------- CLICK MAP GET SELECTED SESSION QUERY EXCEPTION -----------")
                logger.warning(main_query.decode('UTF-8'))
                raise err

            session = cur.fetchone()
        if session:
            session['domURL'] = sessions_mobs.get_urls(session_id=session["session_id"], project_id=project_id)
            session['mobsUrl'] = sessions_mobs.get_urls_depercated(session_id=session["session_id"])
            if len(session['domURL']) == 0 and len(session['mobsUrl']) == 0:
                session["_issue"] = "mob file not found"
                logger.info("can't find selected mob file for heatmap")
            session['events'] = get_page_events(session_id=session["session_id"])

        return helper.dict_to_camel_case(session)


    def get_page_events(session_id):
        with pg_client.PostgresClient() as cur:
            cur.execute(cur.mogrify("""\
                    SELECT 
                        message_id,
                        timestamp,
                        host,
                        path
                        query,
                        path AS value,
                        path AS url,
                        'LOCATION' AS type
                    FROM events.pages
                    WHERE session_id = %(session_id)s
                    ORDER BY timestamp,message_id;""", {"session_id": session_id}))
            rows = cur.fetchall()
            rows = helper.list_to_camel_case(rows)
        return rows

else:
    # use CH
    SESSION_PROJECTION_COLS = """s.project_id,
    s.session_id AS session_id,
    toUnixTimestamp(s.datetime)*1000 AS start_ts,
    s.duration AS duration"""


    def search_short_session(data: schemas.HeatMapSessionsSearch, project_id, user_id,
                             include_mobs: bool = True, exclude_sessions: list[str] = [],
                             _depth: int = 3):
        no_platform = True
        no_location = True
        for f in data.filters:
            if f.type == schemas.FilterType.platform:
                no_platform = False
                break
        for f in data.events:
            if f.type == schemas.EventType.location:
                no_location = False
                if len(f.value) == 0:
                    f.operator = schemas.SearchEventOperator._is_any
                break
        if no_platform:
            data.filters.append(schemas.SessionSearchFilterSchema(type=schemas.FilterType.platform,
                                                                  value=[schemas.PlatformType.desktop],
                                                                  operator=schemas.SearchEventOperator._is))
        if no_location:
            data.events.append(schemas.SessionSearchEventSchema2(type=schemas.EventType.location,
                                                                 value=[],
                                                                 operator=schemas.SearchEventOperator._is_any))

        data.filters.append(schemas.SessionSearchFilterSchema(type=schemas.FilterType.events_count,
                                                              value=[0],
                                                              operator=schemas.MathOperator._greater))

        full_args, query_part = sessions.search_query_parts_ch(data=data, error_status=None, errors_only=False,
                                                               favorite_only=data.bookmarked, issue=None,
                                                               project_id=project_id, user_id=user_id)
        full_args["exclude_sessions"] = tuple(exclude_sessions)
        if len(exclude_sessions) > 0:
            query_part += "\n AND session_id NOT IN (%(exclude_sessions)s)"
        with ch_client.ClickHouseClient() as cur:
            data.order = schemas.SortOrderType.desc
            data.sort = 'duration'
            main_query = cur.format(f"""SELECT * 
                                               FROM (SELECT {SESSION_PROJECTION_COLS}
                                               {query_part}
                                               ORDER BY {data.sort} {data.order.value}
                                               LIMIT 20) AS raw
                                               ORDER BY rand()
                                               LIMIT 1;""", full_args)
            logger.debug("--------------------")
            logger.debug(main_query)
            logger.debug("--------------------")
            try:
                session = cur.execute(main_query)
            except Exception as err:
                logger.warning("--------- CLICK MAP SHORT SESSION SEARCH QUERY EXCEPTION CH -----------")
                logger.warning(main_query)
                logger.warning("--------- PAYLOAD -----------")
                logger.warning(data.model_dump_json())
                logger.warning("--------------------")
                raise err

        if session:
            if include_mobs:
                session['domURL'] = sessions_mobs.get_urls(session_id=session["session_id"], project_id=project_id)
                session['mobsUrl'] = sessions_mobs.get_urls_depercated(session_id=session["session_id"])
                if _depth > 0 and len(session['domURL']) == 0 and len(session['mobsUrl']) == 0:
                    return search_short_session(data=data, project_id=project_id, user_id=user_id,
                                                include_mobs=include_mobs,
                                                exclude_sessions=exclude_sessions + [session["session_id"]],
                                                _depth=_depth - 1)
                elif _depth == 0 and len(session['domURL']) == 0 and len(session['mobsUrl']) == 0:
                    logger.info("couldn't find an existing replay after 3 iterations for heatmap")

            session['events'] = events.get_by_session_id(project_id=project_id, session_id=session["session_id"],
                                                         event_type=schemas.EventType.location)

        return helper.dict_to_camel_case(session)


    def get_selected_session(project_id, session_id):
        with ch_client.ClickHouseClient() as cur:
            main_query = cur.format(f"""SELECT {SESSION_PROJECTION_COLS}
                                              FROM experimental.sessions AS s
                                              WHERE session_id=%(session_id)s;""", {"session_id": session_id})
            logger.debug("--------------------")
            logger.debug(main_query)
            logger.debug("--------------------")
            try:
                session = cur.execute(main_query)
            except Exception as err:
                logger.warning("--------- CLICK MAP GET SELECTED SESSION QUERY EXCEPTION -----------")
                logger.warning(main_query.decode('UTF-8'))
                raise err
        if len(session) > 0:
            session = session[0]
        if session:
            session['domURL'] = sessions_mobs.get_urls(session_id=session["session_id"], project_id=project_id)
            session['mobsUrl'] = sessions_mobs.get_urls_depercated(session_id=session["session_id"])
            if len(session['domURL']) == 0 and len(session['mobsUrl']) == 0:
                session["_issue"] = "mob file not found"
                logger.info("can't find selected mob file for heatmap")
            session['events'] = get_page_events(session_id=session["session_id"])

        return helper.dict_to_camel_case(session)


    def get_page_events(session_id):
        with ch_client.ClickHouseClient() as cur:
            rows = cur.execute("""\
                    SELECT 
                        message_id,
                        timestamp,
                        host,
                        path,
                        query,
                        path AS value,
                        path AS url,
                        'LOCATION' AS type
                    FROM experimental.events
                    WHERE session_id = %(session_id)s AS event_type='LOCATION'
                    ORDER BY timestamp,message_id;""", {"session_id": session_id})
            rows = helper.list_to_camel_case(rows)
        return rows
