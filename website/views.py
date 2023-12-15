from flask import Blueprint,render_template,request,jsonify,url_for,redirect,session
from website import db_connect, extract_shop_datas
from decimal import Decimal
from psycopg2.errors import ForeignKeyViolation 
from datetime import datetime,time,timedelta

views = Blueprint('views',__name__)

@views.route("/")
def home():
    if 'pg_username' in session and 'pg_id' in session:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT count(id) FROM user_auth WHERE pending = 'f';")
        noti_counts = cur.fetchall()[0][0]
        credentials , b_units = extract_shop_datas(cur)
        return render_template('home.html',noti_counts=noti_counts,credentials=credentials,b_units = b_units)
    return redirect(url_for('auth.authenticate',typ='log'))

@views.route("/get-graph-report/<start_dt>/<end_dt>/<bi>/<shop>/<report_type>")
@views.route("/get-report",methods=['GET','POST'])
def get_report(start_dt=None,end_dt=None,bi=None,shop=None,report_type=None):
    if request.method == 'POST' or start_dt:
        if not start_dt and not end_dt:
            start_dt = request.form.get('start-dt')
            end_dt = request.form.get('end-dt')
            bi = request.form.get('bi')
            shop = request.form.get('shop') 
            report_type = request.form.get('report-type')
        else:
            if 'pg_username' not in session or "pg_id" not in session:
                return redirect(url_for('views.home'))
        conn = db_connect()
        cur = conn.cursor()
        mgs = None
        credentials , b_units = extract_shop_datas(cur)
        # all shop , units owned by user
        all_unit_by_users = ",".join([str(dt[0]) for dt in b_units])
        all_shop_by_users = ",".join([str(data[2]) for data in credentials])
        # where clause for eachjob
        where_clause = ""
        where_clause += f"AND ej.business_unit_id in ({bi}) " if bi != '0' else f"AND ej.business_unit_id IN ({all_unit_by_users}) "
        where_clause += f"AND ej.shop_id in ({shop}) " if shop != '0' else f"AND ej.shop_id IN ({all_shop_by_users}) "
        # where clause for technicians
        technician_where_clause = ""
        technician_where_clause = f"AND shop.business_unit_id in ({bi if bi != '0' else all_unit_by_users})"
        technician_where_clause += f"AND transfer.to_shop_id in ({shop if shop != '0' else all_shop_by_users})" 
        # job_types
        print(report_type)
        cur.execute(f"SELECT id,name FROM jobType WHERE team_id IN ({report_type}) ORDER BY id;")
        job_types = cur.fetchall()

        cur.execute(f""" SELECT tech.id,tech.name FROM technicians tech
                            INNER JOIN (
                                SELECT technician_id, to_shop_id FROM technicians_transfer
                                WHERE 
                                    '{start_dt}' BETWEEN from_date AND to_date
                                            OR
                                    '{start_dt}' >= from_date AND to_date IS NULL 
                            ) AS transfer
                        ON transfer.technician_id = tech.id
                            INNER JOIN shop 
                        ON shop.id = transfer.to_shop_id
                        WHERE tech.id != 0 {technician_where_clause} AND tech.team_id IN ({report_type}) ORDER BY tech.id;""")
        technicians_ids = cur.fetchall()
        technicians_names = [tech[1] for tech in technicians_ids]
        if len(technicians_names) == 0:
            mgs = "No Technician found for your specified unit and shop.."
            return render_template('report_graph_view.html',mgs=mgs,credentials=credentials,b_units=b_units)
        else:
            print(job_types)
            print(report_type, "this is report type")
            get_job_types = {job_type[0]:job_type[1] for job_type in job_types}
            total_result = {job_type[0]:[] for job_type in job_types}
            total_result[0] = []
            if '/get-graph-report' in request.path:
                total_result = [
                    ['Amount'] + list(get_job_types.values()) + ['Total',{ 'role': 'annotation'}]
                ]
            lst_data = [Decimal('0.0') for i in technicians_names]
            get_job_types[0] = 'TOTAL'
            for idx,technician_id in enumerate(technicians_ids):
                cur.execute(f"""
                SELECT jt.id AS job_type_id,
                    COALESCE(SUM(
                            CASE WHEN ej.fst_pic_id = {technician_id[0]} THEN ej.fst_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.sec_pic_id = {technician_id[0]} THEN ej.sec_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.thrd_pic_id = {technician_id[0]} THEN ej.thrd_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.frth_pic_id = {technician_id[0]} THEN ej.frth_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.lst_pic_id = {technician_id[0]} THEN ej.lst_pic_amt ELSE 0.0 END
                        ), 0.0) AS total_sum
                FROM (
                    SELECT id
                    FROM jobtype
                    WHERE team_id IN ({report_type})
                    ) AS jt
                CROSS JOIN (
                    SELECT DISTINCT month_extracted
                    FROM eachJobForm
                ) AS months
                LEFT JOIN (
                    SELECT form.month_extracted,form.business_unit_id,form.shop_id,form.job_date,line.job_type_id,line.fst_pic_id,line.sec_pic_id,line.thrd_pic_id,line.frth_pic_id,line.lst_pic_id,
                            line.fst_pic_amt,line.sec_pic_amt,line.thrd_pic_amt,line.frth_pic_amt,line.lst_pic_amt
                    FROM eachJobForm AS form
                    INNER JOIN eachJobLine AS line
                    ON form.id = line.form_id
                    WHERE form.job_date BETWEEN '{start_dt}' AND '{end_dt}'
                ) AS ej ON jt.id = ej.job_type_id AND months.month_extracted = ej.month_extracted
                {where_clause} 
                GROUP BY jt.id
                ORDER BY jt.id;""")
                datas = cur.fetchall()
                print(datas,"all datas")
                if '/get-graph-report' in request.path:
                    data = [dt[1] for dt in datas]
                    total_result.append([technicians_names[idx]]+data+[sum(data),str(sum(data))])
                else:
                    for data in datas:
                        lst_data[idx] += data[1]
                        total_result[data[0]].append(data[1])
                shop_name = "All Shops"
                if shop != "0":
                    cur.execute("SELECT name FROM shop WHERE id = %s;",(shop,))
                    shop_name = cur.fetchall()[0][0]
            if '/get-graph-report' in request.path:
                return jsonify(total_result)
            else:
                total_result[0] = lst_data
    else:
        return redirect(url_for('views.home'))
    for k,v in total_result.items():
        v.insert(0,sum(v))
    return render_template('report_graph_view.html',extra_datas=[['TYPE TOTAL'] + technicians_names,get_job_types,start_dt,end_dt,shop_name,'{:,.2f}'.format(total_result[0][0])],total_result = total_result,credentials=credentials,b_units=b_units,mgs=mgs)

@views.route("time-report/<typ>",methods=['GET','POST'])
def check_in_out_report(typ='in-out'):
    if 'pg_username' not in session or "pg_id" not in session:
        return redirect(url_for('views.home'))
    if request.method == 'POST':
        conn = db_connect()
        cur = conn.cursor()

        ## getting shop id and unit id 
        bi = request.form.get('bi')
        shop = request.form.get('shop')
        report_type = request.form.get('report-type')
        credentials , b_units = extract_shop_datas(cur)
        # all shop , units owned by user
        all_unit_by_users = ",".join([str(dt[0]) for dt in b_units])
        all_shop_by_users = ",".join([str(data[2]) for data in credentials])
        # where clause for eachjob
        where_clause = ""
        where_clause += f"AND ej.business_unit_id in ({bi}) " if bi != '0' else f"AND ej.business_unit_id IN ({all_unit_by_users}) "
        where_clause += f"AND ej.shop_id in ({shop}) " if shop != '0' else f"AND ej.shop_id IN ({all_shop_by_users}) "
        # where clause for technicians
        technician_where_clause = ""
        technician_where_clause = f"AND shop.business_unit_id in ({bi if bi != '0' else all_unit_by_users})"
        technician_where_clause += f"AND transfer.to_shop_id in ({shop if shop != '0' else all_shop_by_users})"

        start_dt = datetime.strptime(request.form.get('start-dt'), '%Y-%m-%d')
        details_or_not = request.form.get('summary')
        print(details_or_not)

        mgs = None
        ## getting shop name 
        if shop == '0':
            shop_name = 'ALL SHOPS'
        else:
            cur.execute("SELECT name FROM shop WHERE id = %s;",(shop,))        
            shop_name = cur.fetchone()[0]

        total_result = {}
        
        cur.execute(f""" SELECT tech.id,tech.name FROM technicians tech
                            INNER JOIN (
                                SELECT technician_id, to_shop_id FROM technicians_transfer
                                WHERE 
                                    '{start_dt}' BETWEEN from_date AND to_date
                                            OR
                                    '{start_dt}' >= from_date AND to_date IS NULL 
                            ) AS transfer
                        ON transfer.technician_id = tech.id
                            INNER JOIN shop 
                        ON shop.id = transfer.to_shop_id
                        WHERE tech.id != 0  {technician_where_clause} AND tech.team_id IN ({report_type}) ORDER BY tech.id;""")
        technicians_ids = cur.fetchall()

        if len(technicians_ids) == 0:
            mgs = "No Technician found for your specified unit and shop.."
            return render_template('check_in_out_report.html',mgs=mgs,total_result=total_result,extra_datas = [start_dt, shop_name, 'Test', {}, {}],typ = typ,credentials = credentials,b_units=b_units,result_datas={})
        ## check condition for summary
        elif not details_or_not:
            only_tech_ids = tuple([tech_id[0] for tech_id in technicians_ids])
            end_dt = datetime.strptime(request.form.get('end-dt'), '%Y-%m-%d')
            typ = "summary"
            cur.execute("SELECT generate_series(%s,%s,'1 day'::interval)::date AS job_date;",(start_dt,end_dt))
            date_datas = cur.fetchall()
            if len(date_datas) == 1:
                mgs = "Summary Report must be within date range , not on a single day.."
            else:
                total_result = { (tech_id,each_date[0]):[0,'',8,'8:00',0,'']    for tech_id in only_tech_ids for each_date in date_datas}
                # print(total_result)
                cur.execute(""" 
                            (
                                WITH date_ranges AS (
                                    SELECT
                                        technician_id,
                                        leave_type_id,
                                        generate_series(
                                            start_date,
                                            end_date,
                                            '1 day'::interval
                                        )::date AS job_date,
                                        start_date::time AS start_time,
                                        end_date::time AS end_time
                                    FROM
                                        leaves
                                    )
                                SELECT DISTINCT ON (technician_id, job_date)
                                    technician_id,
                                    job_date,
                                    '0:00:00' AS total_working_hours,
                                    '0:00:00' AS overtime,
                                    lt.name || '(' || 
                                    CASE
                                        WHEN start_time = '12:00:00' AND end_time = '00:00:00' THEN 'EVENING'
                                        WHEN start_time = '00:00:00' AND end_time = '12:00:00' THEN 'MORNING'
                                        ELSE 'WHOLE'
                                    END || ')' AS duration
                                FROM
                                    date_ranges
                                INNER JOIN leave_type AS lt
                                    ON lt.id = date_ranges.leave_type_id
                                WHERE technician_id IN %s   AND job_date BETWEEN %s AND %s
                                ORDER BY
                                    technician_id,
                                    job_date,
                                    CASE
                                        WHEN start_time = '00:00:00' AND end_time = '00:00:00' THEN 1
                                        WHEN start_time = '12:00:00' AND end_time = '00:00:00' THEN 2
                                        WHEN start_time = '00:00:00' AND end_time = '12:00:00' THEN 3
                                        ELSE 4
                                    END
                            )
                                UNION ALL
                            ( 
                                SELECT technician_id,form.job_date, SUM(end_time - start_time ) AS total_working_hours,
                                    SUM(
                                        ( CASE
                                            WHEN start_time <= '8:30:00' AND end_time <= '8:30:00'
                                                THEN end_time - start_time 
                                            WHEN start_time <= '8:30:00' AND end_time >= '8:00:00'
                                                THEN '8:30:00' - start_time
                                            ELSE '00:00:00'
                                        END ) + -- morning overtime
                                        (CASE	
                                            WHEN start_time <= '12:00:00' AND  ( end_time BETWEEN '12:00:00' AND '13:00:00' )
                                                THEN end_time - '12:00:00'
                                            WHEN end_time >= '13:00:00' AND ( start_time BETWEEN '12:00:00' AND '13:00:00' )
                                                THEN '13:00:00' - start_time
                                            WHEN  ( start_time BETWEEN '12:00:00' AND '13:00:00' ) AND ( end_time BETWEEN '12:00:00' AND '13:00:00' )
                                                THEN end_time - start_time
                                            WHEN start_time <= '12:00:00' AND end_time >= '13:00:00' 
                                                THEN '1:00:00'
                                            ELSE '00:00:00'
                                        END ) + -- noon overtime 
                                        ( CASE
                                            WHEN start_time <= '17:30:00' AND end_time >= '17:30:00'
                                                THEN end_time - '17:30:00' 
                                            WHEN start_time >= '17:30:00' AND end_time >= '17:30:00'
                                                THEN end_time - start_time
                                            ELSE '00:00:00'
                                        END ) -- evening overtime
                                    ) AS overtime,
                                    '' AS duration
                                FROM checkinoutline AS line
                                    INNER JOIN checkinoutform AS form
                                ON line.form_id = form.id
                                    WHERE technician_id IN %s  AND form.job_date BETWEEN %s AND %s
                                GROUP BY technician_id,form.job_date
                                ORDER BY technician_id,form.job_date 
                            )
                """,(only_tech_ids,start_dt,end_dt,only_tech_ids,start_dt,end_dt))
                temp_result = cur.fetchall()
                for each_data in temp_result:
                    print(each_data)
                    data = total_result[(each_data[0],each_data[1])]
                    # if each_data[4] != '' or data[5] != '':                    
                    if each_data[4] != '' or data[5] != '':
                        if each_data[4].endswith("EVENING)"):
                            leave_hour = 4.5
                        elif each_data[4].endswith("MORNING)"):
                            leave_hour = 3.5
                        else:
                            leave_hour = 8
                        data[2] = 0
                        data[3] = ''
                        data[4] = leave_hour
                        data[5] = data[5] if each_data[4] == '' and data[5] != '' else each_data[4]
                    else:
                        data[0] = round(each_data[2].seconds / 3600 + each_data[2].days * 24,2)
                        data[1] = f"{each_data[2].seconds // 3600:02}:{(each_data[2].seconds % 3600) // 60:02}"
                        idle_time = timedelta(seconds=28800) - (each_data[2] - each_data[3])
                        data[2] = round(idle_time.seconds / 3600 + idle_time.days * 24,2)
                        data[3] = f"{idle_time.seconds // 3600:02}:{(idle_time.seconds % 3600) // 60:02}"                        
                    print(data)
            # print(typ)
            # print(total_result)
            return render_template('check_in_out_report.html',divider=len(date_datas),technicians_ids=technicians_ids,result_datas=total_result,total_result={},extra_datas = [start_dt, shop_name, end_dt, {}, {}],typ = "summary",credentials = credentials,b_units=b_units,mgs=mgs)
        


        total_result = {}
        morning_idles = {}
        evening_idles = {}
        idle_report = False

        cur.execute(""" 
                    SELECT tech.name,
                        'LEAVE' || '(' ||
                        CASE
                            WHEN ROUND(EXTRACT(EPOCH FROM (end_date - start_date)) / 86400,1) = 0.5
                                THEN CASE 
                                        WHEN EXTRACT(HOUR FROM start_date) = 12 
                                            THEN 'EVENING'
                                        ELSE 'MORNING'
                                    END
                            ELSE 'WHOLE'
                        END || ')' FROM leaves
                    INNER JOIN technicians AS tech
                    ON tech.id = leaves.technician_id
                    WHERE leaves.technician_id in %s AND %s BETWEEN leaves.start_date AND leaves.end_date;
        """,(tuple([tech_id[0] for tech_id in technicians_ids]),start_dt))
        leave_badges = cur.fetchall()
        leave_badges = leave_badges if len(leave_badges) == 0 else {data[0]:data[1] for data in leave_badges}

        # print(technicians_ids)
        # print(leave_badges)

        if typ == 'idle': 
            idle_report = True
            morning_upper_threshold = datetime.combine(datetime.today(),time(8, 30))
            morning_lower_threshold = datetime.combine(datetime.today(),time(12, 0))
            evening_upper_threshold = datetime.combine(datetime.today(),time(13, 0))
            evening_lower_threshold = datetime.combine(datetime.today(),time(17, 30))

        for technician_id in technicians_ids:
            cur.execute(""" select
                        descript.name,
                        type.name,
                        car.plate,
                        brand.name || ' - ' || model.name,
                        line.start_time,
                        line.end_time,
                        line.end_time - line.start_time,
                        line.technician_id
                        from checkinoutline as line
                        inner join checkinoutform as form
                        on line.form_id = form.id
                        left join technicians as tech
                        on tech.id = line.technician_id
                        left join descriptions as descript
                        on descript.id = line.description_id
                        left join jobtype as type
                        on type.id = line.job_type_id
                        left join vehicle as car
                        on car.id = form.vehicle_id
                        left join vehicle_brand as brand
                        on brand.id = car.brand_id
                        left join vehicle_model as model
                        on model.id = car.model_id
                        where line.technician_id = %s and form.job_date = %s
                        order by line.start_time;""",(technician_id[0],start_dt))
            data = cur.fetchall()
            total_result[technician_id[1]] = data


            if typ == 'idle':
                morning_idle = []
                evening_idle = []
                if data == []:
                    morning_idle.append((morning_upper_threshold,morning_lower_threshold))
                    evening_idle.append((evening_upper_threshold,evening_lower_threshold))
                temp_time = datetime.combine(datetime.today(),time(8, 30))
                for idx,each_job in enumerate(data):
                    # print(each_job)
                    start_time = datetime.combine(datetime.today(),each_job[4])
                    end_time = datetime.combine(datetime.today(),each_job[5])
                    if idx != 0 and idx != len(data)-1:
                        if start_time > morning_lower_threshold and temp_time < morning_lower_threshold:
                            morning_idle.append((temp_time,morning_lower_threshold))
                            print("Diff time is ",temp_time,datetime.combine(datetime.today(),time(12, 0)))
                        if start_time > temp_time:
                            if start_time <= morning_lower_threshold:
                                print("Morning idle with no threshold ",temp_time,start_time)
                                morning_idle.append((temp_time,start_time))
                            elif morning_upper_threshold < start_time < evening_upper_threshold:
                                morning_idle.append((temp_time,morning_lower_threshold))
                            elif start_time >= evening_upper_threshold and start_time <= evening_lower_threshold:
                                evening_idle.append((evening_upper_threshold,start_time))
                            elif start_time >= evening_lower_threshold:
                                evening_idle.append((evening_upper_threshold,evening_lower_threshold))
                            print("Diff time is ",temp_time,start_time)
                        temp_time = end_time
                    else:
                        if idx == 0:
                            if start_time <= morning_lower_threshold:
                                if start_time > morning_upper_threshold:
                                    morning_idle.append((morning_upper_threshold,start_time))
                                    print("Diff is",datetime.combine(datetime.today(),time(8, 30)),start_time)
                                else:
                                    print("No Diff for morning")
                            else:
                                morning_idle.append((morning_upper_threshold,morning_lower_threshold))
                                print("Diff is",datetime.combine(datetime.today(),time(8, 0)),datetime.combine(datetime.today(),time(12, 0)))
                                if start_time > evening_upper_threshold:
                                    evening_idle.append((evening_upper_threshold,start_time))
                                    print("Diff is",datetime.combine(datetime.today(),time(13, 0)),start_time)
                                else:
                                    print("No diff for evevning")
                            temp_time = end_time
                        if idx == len(data) - 1:
                            if start_time > temp_time:
                                if start_time <= morning_lower_threshold:
                                    print("Morning idle with no threshold ",temp_time,start_time)
                                    morning_idle.append((temp_time,start_time))
                                elif morning_upper_threshold < start_time < evening_upper_threshold:
                                    morning_idle.append((temp_time,morning_lower_threshold))
                                elif start_time >= evening_upper_threshold and start_time <= evening_lower_threshold and temp_time >= evening_upper_threshold:
                                    evening_idle.append((temp_time,start_time))
                                elif start_time >= evening_upper_threshold and start_time <= evening_lower_threshold:
                                    evening_idle.append((evening_upper_threshold,start_time))
                                elif start_time >= evening_lower_threshold:
                                    evening_idle.append((evening_upper_threshold,evening_lower_threshold))
                                print("Diff time is ",temp_time,start_time)
                            if end_time <= morning_lower_threshold:
                                if end_time < morning_lower_threshold:
                                    morning_idle.append((end_time, morning_lower_threshold))
                                    print("Diff is",end_time,datetime.combine(datetime.today(),time(12, 0)))
                                else:
                                    print("No Diff for morning")
                                evening_idle.append((evening_upper_threshold,evening_lower_threshold))
                                print("Diff is ",datetime.combine(datetime.today(),time(13, 0)),datetime.combine(datetime.today(),time(17, 0)))                        
                            else:
                                if start_time > morning_lower_threshold and temp_time < morning_lower_threshold:
                                    morning_idle.append((temp_time,morning_lower_threshold))
                                    print("Diff time is ",temp_time,datetime.combine(datetime.today(),time(12, 0)))
                                if end_time < evening_lower_threshold:
                                    evening_idle.append((end_time, evening_lower_threshold))
                                    print("Diff is",end_time,datetime.combine(datetime.today(),time(17, 0)))
                                else:
                                    print("No diff for evevning")
                            temp_time = end_time
                    
                # print("morning idle list is ",morning_idle)
                # print("evening idle list is ",evening_idle)
                morning_idles[technician_id[1]] = morning_idle
                evening_idles[technician_id[1]] = evening_idle

        # print("morning idle is",morning_idles)
        # print("evening idle is",evening_idles)
        # print(total_result)
    else:
        return redirect(url_for('views.home'))
    
    return render_template('check_in_out_report.html',total_result=total_result,extra_datas = [start_dt, shop_name, idle_report, morning_idles, evening_idles],typ = typ,credentials=credentials,b_units=b_units, mgs=mgs,leave_badges = leave_badges,result_datas={},technicians_ids=[],divider=0)
        
@views.route("job-analysis-report",methods=['GET','POST'])
def job_analysis_report():
    if 'pg_username' not in session or "pg_id" not in session:
        return redirect(url_for('views.home'))
    if request.method == 'POST':
        conn = db_connect()
        cur = conn.cursor()
        start_dt = request.form.get('start-dt')
        end_dt = request.form.get('end-dt')
        bi_id = request.form.get('bi')
        shop_id = request.form.get('shop')
        #
        credentials , b_units = extract_shop_datas(cur)
        # where clause for technicians
        technician_where_clause = ""
        technician_where_clause = f""" AND form.business_unit_id in ({bi_id if bi_id != '0' else ",".join([str(dt[0]) for dt in b_units])})"""
        technician_where_clause += f""" AND form.shop_id in ({shop_id if shop_id != '0' else ",".join([str(data[2]) for data in credentials])})"""  
        print(start_dt)
        print(end_dt)  
        
        cur.execute(f""" SELECT form.id,form.job_date,form.job_no,form.tech_count,CASE WHEN form.total_min < 60 THEN form.total_min || ' Mins' ELSE    
                            FLOOR(form.total_min/60) || ' Hrs ' || ROUND(form.total_min%60) || ' Mins ' END,form.total_amt,tech.name,
                            descript.name,line.end_time - line.start_time  FROM checkinoutline AS line
                        INNER JOIN
                            (
                                SELECT time_form.id AS id,MAX(service_form.job_no) AS job_no,MAX(service_form.total_amt) AS total_amt,COUNT(DISTINCT time_line.technician_id) AS tech_count,
                                    EXTRACT(HOUR FROM SUM(time_line.end_time - time_line.start_time)) * 60 +
                                    EXTRACT(MINUTE FROM SUM(time_line.end_time - time_line.start_time))
                                    AS total_min,MAX(service_form.job_date) AS job_date
                                FROM checkinoutform AS time_form
                                    INNER JOIN checkinoutline AS time_line
                                ON time_form.id = time_line.form_id
                                    INNER JOIN (
                                        SELECT MAX(form.job_no) AS job_no ,form.id,SUM(line.total_amt) AS total_amt,MAX(form.job_date) AS job_date FROM eachJobForm AS form
                                            INNER JOIN eachJobline AS line
                                        ON form.id = line.form_id
                                            WHERE form.job_date BETWEEN '{start_dt}' AND '{end_dt}'  {technician_where_clause}
                                        GROUP BY form.id
                                    ) AS service_form
                                ON service_form.id = time_form.form_id
                                GROUP BY time_form.id
                            ) AS form
                        ON form.id = line.form_id
                            LEFT JOIN technicians AS tech
                        ON tech.id = line.technician_id
                                        LEFT JOIN descriptions AS descript
                                    ON descript.id = line.description_id
                        ORDER BY form.job_date,form.job_no;""")
        datas = cur.fetchall()  
        print(datas) 
        result = {}
        for data in datas:
            keyy = data[:6]
            if keyy not in result:
                result[keyy] = [data[6:]]
            else:
                result[keyy].append(data[6:])     
        if shop_id == '0':
            shop_name = 'ALL SHOPS'
        else:
            cur.execute("SELECT name FROM shop WHERE id = %s;",(shop_id,))        
            shop_name = cur.fetchone()[0]
        print(result)
        return render_template('job_analysis.html',result=result,extra_datas = [start_dt,end_dt,shop_name], credentials=credentials, b_units=b_units)
    return redirect('views.home')

@views.route("pic-report",methods=['GET','POST'])
def pic_report():
    if 'pg_username' not in session or "pg_id" not in session:
        return redirect(url_for('views.home'))
    if request.method == 'POST':
        conn = db_connect()
        cur = conn.cursor()
        start_dt = request.form.get('start-dt')
        end_dt = request.form.get('end-dt')
        bi_id = request.form.get('bi')
        shop_id = request.form.get('shop')
        report_type = request.form.get('report-type')

        credentials , b_units = extract_shop_datas(cur)
        # all shop , units owned by user
        all_unit_by_users = ",".join([str(dt[0]) for dt in b_units])
        all_shop_by_users = ",".join([str(data[2]) for data in credentials])
        # where clause for eachjob
        where_clause = ""
        where_clause += f"AND ej.business_unit_id in ({bi_id}) " if bi_id != '0' else f"AND ej.business_unit_id IN ({all_unit_by_users}) "
        where_clause += f"AND ej.shop_id in ({shop_id}) " if shop_id != '0' else f"AND ej.shop_id IN ({all_shop_by_users}) "
        # where clause for technicians
        technician_where_clause = ""
        technician_where_clause = f"AND shop.business_unit_id in ({bi_id if bi_id != '0' else all_unit_by_users})"
        technician_where_clause += f"AND transfer.to_shop_id in ({shop_id if shop_id != '0' else all_shop_by_users})" 



        cur.execute(f"SELECT id,name FROM jobType WHERE team_id IN ({report_type}) ORDER BY id;")
        job_types = cur.fetchall()

        print(job_types)

        cur.execute(f""" SELECT tech.id,tech.name FROM technicians tech
                    INNER JOIN (
                        SELECT technician_id, to_shop_id FROM technicians_transfer
                        WHERE 
                            '{start_dt}' BETWEEN from_date AND to_date
                                    OR
                            '{start_dt}' >= from_date AND to_date IS NULL 
                    ) AS transfer
                ON transfer.technician_id = tech.id
                    INNER JOIN shop 
                ON shop.id = transfer.to_shop_id
                WHERE tech.id != 0 {technician_where_clause} AND tech.team_id IN ({report_type}) ORDER BY tech.id;""")
        technicians_ids = cur.fetchall()
        if len(technicians_ids) == 0:
            mgs = 'No technicians found for your specific shop and business unit id..'
            return render_template('pic_report.html',mgs=mgs,credentials=credentials,b_units=b_units)
        technicians_names = [tech[1] for tech in technicians_ids]
        total_result = {}

        for idx,technician_id in enumerate(technicians_ids):
            query = f""" 
                        SELECT
                            jt.id,
                            COALESCE(SUM(
                                CASE WHEN ej.fst_pic_id = {technician_id[0]} THEN ej.fst_pic_amt ELSE 0.0 END +
                                CASE WHEN ej.sec_pic_id = {technician_id[0]} THEN ej.sec_pic_amt ELSE 0.0 END +
                                CASE WHEN ej.thrd_pic_id = {technician_id[0]} THEN ej.thrd_pic_amt ELSE 0.0 END +
                                CASE WHEN ej.frth_pic_id = {technician_id[0]} THEN ej.frth_pic_amt ELSE 0.0 END +
                                CASE WHEN ej.lst_pic_id = {technician_id[0]} THEN ej.lst_pic_amt ELSE 0.0 END
                            ), 0.0) AS total_sum,
                            COALESCE(SUM(CASE WHEN ej.fst_pic_id = {technician_id[0]} THEN ej.fst_pic_amt ELSE 0.0 END), 0.0) AS pic_1,
                            COALESCE(SUM(CASE WHEN ej.sec_pic_id = {technician_id[0]} THEN ej.sec_pic_amt ELSE 0.0 END), 0.0) AS pic_2,
                            COALESCE(SUM(CASE WHEN ej.thrd_pic_id = {technician_id[0]} THEN ej.thrd_pic_amt ELSE 0.0 END), 0.0) AS pic_3,
                            COALESCE(SUM(CASE WHEN ej.frth_pic_id = {technician_id[0]} THEN ej.frth_pic_amt ELSE 0.0 END), 0.0) AS pic_4,
                            COALESCE(SUM(CASE WHEN ej.lst_pic_id = {technician_id[0]} THEN ej.lst_pic_amt ELSE 0.0 END), 0.0) AS pic_5
                        FROM (
                            SELECT id
                            FROM jobtype WHERE team_id IN ({report_type})
                        ) AS jt
                        CROSS JOIN (
                            SELECT DISTINCT month_extracted
                            FROM eachJobForm
                        ) AS months
                        LEFT JOIN (
                            SELECT form.month_extracted,form.business_unit_id,form.shop_id,form.job_date,line.job_type_id,line.fst_pic_id,line.sec_pic_id,line.thrd_pic_id,line.frth_pic_id,line.lst_pic_id,
                                    line.fst_pic_amt,line.sec_pic_amt,line.thrd_pic_amt,line.frth_pic_amt,line.lst_pic_amt
                            FROM eachJobForm AS form
                            INNER JOIN eachJobLine AS line
                            ON form.id = line.form_id
                            WHERE form.job_date BETWEEN '{start_dt}' AND '{end_dt}'
                        ) AS ej ON jt.id = ej.job_type_id AND months.month_extracted = ej.month_extracted
                            {where_clause}
                        GROUP BY jt.id
                        ORDER BY jt.id;
                    """          
            cur.execute(query)
            datas = cur.fetchall()
            result = [[] for _ in range(7)]
            for data in datas:
                for i,dt in enumerate(data[1:]):
                    result[i].append('{:,.2f}'.format(dt))
            sum_of_first_column = sum(float(value.replace(',', '')) for value in result[0])
            formatted_sum = '{:,.2f}'.format(sum_of_first_column)
            result[0].append(formatted_sum)
            result = [item for subitem in result for item in subitem]
            total_result[technicians_names[idx]] = result
            if shop_id == '0':
                shop_name = 'ALL SHOPS'
            else:
                cur.execute("SELECT name FROM shop WHERE id = %s;",(shop_id,))        
                shop_name = cur.fetchall()[0][0]
            print(job_types)
    else:
        return redirect(url_for('views.home'))
    return render_template('pic_report.html',total_result=total_result,job_types=job_types,extra_datas = [start_dt,end_dt,shop_name],credentials =credentials , b_units = b_units)


@views.route("/show-datas/<typ>/<mgs>",methods=['GET'])
@views.route("/show-datas/<typ>",methods=['GET','POST'])
def show_service_datas(typ,mgs=None):
    if 'pg_username' not in session or "pg_id" not in session:
        return redirect(url_for('views.home'))
    mgs = request.args.get("mgs")
    conn = db_connect()
    cur = conn.cursor()
    credentials , b_units = extract_shop_datas(cur)
    user_roles_lst = ','.join([str(dt[2]) for dt in credentials])
    extra_datas = []
    if request.method == 'POST':
        filt = True
        column = request.form.get('column')
        db = request.form.get('database')
        val = request.form.get('filter')
        bol = request.form.get('editOrSubmit')
        print(column,'this is filter',bol)
        print(db)
        print(typ)
        if typ == 'service-datas':
            if db == 'eachJob':
                query = f""" WITH month_cte AS (
                    SELECT
                        month_id,
                        TO_CHAR(DATE_TRUNC('month', TIMESTAMP '2000-01-01'::date + (month_id-1  || ' months')::interval), 'Month') AS month_text
                    FROM generate_series(1, 12) AS month_id
                    )
                    SELECT 
                        month_cte.month_text,jb.job_date,unit.name,shop.name,jb.job_no,customer.name,vehicle.plate,model.name,
                        vehicle.year,jb.invoice_no,jb.id
                    FROM eachJobForm AS jb
                    LEFT JOIN month_cte
                    ON month_cte.month_id = jb.month_extracted
                    LEFT JOIN res_partner AS unit
                    ON unit.id = jb.business_unit_id
                    LEFT JOIN shop
                    ON shop.id = jb.shop_id
                    LEFT JOIN customer
                    ON customer.id = jb.customer_id
                    LEFT JOIN vehicle
                    ON vehicle.id = jb.vehicle_id
                    LEFT JOIN vehicle_model model
                    ON model.id = vehicle.model_id
                    WHERE {column} iLIKE '%{val}%' AND shop.id IN ({user_roles_lst})
                    ORDER BY jb.job_date DESC,job_no DESC;"""
                print(query)
                if eval(bol):
                    place_insert_query = f"jb.id = '{val}' "
                    with_id_query =f""" SELECT 
                                        jb.job_date,unit.id,shop.id,jb.job_no,customer.name,vehicle.plate,jb.customer_id,jb.vehicle_id,customer.address,
                                        customer.phone,state.name,model.name,brand.name,model.brand_id,model.id,vehicle.year,jb.invoice_no,jb.business_unit_id,
                                        jb.shop_id,line.job_name,jobType.name,line.total_amt,t_one.name,t_two.name,
                                        t_three.name,t_four.name,t_five.name,pic.unique_rate,jb.id
                                    FROM eachJobForm AS jb
                                    INNER JOIN eachJobLine AS line
                                    ON line.form_id = jb.id 
                                    LEFT JOIN res_partner AS unit
                                    ON unit.id = jb.business_unit_id
                                    LEFT JOIN shop
                                    ON shop.id = jb.shop_id
                                    LEFT JOIN customer
                                    ON customer.id = jb.customer_id
                                    LEFT JOIN vehicle
                                    ON vehicle.id = jb.vehicle_id
                                    LEFT JOIN jobType
                                    ON jobType.id = line.job_type_id
                                    LEFT JOIN technicians AS t_one
                                    ON t_one.id = line.fst_pic_id 
                                    LEFT JOIN technicians AS t_two
                                    ON t_two.id = line.sec_pic_id 
                                    LEFT JOIN technicians AS t_three
                                    ON t_three.id = line.thrd_pic_id 
                                    LEFT JOIN technicians AS t_four
                                    ON t_four.id = line.frth_pic_id 
                                    LEFT JOIN technicians AS t_five
                                    ON t_five.id = line.lst_pic_id 
                                    LEFT JOIN pic 
                                    ON pic.id = line.pic_rate_id
                                    LEFT JOIN vehicle_model model
                                    ON model.id = vehicle.model_id
                                    LEFT JOIN vehicle_brand brand
                                    ON brand.id = model.brand_id
                                    LEFT JOIN state
                                    ON state.id = customer.state_id
                                    WHERE {place_insert_query}
                                    ORDER BY jb.job_date DESC,job_no DESC;""" 
                    cur.execute(with_id_query)
                    print(with_id_query)
                    result = []
                    result.append(cur.fetchall())
                    print(result)
                    cur.execute("SELECT id,name FROM technicians WHERE shop_id = %s;",(result[0][0][18],))
                    result.append(cur.fetchall())
                    cur.execute("SELECT id,name FROM jobType;")
                    result.append(cur.fetchall())
                    cur.execute("SELECT unique_rate FROM pic;")
                    result.append(cur.fetchall())
                    result.append(datetime.now().year)
                    result.append(sum(data[21] for data in result[0]))
                    return render_template('edit_form.html',result = result,typ=typ, credentials = credentials,b_units=b_units)
                cur.execute(query)
                result = cur.fetchall()
                cur.execute(f"SELECT count(jb.id) FROM eachJobForm jb LEFT JOIN vehicle ON vehicle.id = jb.vehicle_id  LEFT JOIN res_partner AS unit ON unit.id = jb.business_unit_id LEFT JOIN shop ON shop.id = jb.shop_id LEFT JOIN customer ON customer.id = jb.customer_id WHERE {column} iLIKE '%{val}%';")
                length = cur.fetchall()
        elif typ == 'check-in-out':
            query = f""" SELECT MAX(form.job_date) , MAX(form.seq) , MAX(form.job_no) , MAX(car.plate) , MAX(brand.name) , MAX(model.name) , MAX(unit.name) , MAX(shop.name) , 
                            COUNT(DISTINCT line.technician_id), SUM(line.end_time - line.start_time) , 
                            CASE WHEN COUNT(form.form_id) > 0 THEN 'Approved' ELSE 'Draft' END  , form.id
                        FROM checkinoutform AS form
                        INNER JOIN checkinoutline AS line
                        ON form.id = line.form_id
                        LEFT JOIN vehicle AS car
                        ON car.id = form.vehicle_id
                        LEFT JOIN vehicle_brand AS brand
                        ON brand.id = car.brand_id
                        LEFT JOIN vehicle_model AS model
                        ON model.id = car.model_id
                        LEFT JOIN res_partner AS unit
                        ON unit.id = form.business_unit_id
                        LEFT JOIN shop AS shop
                        ON shop.id = form.shop_id
                        WHERE {column} iLIKE '%{val}%' AND shop.id IN ({user_roles_lst})
                        GROUP BY form.id
                        ORDER BY form.job_date DESC;"""
            if eval(bol):
                with_id_query = """ SELECT car.plate , car.id ,  form.job_date , form.job_no , brand.name , model.name , brand.id , model.id , car.year, unit.name , shop.name , form.id , 
                                    line.id , descriptions.name , tech.name , type.name , line.start_time , line.end_time , line.end_time - line.start_time , shop.id , form.form_id , line.description_id , tech.id , form.seq
                                    FROM checkinoutform AS form
                                    INNER JOIN checkinoutline AS line
                                    ON form.id = line.form_id
                                    LEFT JOIN descriptions
                                    ON descriptions.id = line.description_id
                                    LEFT JOIN vehicle AS car
                                    ON car.id = form.vehicle_id
                                    LEFT JOIN vehicle_brand AS brand
                                    ON brand.id = car.brand_id
                                    LEFT JOIN vehicle_model AS model
                                    ON model.id = car.model_id
                                    LEFT JOIN res_partner AS unit
                                    ON unit.id = form.business_unit_id
                                    LEFT JOIN shop AS shop
                                    ON shop.id = form.shop_id
                                    LEFT JOIN technicians AS tech
                                    ON tech.id = line.technician_id
                                    LEFT JOIN jobType AS type
                                    ON type.id = line.job_type_id
                                    WHERE form.id = %s
                                    ORDER BY line.start_time;""" 
                result = [[]]
                cur.execute("SELECT id,name FROM jobType;")
                result.append(cur.fetchall())
                cur.execute("SELECT id,short_name,name FROM state;")
                result.append(cur.fetchall())
                cur.execute("SELECT id,name FROM vehicle_brand;")
                result.append(cur.fetchall())
                result.append(datetime.now().year)
                cur.execute(with_id_query,(val,))
                result.append(cur.fetchall())
                result.append(sum([dt[18] for dt in result[5]],timedelta()))
                cur.execute("SELECT id,name FROM descriptions;")
                result.append(cur.fetchall())
                cur.execute("SELECT id,name FROM technicians WHERE shop_id = %s;",(result[5][0][19],))
                result.append(cur.fetchall())
                return render_template('edit_form.html',result = result,typ=typ, credentials = credentials ,b_units = b_units)
            cur.execute(query)
            result = cur.fetchall()
            print(result)
            cur.execute(f"SELECT count(jb.id) FROM checkinoutform AS jb LEFT JOIN vehicle ON vehicle.id = jb.vehicle_id  LEFT JOIN res_partner AS unit ON unit.id = jb.business_unit_id LEFT JOIN shop ON shop.id = jb.shop_id WHERE {column} iLIKE '%{val}%';")
            length = cur.fetchall()
        elif typ == 'psfu-calls':
            query = f""" 
                    SELECT form.job_date,unit.name,shop.name,form.job_no,car.plate,cus.name,cus.phone,status.name,psfu.remark,form.id,psfu.id FROM psfu_call AS psfu
                    INNER JOIN eachJobFORM AS form
                    ON form.id = psfu.form_id
                    LEFT JOIN vehicle car
                    ON car.id = form.vehicle_id
                    LEFT JOIN customer cus
                    ON cus.id = form.customer_id
                    LEFT JOIN call_status status
                    ON status.id = psfu.call_status_id
                    LEFT JOIN shop
                    ON shop.id = form.shop_id
                    LEFT JOIN res_partner unit
                    ON unit.id = shop.business_unit_id
                    WHERE form.shop_id in ({user_roles_lst}) AND psfu.call_status_id IS NOT NULL AND  {column} iLIKE '%{val}%'
                    ORDER BY form.job_date;
                """
            if eval(bol):
                cur.execute(""" 
                    SELECT form.job_date,unit.name,unit.id,shop.name,shop.id,form.job_no,car.plate,cus.name,cus.phone,status.name,psfu.remark,form.id,psfu.id FROM psfu_call AS psfu
                    INNER JOIN eachJobFORM AS form
                    ON form.id = psfu.form_id
                    LEFT JOIN vehicle car
                    ON car.id = form.vehicle_id
                    LEFT JOIN customer cus
                    ON cus.id = form.customer_id
                    LEFT JOIN call_status status
                    ON status.id = psfu.call_status_id
                    LEFT JOIN shop
                    ON shop.id = form.shop_id
                    LEFT JOIN res_partner unit
                    ON unit.id = shop.business_unit_id
                    WHERE psfu.id = %s;""",(val,))
                result = []
                result.append(cur.fetchone())
                cur.execute("SELECT id,name FROM call_status;")
                result.append(cur.fetchall())
                print(result)
                return render_template('edit_form.html',result = result,typ=typ, credentials = credentials ,b_units = b_units)
        elif typ == 'technician':
            query = f""" 
                SELECT 
                            tech.id,
                            tech.name,
                            bi.name,
                            CASE 
                                WHEN transfer.to_shop_id = 5 THEN 
                            'INACTIVE - ' || 
                                    (SELECT name FROM shop WHERE id = transfer.from_shop_id)
                                ELSE 
                                    shop.name
                            END AS shop_name,
                            team.name
                        FROM 
                            technicians tech
                        INNER JOIN (
                            SELECT 
                                technician_id, 
                                from_shop_id,
                                to_shop_id 
                            FROM 
                                technicians_transfer
                            WHERE 
                                (CURRENT_DATE BETWEEN from_date AND to_date OR CURRENT_DATE >= from_date AND to_date IS NULL)
                        ) AS transfer ON transfer.technician_id = tech.id
                        LEFT JOIN shop ON shop.id = transfer.to_shop_id
                        LEFT JOIN res_partner AS bi
                        ON bi.id = shop.business_unit_id
                        LEFT JOIN technician_team AS team
                        ON team.id = tech.team_id
                        WHERE 
                            tech.id != 0 AND ( 
                            (transfer.to_shop_id = 5 AND transfer.from_shop_id in ({user_roles_lst}) )
                                OR  
                                transfer.to_shop_id IN ({user_roles_lst})
                            ) AND {column}.name iLIKE '%{val}%'
                        ORDER BY 
                            tech.name;
            """
            query = f""" SELECT tech.id,tech.name,bi.name,shop.name,team.name
                        FROM technicians tech
                            INNER JOIN (
                                SELECT technician_id, to_shop_id FROM technicians_transfer
                                WHERE 
                                    CURRENT_DATE BETWEEN from_date AND to_date
                                            OR
                                    CURRENT_DATE >= from_date AND to_date IS NULL 
                            ) AS transfer
                        ON transfer.technician_id = tech.id
                            INNER JOIN shop
                        ON shop.id = transfer.to_shop_id
                            INNER JOIN res_partner bi
                        ON bi.id = shop.business_unit_id
                            LEFT JOIN technician_team AS team
                        ON team.id = tech.team_id
                            WHERE tech.id != 0 AND {column}.name iLIKE '%{val}%'  
                                AND transfer.to_shop_id IN ({user_roles_lst})
                        ORDER BY tech.name;"""
            if eval(bol):
                cur.execute(""" SELECT his.technician_id, tech.name, from_shop.name , to_shop.id ,to_shop.name, his.from_date, 
                                his.to_date,CASE
		                                        WHEN his.to_date IS NULL THEN 1
							                    WHEN CURRENT_DATE BETWEEN his.from_date AND his.to_date THEN 0
		                                        ELSE 2
                                            END AS flag_shop, tech.team_id , team.name
                                    FROM technicians_transfer AS his
                                LEFT JOIN technicians AS tech
                                    ON tech.id = his.technician_id
                                LEFT JOIN shop AS from_shop
                                    ON from_shop.id = his.from_shop_id
                                LEFT JOIN shop AS to_shop
                                    ON to_shop.id = his.to_shop_id
                                LEFT JOIN technician_team AS team
                                    ON team.id = tech.team_id
                                WHERE tech.id = %s
				                    ORDER BY flag_shop;""",(val,))
                result = []
                result.append(cur.fetchall())
                cur.execute("SELECT id,name FROM shop;")
                result.append(cur.fetchall())
                cur.execute("""SELECT lt.name,remark,start_date,end_date,end_date-start_date
                                FROM leaves 
                                INNER JOIN leave_type AS lt
                                ON lt.id = leaves.leave_type_id
                                WHERE technician_id = %s
                                ORDER BY start_date DESC;
                                """,(val,))
                result.append(cur.fetchall())
                cur.execute("SELECT id,name FROM technician_team;")
                result.append(cur.fetchall())
                # print(result)
                return render_template('edit_form.html',result = result,typ=typ, credentials = credentials ,b_units = b_units)
            cur.execute(query)
            result = cur.fetchall()
            db = 'technicians'
            cur.execute("SELECT name  FROM res_partner;")
            extra_datas.append(cur.fetchall())
            cur.execute("SELECT name  FROM shop;")
            extra_datas.append(cur.fetchall())
            length = [(len(result),)]
        elif typ == 'leaves':
            leave_type_id = request.form.get('leave_type_id')
            shop_id = request.form.get('shop_id')
            start_dt = request.form.get('start_dt')
            end_dt = request.form.get('end_dt')
            print(leave_type_id)
            print(shop_id)
            print(start_dt)
            print(end_dt)
            cur.execute("SELECT name FROM leave_type WHERE id = %s;",(leave_type_id,))
            leave_type_name = cur.fetchone()
            print(leave_type_name)
            if leave_type_name[0] == 'WHOLE SHOP LEAVE':
                cur.execute(""" SELECT shop.name,remark,start_date,end_date,ROUND(EXTRACT(EPOCH FROM (end_date - start_date)) / 86400,1)
                            FROM shop_leaves AS leaves
                            INNER JOIN shop 
                            ON shop.id = leaves.shop_id
                            WHERE start_date >= %s AND end_date <= %s;
                        """,(start_dt,end_dt))
            else:
                cur.execute("""SELECT tech.name,remark,start_date,end_date,ROUND(EXTRACT(EPOCH FROM (end_date - start_date)) / 86400,1)
                            FROM leaves
                            INNER JOIN technicians AS tech
                            ON tech.id = leaves.technician_id
                            WHERE leave_type_id = %s AND leaves.shop_id = %s AND start_date >= %s AND end_date <= %s;
                            """,(leave_type_id, shop_id, start_dt, end_dt))
            datas = cur.fetchall()
            cur.execute("SELECT id,name FROM leave_type;")
            extra_datas = ['',cur.fetchall()]
            print(datas)
            return render_template("view_datas.html", filter=True, result=[datas, leave_type_name],credentials=credentials,typ="leaves",extra_datas=extra_datas)
        elif typ == 'customers':
            if eval(bol):
                result = []
                cur.execute(""" SELECT id,code,registered_date,name,state_id,address,phone FROM customer WHERE customer.id = %s; """,(val,))
                result.append(cur.fetchall())
                cur.execute(""" SELECT ownership.vehicle_id,car.plate,brand.name,model.name,car.year,ownership.start_date,ownership.end_date
                    FROM ownership 
                    INNER JOIN customer 
                    ON customer.id = ownership.customer_id
                    INNER JOIN vehicle AS car
                    ON car.id = ownership.vehicle_id
                    INNER JOIN vehicle_model AS model
                    ON model.id = car.model_id
                    INNER JOIN vehicle_brand AS brand
                    ON brand.id = car.brand_id
                    WHERE customer_id = %s
                    ORDER BY ownership.start_date DESC;""",(val,))
                result.extend([[],[]])
                for data in cur.fetchall():
                    if data[6]:
                        result[2].append(data)
                    else:
                        result[1].append(data)
                cur.execute("SELECT id,name,short_name FROM state;")
                result.append(cur.fetchall())
                return render_template("registration_form.html",result=result,typ=typ,credentials=credentials,b_units=b_units)
            else:
                cur.execute(f"SELECT customer.id,code,customer.name,COALESCE(address,'Undefined'),COALESCE(state.name,'Undefined'),COALESCE(phone,'undefined') FROM customer LEFT JOIN state ON customer.state_id = state.id WHERE {column} iLIKE '%{val}%';")
                result = cur.fetchall()
                cur.execute(f"SELECT count(id) FROM customer WHERE {column} iLIKE '%{val}%';")
                length = cur.fetchall()
        elif typ == 'vehicles':
            if eval(bol):
                result = []
                cur.execute("SELECT car.id,LEFT(car.plate,3),SUBSTRING(car.plate,4,LENGTH(car.plate)-7),RIGHT(car.plate,4),car.register_date,brand.name,model.name,car.year,car.brand_id FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id WHERE car.id = %s;",(val,))
                result.append(cur.fetchall())
                cur.execute("SELECT short_name FROM state;")
                result.append(cur.fetchall())
                cur.execute("SELECT name FROM vehicle_brand;")
                result.append(cur.fetchall())
                cur.execute("SELECT name FROM vehicle_model WHERE brand_id = %s;",(result[0][0][8],))
                result.append(cur.fetchall())
                return render_template("registration_form.html",result=result,typ=typ,credentials=credentials,b_units=b_units)
            else:
                cur.execute(f"SELECT car.id,car.plate,brand.name,model.name,car.year FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id WHERE {column} iLIKE '%{val}%' ORDER BY plate desc;")
                result = cur.fetchall()
                cur.execute(f"SELECT count(car.id) FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id  WHERE {column} iLIKE '%{val}%';")  
                length = cur.fetchall()
        elif typ == 'descriptions' or typ == 'jobType':
            cur.execute(f"SELECT id,name FROM {typ} WHERE {column} iLIKE '%{val}%' ORDER BY name;")
            result = cur.fetchall()
            cur.execute(f"SELECT COUNT(id) FROM {typ} WHERE {column} iLIKE '%{val}%';")
            length = cur.fetchall()
        elif typ == 'brand':
            cur.execute(f"select brand.name,model.name from vehicle_brand brand inner join vehicle_model model on brand.id = model.brand_id where {column} ilike '%{val}%' order by brand.name;")
            datas = cur.fetchall()
            datas_dct = {}
            for data in datas:
                if data[0] not in datas_dct:
                    datas_dct[data[0]] = [data[1]]
                else:
                    datas_dct[data[0]].append(data[1])
            return render_template('view_datas.html',mgs=mgs,datas_dct=datas_dct,typ='brand',filt=True, credentials =credentials, b_units = b_units)
    else:      
        filt = False 
        extra_datas = []
        if typ == 'service-datas':
            query = f""" WITH month_cte AS (
            SELECT
                month_id,
                TO_CHAR(DATE_TRUNC('month', TIMESTAMP '2000-01-01'::date + (month_id-1  || ' months')::interval), 'Month') AS month_text
            FROM generate_series(1, 12) AS month_id
            )
            SELECT 
                month_cte.month_text,jb.job_date,unit.name,shop.name,jb.job_no,customer.name,vehicle.plate,model.name,
                vehicle.year,jb.invoice_no,jb.id
            FROM eachJobForm As jb 
            LEFT JOIN month_cte
            ON month_cte.month_id = jb.month_extracted
            LEFT JOIN res_partner AS unit
            ON unit.id = jb.business_unit_id
            LEFT JOIN shop
            ON shop.id = jb.shop_id
            LEFT JOIN customer
            ON customer.id = jb.customer_id
            LEFT JOIN vehicle
            ON vehicle.id = jb.vehicle_id
            LEFT JOIN vehicle_model AS model
            ON model.id = vehicle.model_id
            WHERE shop.id IN ({user_roles_lst})
            ORDER BY jb.job_date DESC,job_no DESC
            LIMIT 81;"""
            length_query = f"SELECT count(eachJobForm.id) FROM eachJobForm LEFT JOIN shop ON eachJobForm.shop_id = shop.id WHERE shop.id in ({user_roles_lst});"
        elif typ == 'check-in-out':
            query = f"""
                SELECT MAX(form.job_date), MAX(form.seq) , MAX(form.job_no) , MAX(car.plate) , MAX(brand.name) , MAX(model.name) , MAX(unit.name) , MAX(shop.name) , COUNT(DISTINCT line.technician_id), SUM(line.end_time - line.start_time) , 
                CASE WHEN COUNT(form.form_id) > 0 THEN 'Approved' ELSE 'Draft' END AS status , form.id
                FROM checkinoutform AS form
                INNER JOIN checkinoutline AS line
                ON form.id = line.form_id
                LEFT JOIN vehicle AS car
                ON car.id = form.vehicle_id
                LEFT JOIN vehicle_brand AS brand
                ON brand.id = car.brand_id
                LEFT JOIN vehicle_model AS model
                ON model.id = car.model_id
                LEFT JOIN res_partner AS unit
                ON unit.id = form.business_unit_id
                LEFT JOIN shop AS shop
                ON shop.id = form.shop_id
                WHERE shop.id in ({user_roles_lst})
                GROUP BY form.id
                ORDER BY form.job_date DESC , status
                LIMIT 81;
            """
            length_query = f"SELECT count(form.id) FROM checkinoutform AS form LEFT JOIN shop ON form.shop_id = shop.id WHERE shop.id in ({user_roles_lst});"           
        elif typ == 'psfu-calls':
            query = f""" 
                    SELECT form.job_date,unit.name,shop.name,form.job_no,car.plate,cus.name,cus.phone,status.name,psfu.remark,form.id,psfu.id FROM psfu_call AS psfu
                    INNER JOIN eachJobFORM AS form
                    ON form.id = psfu.form_id
                    LEFT JOIN vehicle car
                    ON car.id = form.vehicle_id
                    LEFT JOIN customer cus
                    ON cus.id = form.customer_id
                    LEFT JOIN call_status status
                    ON status.id = psfu.call_status_id
                    LEFT JOIN shop
                    ON shop.id = form.shop_id
                    LEFT JOIN res_partner unit
                    ON unit.id = shop.business_unit_id
                    WHERE form.shop_id in ({user_roles_lst}) AND psfu.call_status_id IS NOT NULL
                    ORDER BY form.job_date LIMIT 81;"""
            length_query = f"SELECT count(psfu.id) FROM psfu_call AS psfu INNER JOIN eachJobForm AS form ON form.id = psfu.form_id  WHERE form.shop_id in ({user_roles_lst}) AND psfu.call_status_id IS NOT NULL;"
        elif typ == 'leaves':
            cur.execute("SELECT id,name FROM leave_type WHERE name <> 'WHOLE SHOP LEAVE';")
            datas = cur.fetchall()
            extra_datas.append({(data[0],data[1]):[] for data in datas})
            cur.execute(""" SELECT leave_type_id,leave_type.name,leaves.id,tech.name,shop.name,start_date,end_date,
                                ROUND(EXTRACT(EPOCH FROM (end_date - start_date)) / 86400,1),remark  
                            FROM leaves 
                        INNER JOIN technicians AS tech ON tech.id = leaves.technician_id
                            LEFT JOIN shop ON shop.id = leaves.shop_id
                        LEFT JOIN leave_type ON leave_type.id = leaves.leave_type_id
                            WHERE leaves.leave_type_id <> (SELECT id FROM leave_type WHERE name = 'WHOLE SHOP LEAVE')
                        AND CURRENT_DATE BETWEEN start_date AND end_date;""")
            result = cur.fetchall()
            print(result)
            for data in result:
                extra_datas[0][(data[0],data[1])].append(data[1:])
            query = """ SELECT shop_leaves.id,shop.name,start_date,end_date,
                                ROUND(EXTRACT(EPOCH FROM (end_date - start_date)) / 86400,1),remark 
                            FROM shop_leaves 
                        INNER JOIN shop ON shop.id = shop_leaves.shop_id
                            WHERE CURRENT_DATE BETWEEN start_date AND end_date;"""
            length_query = "SELECT 10;"
            cur.execute("SELECT id,name FROM leave_type;")
            extra_datas.append(cur.fetchall())
        elif typ == 'descriptions':
            query = """ SELECT id,name FROM descriptions ORDER BY name LIMIT 81;"""
            length_query = "SELECT count(id) FROM descriptions;"
        elif typ == 'call-status':
            query = """ SELECT id,name FROM call_status ORDER BY name LIMIT 81;"""
            length_query = "SELECT count(id) FROM call_status;"
        elif typ == 'leave-type':
            query = " SELECT id,name FROM leave_type ORDER BY name LIMIT 81;"
            length_query = "SELECT count(id) FROM leave_type;"
        elif typ == 'pic-rate':
            query = """ SELECT id,fst_rate,sec_rate,thrd_rate,frth_rate,lst_rate FROM pic ORDER BY id DESC;"""
            length_query = "SELECT count(id) FROM pic;"
        elif typ == 'technician':
            query = f"""SELECT 
                            tech.id,
                            tech.name,
                            bi.name,
                            CASE 
                                WHEN transfer.to_shop_id = 5 THEN 
                            'INACTIVE - ' || 
                                    (SELECT name FROM shop WHERE id = transfer.from_shop_id)
                                ELSE 
                                    shop.name
                            END AS shop_name,
                            team.name
                        FROM 
                            technicians tech
                        INNER JOIN (
                            SELECT 
                                technician_id, 
                                from_shop_id,
                                to_shop_id 
                            FROM 
                                technicians_transfer
                            WHERE 
                                (CURRENT_DATE BETWEEN from_date AND to_date OR CURRENT_DATE >= from_date AND to_date IS NULL)
                        ) AS transfer ON transfer.technician_id = tech.id
                        LEFT JOIN shop ON shop.id = transfer.to_shop_id
                        LEFT JOIN res_partner AS bi
                        ON bi.id = shop.business_unit_id
                        LEFT JOIN technician_team AS team
                        ON team.id = tech.team_id
                        WHERE 
                            tech.id != 0 AND ( 
                            (transfer.to_shop_id = 5 AND transfer.from_shop_id in ({user_roles_lst}) )
                                OR  
                                transfer.to_shop_id IN ({user_roles_lst})
                            ) 
                        ORDER BY 
                            tech.name;"""
            cur.execute("SELECT name  FROM res_partner;")
            extra_datas.append(cur.fetchall())
            cur.execute("SELECT name  FROM shop WHERE name <> 'INACTIVE';")
            extra_datas.append(cur.fetchall())
            cur.execute("SELECT id,name FROM technician_team;")
            extra_datas.append(cur.fetchall())
            length_query =f"""  SELECT 
                                    COUNT(tech.id)
                                FROM 
                                    technicians tech
                                INNER JOIN (
                                    SELECT 
                                        technician_id, 
                                        from_shop_id,
                                        to_shop_id 
                                    FROM 
                                        technicians_transfer
                                    WHERE 
                                        (CURRENT_DATE BETWEEN from_date AND to_date OR CURRENT_DATE >= from_date AND to_date IS NULL)
                                ) AS transfer ON transfer.technician_id = tech.id
                                LEFT JOIN shop ON shop.id = transfer.to_shop_id
                                WHERE 
                                    tech.id != 0 AND ( 
                                    (transfer.to_shop_id = 5 AND transfer.from_shop_id in ({user_roles_lst}) )
                                        OR  
                                        transfer.to_shop_id IN ({user_roles_lst})
                                    );"""
        elif typ == 'brand':
            cur.execute("select brand.name,model.name from vehicle_brand brand inner join vehicle_model model on brand.id = model.brand_id order by brand.name;")
            datas = cur.fetchall()
            datas_dct = {}
            for data in datas:
                if data[0] not in datas_dct:
                    datas_dct[data[0]] = [data[1]]
                else:
                    datas_dct[data[0]].append(data[1])
            return render_template('view_datas.html',mgs=mgs,datas_dct=datas_dct,typ='brand',credentials=credentials,b_units=b_units)
        elif typ == 'customers':
            query = "SELECT customer.id,code,customer.name,COALESCE(address,'Undefined'),COALESCE(state.name,'Undefined'),COALESCE(phone,'undefined') FROM customer LEFT JOIN state ON customer.state_id = state.id ORDER BY code LIMIT 81;"
            length_query = "SELECT count(id) FROM customer;"
        elif typ == 'vehicles':
            query = "SELECT car.id,car.plate,brand.name,model.name,car.year FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id ORDER BY plate desc LIMIT 81;"
            length_query = "SELECT count(id) FROM vehicle;"
        else:
            typ = 'jobType'
            query = """  SELECT id,name FROM jobType ORDER BY name;  """
            length_query = "SELECT count(id) FROM jobType;"
        cur.execute(query)
        result = cur.fetchall()
        cur.execute(length_query)
        length = cur.fetchall()
    return render_template('view_datas.html',mgs=mgs,extra_datas=extra_datas,result=result,length=length,filt = filt,typ=typ,credentials=credentials,b_units=b_units)

@views.route("/get-data/<db>/<idd>",methods=["GET", "POST"])
def get_data(db,idd:str):
    conn = db_connect()
    cur = conn.cursor()
    if db == 'vehicle':
        plate = idd.split("||")[0]
        cus_id =  f"and customer.id = {idd.split('||')[1]}" if "||" in idd else ""
        cur.execute(f"""SELECT vehicle.plate,brand.name,model.name,customer.name,customer.phone,customer.state_id,customer.id,customer.address,vehicle.year,vehicle.id, 't' AS ownership_status
                    FROM ownership
                    LEFT JOIN vehicle
                    ON ownership.vehicle_id = vehicle.id
                    LEFT JOIN customer
                    ON customer.id = ownership.customer_id
                    LEFT JOIN vehicle_brand brand
                    ON brand.id = vehicle.brand_id
                    LEFT JOIN vehicle_model model
                    ON model.id = vehicle.model_id
                    WHERE vehicle.plate = '{plate}' {cus_id} ORDER BY end_date;""")
        datas = cur.fetchall()
        if len(datas) == 0:
            cur.execute(""" SELECT vehicle.id,brand.name,model.name,vehicle.year,'f' AS ownership_status
                        FROM vehicle 
                        INNER JOIN  vehicle_brand AS brand
                        ON brand.id = vehicle.brand_id
                        INNER JOIN vehicle_model AS model
                        ON model.id = vehicle.model_id
                        WHERE vehicle.plate = %s;""",(plate,))
            data = cur.fetchone()
            if data:
                datas = [data]
        print(datas,len(datas))
        return jsonify(datas)
    elif db == 'autofill-vehicle':
        cur.execute("SELECT car.plate,car.make,car.model,cus.name,cus.phone,state.name,cus.id FROM vehicle AS car INNER JOIN customer AS cus on cus.id = car.customer_id LEFT JOIN state ON state.id = cus.state_id WHERE plate = %s;",(idd,))
    elif db == 'autofill-customer':
        cur.execute("SELECT address,state_id,phone,id FROM customer WHERE name = %s;",(idd,))
    elif db == 'get-brand-model':
        cur.execute("SELECT brand_id,id FROM vehicle_model WHERE name = %s;",(idd,))
    elif db == 'eachJobDelForm':
        cur.execute("DELETE FROM psfu_call WHERE form_id = %s;",(idd,))
        cur.execute("DELETE FROM eachJobLine WHERE form_id = %s;",(idd,))
        cur.execute("DELETE FROM eachJobForm WHERE id = %s;",(idd,))
        conn.commit()
        return "Finished"
    elif db == 'checkinoutDelForm':
        cur.execute("DELETE FROM checkinoutline WHERE form_id = %s;",(idd,))
        cur.execute("DELETE FROM checkinoutform WHERE id = %s;",(idd,))
        conn.commit()
        return "Finished"
    elif db in ('pic','technicians','jobType','descriptions','leave-type','call-status'):
        db = db.replace("-", "_")
        try:
            cur.execute("DELETE FROM {} WHERE id = %s;".format(db), (idd,))
        except ForeignKeyViolation as err:
            return "failed"
        conn.commit()
        return "finished"
    elif db == 'vehicle_model':
        cur.execute("SELECT name FROM vehicle_model WHERE brand_id = (SELECT id FROM vehicle_brand WHERE name = %s);",(idd,))
    elif db == 'check-duplicate-technician':
        if request.method == 'POST':
            pass
        name , shop_id = idd.split("|")
        cur.execute("SELECT id FROM technicians WHERE name = %s AND shop_id = %s;",(name,shop_id))
    elif db == 'check-vehicle':
        cur.execute("SELECT id FROM vehicle WHERE plate = %s;",(idd,))
    elif db == 'change-owner':
        cur.execute(""" UPDATE ownership AS o
                            SET end_date = CURRENT_DATE
                        FROM (
                            SELECT id
                            FROM ownership
                            WHERE vehicle_id = (SELECT id FROM vehicle WHERE plate = %s)
                            ORDER BY end_date DESC
                            LIMIT 1
                        ) AS subquery
                        WHERE o.id = subquery.id;
                        """,(idd,))
        conn.commit()
        return "Finished"
    elif db == 'show-technician-shop':
        shop_id,  start_dt = idd.split("~~")
        cur.execute(""" SELECT tech.name,tech.id FROM technicians tech
                    INNER JOIN (
                        SELECT technician_id, to_shop_id FROM technicians_transfer
                        WHERE 
                            %s BETWEEN from_date AND to_date
                                    OR
                            %s >= from_date AND to_date IS NULL 
                    ) AS transfer
                ON transfer.technician_id = tech.id
                    INNER JOIN shop 
                ON shop.id = transfer.to_shop_id
                WHERE tech.id != 0 AND shop.id = %s ORDER BY tech.id;""",(start_dt, start_dt, shop_id))
    elif db == 'ownership':
        vehicle_id,customer_id = idd.split("||")
        cur.execute("""INSERT INTO ownership(vehicle_id,customer_id,start_date,unique_owner)
                VALUES(%s,%s,%s,%s) ON CONFLICT (unique_owner) DO UPDATE set end_date = NULL""",(vehicle_id,customer_id,datetime.now().strftime("%Y-%m-%d"),vehicle_id+'-'+customer_id))
        cur.execute("UPDATE ownership SET end_date = %s WHERE vehicle_id = %s AND customer_id <> %s AND end_date IS  NULL;",(datetime.now().strftime("%Y-%m-%d"),vehicle_id,customer_id))
        conn.commit()
        return "Finished"
    elif db == 'postPsfuCall':
        psfu_id, status_id, remark = idd.split("||")
        print(psfu_id, status_id, remark)
        cur.execute("UPDATE psfu_call SET call_status_id = %s , remark = %s WHERE id = %s;",(status_id,remark,psfu_id))
        conn.commit()
        return "Finished"
    elif db == 'deleteCustomersData':
        cur.execute("SELECT id FROM eachJobForm WHERE ownership_id = (SELECT id FROM ownership WHERE customer_id = %s);",(idd,))
        if cur.fetchall() == []:
            cur.execute("DELETE FROM ownership WHERE customer_id = %s;",(idd,))
            cur.execute("DELETE FROM customer WHERE id = %s;",(idd,))
            conn.commit()
            return "Finished"
        return 'failed'
    elif db == 'deleteVehiclesData':
        cur.execute("SELECT id FROM eachJobForm WHERE ownership_id = (SELECT id FROM ownership WHERE vehicle_id = %s);",(idd,))
        if cur.fetchall() == []:
            cur.execute("DELETE FROM ownership WHERE vehicle_id = %s;",(idd,))
            cur.execute("DELETE FROM vehicle WHERE id = %s;",(idd,))
            conn.commit()
            return "Finished"
        return 'failed'
    elif db in ('brand','model'):
        update_brand , brand = idd.split("~")
        cur.execute(f"UPDATE vehicle_{db} SET name = '{update_brand}' WHERE TRIM(name) = '{brand}' AND NOT EXISTS (SELECT 1 FROM vehicle_{db} WHERE name = '{update_brand}');")
        conn.commit()
        return "Finished"
    elif db == 'remove-access':
        user_role_name , mail = idd.split("|") 
        cur.execute("SELECT id FROM user_role WHERE name = %s;",(user_role_name,)) 
        user_role_id = cur.fetchone()
        if user_role_id:    
            cur.execute("SELECT shop_ids FROM user_auth WHERE mail = %s;",(mail,))
            access_shop_ids:list = cur.fetchone()[0]     
            access_shop_ids.remove(user_role_id[0]) 
            cur.execute(f"""UPDATE user_auth SET shop_ids = ARRAY[{",".join(list(map(str,access_shop_ids)))}] WHERE mail = '{mail}';""")
            print(f"""UPDATE user_auth SET shop_ids = ARRAY[{",".join(list(map(str,access_shop_ids)))}] WHERE mail = '{mail}';""")
            conn.commit()
            return "Finished"
        else:
            return "Not"
    elif db == 'add-access':
        user_role_name , mail = idd.split("|")
        print(user_role_name,mail)
        cur.execute("SELECT id FROM user_role WHERE name = %s;",(user_role_name,))
        user_role_id = cur.fetchone()
        print(user_role_id)
        if user_role_id:
            cur.execute("SELECT shop_ids FROM user_auth WHERE mail = %s;",(mail,))
            access_shop_ids:list = cur.fetchone()[0]
            if user_role_id[0] not in access_shop_ids:
                access_shop_ids.append(user_role_id[0])
            cur.execute(f"""UPDATE user_auth SET shop_ids = ARRAY[{",".join(list(map(str,access_shop_ids)))}] WHERE mail = '{mail}';""")
            print(f"""UPDATE user_auth SET shop_ids = ARRAY[{",".join(list(map(str,access_shop_ids)))}] WHERE mail = '{mail}';""")
            conn.commit()
        return f"{user_role_id[0]}"
    elif db == 'checkRegisteredUsers':
        registered_id , what = idd.split("|")
        if what == 't' or what == 'f':
            cur.execute("UPDATE user_auth SET pending = %s WHERE id = %s;",(what,registered_id))
        else:
            cur.execute("DELETE FROM user_auth WHERE id = %s;",(registered_id,))
        conn.commit()
        return "Finished"
    datas = cur.fetchall()
    print(datas)
    return jsonify(datas)


@views.route("/offset-display/<for_what>/<ofset>")
def offset_display(for_what,ofset):
    conn = db_connect()
    cur = conn.cursor()
    credentials , b_units = extract_shop_datas(cur)
    user_roles_lst = ",".join([str(dt[2]) for dt in credentials])
    shop_id = ''
    if '~' in ofset:
        ofset, shop_id = ofset.split('~')
    print(for_what)
    queries_dct = {
        "job" : f""" WITH month_cte AS (
            SELECT
                month_id,
                TO_CHAR(DATE_TRUNC('month', TIMESTAMP '2000-01-01'::date + (month_id-1  || ' months')::interval), 'Month') AS month_text
            FROM generate_series(1, 12) AS month_id
            )
            SELECT 
                month_cte.month_text,jb.job_date,unit.name,shop.name,jb.job_no,customer.name,vehicle.plate,model.name,
                vehicle.year,jb.invoice_no,jb.shop_id
            FROM eachJobForm As jb 
            LEFT JOIN month_cte
            ON month_cte.month_id = jb.month_extracted
            LEFT JOIN res_partner AS unit
            ON unit.id = jb.business_unit_id
            LEFT JOIN shop
            ON shop.id = jb.shop_id
            LEFT JOIN customer
            ON customer.id = jb.customer_id
            LEFT JOIN vehicle
            ON vehicle.id = jb.vehicle_id
            LEFT JOIN vehicle_model AS model
            ON model.id = vehicle.model_id
            WHERE shop.id IN ({user_roles_lst})
            ORDER BY jb.job_date DESC,job_no DESC
            LIMIT 81 OFFSET {ofset};""",
            "customers":f"SELECT customer.id,code,customer.name,COALESCE(address,'Undefined'),COALESCE(state.name,'Undefined'),COALESCE(phone,'undefined') FROM customer LEFT JOIN state ON customer.state_id = state.id ORDER BY code LIMIT 81 OFFSET {ofset};",
            "vehicles":f"SELECT car.id,car.plate,brand.name,model.name,car.year FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id ORDER BY plate desc LIMIT 81 OFFSET {ofset};",
            "descriptions":f"SELECT id,name FROM descriptions ORDER BY name LIMIT 81 OFFSET {ofset};",
            "jobType":f"SELECT id,name FROM jobType ORDER BY name LIMIT 81 OFFSET {ofset};",
            "psfuCall":f""" SELECT form.job_no,form.job_date,car.plate,cus.name,cus.phone,form.id,psfu.id FROM psfu_call AS psfu
                INNER JOIN eachJobFORM AS form
                    ON form.id = psfu.form_id
                LEFT JOIN vehicle car
                    ON car.id = form.vehicle_id
                LEFT JOIN customer cus
                    ON cus.id = form.customer_id
                WHERE form.shop_id = '{shop_id}' and form.job_date < CURRENT_DATE - 2 AND psfu.call_status_id IS NULL
                    ORDER BY form.job_date LIMIT 20 OFFSET {ofset}; """,
            "technician":f"""SELECT 
                                tech.id,
                                tech.name,
                                bi.name,
                                CASE 
                                    WHEN transfer.to_shop_id = 5 THEN 
                                'INACTIVE - ' || 
                                        (SELECT name FROM shop WHERE id = transfer.from_shop_id)
                                    ELSE 
                                        shop.name
                                END AS shop_name,
                                team.name
                            FROM 
                                technicians tech
                            INNER JOIN (
                                SELECT 
                                    technician_id, 
                                    from_shop_id,
                                    to_shop_id 
                                FROM 
                                    technicians_transfer
                                WHERE 
                                    (CURRENT_DATE BETWEEN from_date AND to_date OR CURRENT_DATE >= from_date AND to_date IS NULL)
                            ) AS transfer ON transfer.technician_id = tech.id
                            LEFT JOIN shop ON shop.id = transfer.to_shop_id
                            LEFT JOIN res_partner AS bi
                            ON bi.id = shop.business_unit_id
                            LEFT JOIN technician_team AS team
                            ON team.id = tech.team_id
                            WHERE 
                                tech.id != 0 AND ( 
                                (transfer.to_shop_id = 5 AND transfer.from_shop_id in ({user_roles_lst}) )
                                    OR  
                                    transfer.to_shop_id IN ({user_roles_lst})
                                ) 
                            ORDER BY tech.name
                                LIMIT 81 OFFSET {ofset}; """
    }
    cur.execute(queries_dct[for_what])
    result_datas = cur.fetchall()
    return jsonify(result_datas)