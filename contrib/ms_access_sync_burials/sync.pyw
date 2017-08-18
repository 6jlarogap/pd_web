# coding=utf-8

# sync.py
#
# Синхронизация локальной MS Access б.д. с данными на сервере
#
# Использует settings.py, который лежит в том же каталоге
# Ведется журнал последней синхронизации, если указан
# settings.LAST_LOG
#
# Алгоритм
#
#   NB: Термин(ы)
#       -   Здесь участок и место, как в России участок.
#           В РБ это соответственно сектор и участок.
#
#   *   В settings.py указано, где находится ms access db
#   *   Выполняем логин в систему с именем и паролем пользователя,
#       получаем token. Имя и пароль пользователя указаны в
#       settings.py. Для того, чтобы всякий раз на разных
#       "кластерах" кладбищ не вводить для каждого "кластера"
#       имя и пароль, завели служебного пользователя с паролем
#   *   В offline базе находим время последней модификации
#       по всей локально базе. Т.е. есть ли что-то изменилось
#       в локальной базе.
#   *   Идем в online source, получаем список всех кладбищ
#       организации (ид и названия).
#       По каждому кладбищу из settings.CEMETERIES
#       -   Проверяем, чтобы указанные в settings.CEMETERIES
#           входили в состав принятых из online source.
#       -   Если в локальной базе что-то было до синхронизации.
#           Вдруг переименовали кладбище в online source,
#           переименовали его и здесь, в settings.py, а в
#           локальной б.д записи по этому кладбищу остались без
#           изменений. Производим переименование.
#       -   Получаем список участков кладбища.
#       -   Если в локальной базе что-то было до синхронизации.
#           Проверяем по локальной базе на то, что на сервере
#           какие-то участки переименовали.
#   *   Удаляем из ms access db все записи, которые не относятся
#       к кладбищам из settings.CEMETERIES
#       NB: можно было бы в settings.py не хранить список кладбищ,
#       но пользователь может уйти с этого списка кладбищ
#       на другой список, в результате алгоритм загрузил бы
#       данные по другому списку кладбищ
#   *   По каждому участку из считанных в online source кладбищ:
#       -   Находим время последней синхронизации в локальной
#           б.д.
#       -   Если это время ненулевое, т.е. ранее была синхронизация,
#           пусть даже и незаконченная, по участку, считываем из
#           online список мест участка, измененных после того
#           времени. Если какое-то из мест (ряд/название)
#           было переименовано в online, здесь же в
#           offline оно тоже будет переименовано
#       -   получаем данные по захоронениям, которые
#       - a) удалены со времени последней синхронизации.
#            Такие данные выдаются с сервера, если время последней
#            синхронизации (utc timestamp, секунд, прошедших с
#            01.01.1970 00:00:00 UTC) больше 0
#       - b) изменены. Т.е модифицированы или добавлены
#

import settings

import os, datetime
import pypyodbc as pyodbc

import urllib.request, urllib.error
import json   

f_log = cursor = connection = None

def main():
    global f_log, cursor, connection

    if hasattr(settings, 'LAST_LOG'):
        # last parm == 1 means line buffered output :
        f_log = open(os.path.abspath(settings.LAST_LOG), 'w', 1)

    databaseFile  = os.path.abspath(settings.MS_ACCESS_DBFILE)
    connection_string = "Driver={%s};Dbq=%s" % (
        settings.ODBC_DRIVER,
        databaseFile,
    )
    connection = pyodbc.connect(connection_string)
    cursor = connection.cursor()
    
    log_('Online source: login')
    rc, data = request_json(
        path='/api/auth/signin',
        method = 'POST',
        data = dict(
            username=settings.USERNAME,
            password=settings.PASSWORD,
    ))
    token = data.get('token')
    if not token:
        scram(1, "ERROR: Failed to log in to online source")
    log_(" OK")

    log_('Offline source: get max_dt_modified of all the records')
    max_dt_modified = 0
    cursor.execute(r"""
        SELECT
            Max(dt_modified) as dt_sync
        FROM
            burials
    """, ())
    if cursor.rowcount:
        sql_result = cursor.fetchone()
        max_dt_modified = sql_result['dt_sync'] or 0
    if max_dt_modified:
        log_(" : %s" % (
            datetime.datetime.fromtimestamp(max_dt_modified)
        ))
    else:
        log_(" : no records in offline source; this is the first sync")

    log_('Online source: get all cemeteries')
    rc, data = request_json(
        path='/api/oms/cemeteries?all=1',
        method = 'GET',
        token=token,
    )
    cemeteries_online = data
    cemeteries_online_dict = dict()
    log_(" OK")

    try:
        for c in cemeteries_online:
            cemeteries_online_dict[c['title']] = c['id']
    except (TypeError, KeyError,):
        scram(code=1, message="ERROR: Failed to get cemeteries!")

    log_("Local DB: Check data against online source")
    for cemetery_name in settings.CEMETERIES:
        if cemetery_name not in cemeteries_online_dict:
            scram(1, "ERROR: cemetery %s from settings.py not in online cemeteries" % cemetery_name)

    cemeteries_offline = list()
    for cemetery_name in settings.CEMETERIES:
        cemetery_dict = {
            'name': cemetery_name,
            'id': cemeteries_online_dict[cemetery_name],
            'areas': None
        }
        log_(" %s" % cemetery_name)
        if max_dt_modified:
            log_("  Rename records of cemetery_id==%s to name='%s' if necessary" % (
                cemetery_dict['id'],
                cemetery_name,
            ))
            cursor.execute(r"""
                UPDATE
                    burials
                SET
                    cemetery = ?
                WHERE
                    cemetery_id = ? AND
                    (cemetery <> ? OR (cemetery IS NULL AND ? <> ''))
            """, (
                cemetery_name,
                cemetery_dict['id'],
                cemetery_name,
                cemetery_name,
            )).commit()

        log_("  Get all areas")
        rc, data = request_json(
            path='/api/oms/cemeteries/%s/areas' % cemetery_dict['id'],
            method = 'GET',
            token=token,
        )
        log_("   : %s areas at the cemetery" % len(data))

        areas = list()
        for area in data:
            try:
                areas.append({
                    'name': area['title'],
                    'id': area['id'],
                })
            except (TypeError, KeyError,):
                scram(code=1, message="ERROR: Failed to get areas!")

        if max_dt_modified:

            log_("  Get max_dt_modified of burials at the cemetery")
            dt_modified = 0
            cursor.execute(r"""
                SELECT
                    Max(dt_modified) as dt_sync
                FROM
                    burials
                WHERE
                    cemetery_id = ?
            """, (
                cemetery_dict['id'],
            ))
            if cursor.rowcount:
                sql_result = cursor.fetchone()
                dt_modified = sql_result['dt_sync'] or 0
            if not dt_modified:
                log_("   No burials yet at offline for the cemetery")
            else:
                log_("   : %s" % (
                    datetime.datetime.fromtimestamp(dt_modified),
                ))
                log_("  Get areas modified after %s" % (
                    datetime.datetime.fromtimestamp(dt_modified),
                ))
                rc, data = request_json(
                    path='/api/oms/cemeteries/%s/areas?dt_modified=%s' % (
                        cemetery_dict['id'],
                        dt_modified,
                    ),
                    method = 'GET',
                    token=token,
                )
                if not data:
                    log_("   No such areas at the cemetery")
                for area in data:
                    log_("  Rename records of area_id==%s to name='%s' if necessary" % (
                        area['id'],
                        area['title'],
                    ))
                    cursor.execute(r"""
                        UPDATE
                            burials
                        SET
                            area = ?
                        WHERE
                            area_id = ? AND
                            (area <> ? OR (area IS NULL and ? <> ''))
                    """, (
                        area['title'],
                        area['id'],
                        area['title'],
                        area['title'],
                    )).commit()

                # Это удаленные из базы
                log_("  Remove burials deleted, annulated, exhumated after %s" % (
                    datetime.datetime.fromtimestamp(dt_modified),
                ))
                rc, data = request_json(
                    path='/api/oms/cemeteries/%s/deleted_burials?dt_modified=%s' % (
                        cemetery_dict['id'],
                        dt_modified,
                    ),
                    method = 'GET',
                    token=token,
                )
                if not data:
                    log_("   No such burials at the cemetery")
                for b in data:
                    cursor.execute(r"""
                        DELETE FROM
                            burials
                        WHERE
                            burial_id = ?
                    """, (
                        b['pk'],
                    )).commit()
                    log_("   DELETEd burial_id: %s" % b['pk'])

        cemetery_dict['areas'] = areas
        cemeteries_offline.append(cemetery_dict)

    if max_dt_modified:
        cemeteries_offline_str = ", ".join([c for c in settings.CEMETERIES])
        log_('Local DB: Remove other cemeteries than:')
        log_("", cemeteries_offline_str)
        cemeteries_offline_sql_str = ", ".join(["?" for c in settings.CEMETERIES])
        sql_str = "DELETE FROM [burials] WHERE cemetery NOT IN (%s)" % (
            cemeteries_offline_sql_str
        )
        cursor.execute(sql_str, settings.CEMETERIES).commit()
        log_(" OK. %s record(s) removed" % cursor.rowcount)

    log_('Local DB: Look for last dt_modified per burials in every area')
    log_('Online source: get new/modified burials')
    log_('Local DB: Update with those burials')
    for cemetery in cemeteries_offline:
        log_(' Cemetery: %s' % cemetery['name'])
        for area in cemetery['areas']:
            log_('  Area: %s' % area['name'])
            dt_modified = 0
            cursor.execute(r"""
                SELECT
                    Max(dt_modified) as dt_sync
                FROM
                    burials
                WHERE
                    area_id = ? and cemetery_id = ?
            """, (
                area['id'], cemetery['id'],
            ))
            if cursor.rowcount:
                sql_result = cursor.fetchone()
                dt_modified = sql_result['dt_sync'] or 0
            if dt_modified:
                log_("   Sync'ing local db by online data since %s" % (
                    datetime.datetime.fromtimestamp(dt_modified)
                ))
                dt_modified += 1

                log_("     Check for renamed places/rows at the area after %s" % (
                    datetime.datetime.fromtimestamp(dt_modified)
                ))
                try:
                    rc, data = request_json(
                        path='/api/oms/cemeteries/%s/areas/%s/places?dt_modified=%s' % (
                            cemetery['id'],
                            area['id'],
                            dt_modified,
                        ),
                        method = 'GET',
                        token=token,
                    )
                except (TypeError, KeyError,):
                    scram(code=1, message="ERROR: Failed to get places!")
                for place in data:
                    cursor.execute(r"""
                        UPDATE
                            burials
                        SET
                            place = ?, row = ?
                        WHERE
                            place_id = ? AND
                            (place <> ? OR (place IS NULL AND ? <> '') OR row <> ? OR (row IS NULL AND ? <> ''))
                    """, (
                        place['title'],
                        place['row'],
                        place['id'],
                        place['title'],
                        place['title'],
                        place['row'],
                        place['row'],
                    )).commit()
                log_("      %s place(s) checked" % len(data))

            else:
                log_("   No data for the area in local db. Fetching all data for it")

            rc, data = request_json(
                path='/api/oms/area/%s/msaccess/sync?dt_modified=%s' % (
                    area['id'],
                    dt_modified,
                ),
                method = 'GET',
                token=token,
            )
            for b in data:
                cursor.execute(r"""
                    SELECT
                        burial_id
                    FROM
                        burials
                    WHERE
                        burial_id = ?
                """, (
                    b['burial_id'],
                ))
                if cursor.fetchone():
                    cursor.execute(r"""
                        UPDATE
                            burials
                        SET
                            cemetery = ?,
                            area = ?,
                            row = ?,
                            place = ?,
                            grave_number = ?,
                            deadman = ?,
                            fact_date = ?,
                            deadman_dob = ?,
                            deadman_dod = ?,
                            burial_comments = ?,
                            burial_type = ?,
                            applicant = ?,
                            applicant_address = ?,
                            deadman_address=?,
                            dt_modified = ?,
                            cemetery_id = ?,
                            area_id = ?,
                            place_id = ?
                        WHERE
                            burial_id = ?
                    """, (
                        b['cemetery'],
                        b['area'],
                        b['row'],
                        b['place'],
                        b['grave_number'],
                        b['deadman'],
                        b['fact_date'],
                        b['deadman_dob'],
                        b['deadman_dod'],
                        b['burial_comments'],
                        b['burial_type'],
                        b['applicant'],
                        b['applicant_address'],
                        b['deadman_address'],
                        b['dt_modified'],
                        b['cemetery_id'],
                        b['area_id'],
                        b['place_id'],
                        b['burial_id'],
                    )).commit()
                    log_("    UPDATEd burial_id: %s " % b['burial_id'])
                else:
                    cursor.execute(r"""
                        INSERT INTO
                            burials
                        (
                            cemetery,
                            area,
                            row,
                            place,
                            grave_number,
                            deadman,
                            fact_date,
                            deadman_dob,
                            deadman_dod,
                            burial_comments,
                            burial_type,
                            applicant,
                            applicant_address,
                            deadman_address,
                            dt_modified,
                            cemetery_id,
                            area_id,
                            place_id,
                            burial_id
                        )
                        VALUES
                        (
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?
                        )
                    """, (
                        b['cemetery'],
                        b['area'],
                        b['row'],
                        b['place'],
                        b['grave_number'],
                        b['deadman'],
                        b['fact_date'],
                        b['deadman_dob'],
                        b['deadman_dod'],
                        b['burial_comments'],
                        b['burial_type'],
                        b['applicant'],
                        b['applicant_address'],
                        b['deadman_address'],
                        b['dt_modified'],
                        b['cemetery_id'],
                        b['area_id'],
                        b['place_id'],
                        b['burial_id'],
                    )).commit()
                    log_("    INSERTed burial_id: %s " % b['burial_id'])

    log_(" OK")

    scram(0, "Success")

class ServiceException(Exception):
    pass

def scram(code=0, message=None):
    """
    Выйти из сценария с кодом возврата, возможно с сообщением на консоль
    """
    global f_log, cursor, connection
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    if message:
        log_(message)
    if f_log:
        f_log.close()
    quit(code)

def log_(*args, **kwargs):

    global f_log
    s = " ".join([str(s) for s in args])
    s = "%s %s" % (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        s,
    )
    if f_log:
        f_log.write("%s\n" % s)
    else:
        print(s)

def request_json(path, method='GET', token=None, data=None):
    """
    Выполнить запрос на сервер. Возвращает код (типа "OK 200")  и данные

    path:       (!) относительный url запроса. Часть, относящаяся
                    к серверу, подставляется из settings.py
    data        при методах, отличных от GET, dict
    token       для авторизации: 'Authorization: Token %s' % token
    method      отработаны методы GET и POST
    """

    msg_no_connection = "Connection to online source failed"

    try:
        online_url = settings.ONLINE_URL
        while online_url.endswith('/'):
            online_url = online_url[:-1]
        while path.startswith('/'):
            path = path[1:]
        req = urllib.request.Request("%s/%s" % (
            settings.ONLINE_URL,
            path
        ))
        if method.upper() == 'GET':
            jsondata = None
        else:
            req.add_header('Content-Type', 'application/json; charset=utf-8')
            jsondata = json.dumps(data).encode('utf-8')
            req.add_header('Content-Length', len(jsondata))
        req.get_method = lambda: method
        if token:
            req.add_header('Authorization', 'Token %s' % token)
        try:
            response = urllib.request.urlopen(req, jsondata, timeout=settings.ONLINE_TIMEOUT)
        except urllib.error.URLError:
            raise ServiceException(msg_no_connection)

        raw_data = response.read().decode('utf-8')
        try:
            return response.getcode(), json.loads(raw_data)
        except ValueError:
            raise ServiceException(msg_no_connection)
    except ServiceException as excpt:
        scram(code=1, message="ERROR: %s" % excpt.args[0])

main()
