from flask import Blueprint,render_template,request,jsonify,url_for,redirect
from website import db_connect
from decimal import Decimal 

views = Blueprint('views',__name__)

# views.add_url_rule('/favicon.ico',redirect_to=url_for('static', filename='images/MDMM.ico'))

@views.route("/")
def home():
    if request.cookies.get('username'): 
        return render_template('home.html')
    return redirect(url_for('auth.authenticate',typ='log'))


@views.route("/get-graph-report/<start_dt>/<end_dt>/<bi>/<shop>")
@views.route("/get-report",methods=['GET','POST'])
def get_report(start_dt=None,end_dt=None,bi=None,shop=None):
    if request.method == 'POST' or start_dt:
        if not start_dt and not end_dt:
            start_dt = request.form.get('start-dt')
            end_dt = request.form.get('end-dt')
            bi = request.form.get('bi')
            shop = request.form.get('shop')
        else:
            if not request.cookies.get('username'): 
                return redirect(url_for('views.home'))
        where_clause = ""
        where_clause += f"WHERE ej.business_unit_id = '{bi}' " if bi != '0' else ""
        where_clause += f"AND ej.shop_id = '{shop}' " if shop != '0' else ""
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT id,name FROM technicians WHERE id != 0 ORDER BY id;")
        technicians_ids = cur.fetchall()
        technicians_names = [tech[1] for tech in technicians_ids]
        cur.execute("SELECT id,name FROM jobType ORDER BY id;")
        job_types = cur.fetchall()
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
            ) AS jt
            CROSS JOIN (
                SELECT DISTINCT month_extracted
                FROM eachJob
            ) AS months
            LEFT JOIN (
                SELECT *
                FROM eachJob
                WHERE job_date BETWEEN '{start_dt}' AND '{end_dt}'
            ) AS ej ON jt.id = ej.job_type_id AND months.month_extracted = ej.month_extracted
            {where_clause}
            GROUP BY jt.id
            ORDER BY jt.id;""")
            datas = cur.fetchall()
            if '/get-graph-report' in request.path:
                data = [dt[1] for dt in datas]
                total_result.append([technicians_names[idx]]+data+[sum(data),str(sum(data))])
            else:
                for data in datas:
                    lst_data[idx] += data[1]
                    total_result[data[0]].append(data[1])
            cur.execute("SELECT name FROM shop WHERE id = %s;",(shop,))
            shop_name = cur.fetchall()[0][0]
        if '/get-graph-report' in request.path:
            return jsonify(total_result)
        else:
            total_result[0] = lst_data
    else:
        return redirect(url_for('views.home'))
    return render_template('report_graph_view.html',extra_datas=[technicians_names,get_job_types,start_dt,end_dt,shop_name],total_result = total_result,)

@views.route("pic-report",methods=['GET','POST'])
def pic_report():
    if not request.cookies.get('username'): 
        return redirect(url_for('views.home'))
    if request.method == 'POST':
        conn = db_connect()
        cur = conn.cursor()
        start_dt = request.form.get('start-dt')
        end_dt = request.form.get('end-dt')
        bi_id = request.form.get('bi')
        shop_id = request.form.get('shop')
        where_clause = ""
        where_clause += f"WHERE ej.business_unit_id = '{bi_id}' " if bi_id != '0' else ""
        where_clause += f"AND ej.shop_id = '{shop_id}' " if shop_id != '0' else ""
        cur.execute("SELECT id,name FROM jobType ORDER BY id;")
        job_types = cur.fetchall()
        cur.execute("SELECT id,name FROM technicians WHERE id != 0 ORDER BY id;")
        technicians_ids = cur.fetchall()
        technicians_names = [tech[1] for tech in technicians_ids]
        total_result = {}

        for idx,technician_id in enumerate(technicians_ids):
            print(f""" 
                SELECT 
                    COALESCE(SUM(
                            CASE WHEN ej.fst_pic_id = {technician_id[0]} THEN ej.fst_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.sec_pic_id = {technician_id[0]} THEN ej.sec_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.thrd_pic_id = {technician_id[0]} THEN ej.thrd_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.frth_pic_id = {technician_id[0]} THEN ej.frth_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.lst_pic_id = {technician_id[0]} THEN ej.lst_pic_amt ELSE 0.0 END
                        ), 0.0) AS total_sum,
                        COALESCE(SUM(CASE WHEN ej.fst_pic_id = {technician_id[0]} THEN ej.fst_pic_amt ELSE 0.0 END)) AS pic_1,
                        COALESCE(SUM(CASE WHEN ej.sec_pic_id = {technician_id[0]} THEN ej.sec_pic_amt ELSE 0.0 END)) AS pic_2,
                        COALESCE(SUM(CASE WHEN ej.thrd_pic_id = {technician_id[0]} THEN ej.thrd_pic_amt ELSE 0.0 END)) AS pic_3,
                        COALESCE(SUM(CASE WHEN ej.frth_pic_id = {technician_id[0]} THEN ej.frth_pic_amt ELSE 0.0 END)) AS pic_4,
                        COALESCE(SUM(CASE WHEN ej.lst_pic_id = {technician_id[0]} THEN ej.lst_pic_amt ELSE 0.0 END)) AS pic_5
                FROM (
                    SELECT id
                    FROM jobtype
                ) AS jt
                CROSS JOIN (
                    SELECT DISTINCT month_extracted
                    FROM eachJob
                ) AS months
                LEFT JOIN (
                    SELECT *
                    FROM eachJob
                    WHERE job_date BETWEEN '{start_dt}' AND '{end_dt}'
                ) AS ej ON jt.id = ej.job_type_id AND months.month_extracted = ej.month_extracted
                {where_clause}
                GROUP BY jt.id
                ORDER BY jt.id;
            """)
            query = f""" 
                SELECT 
                    COALESCE(SUM(
                            CASE WHEN ej.fst_pic_id = {technician_id[0]} THEN ej.fst_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.sec_pic_id = {technician_id[0]} THEN ej.sec_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.thrd_pic_id = {technician_id[0]} THEN ej.thrd_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.frth_pic_id = {technician_id[0]} THEN ej.frth_pic_amt ELSE 0.0 END +
                            CASE WHEN ej.lst_pic_id = {technician_id[0]} THEN ej.lst_pic_amt ELSE 0.0 END
                        ), 0.0) AS total_sum,
                        COALESCE(SUM(CASE WHEN ej.fst_pic_id = {technician_id[0]} THEN ej.fst_pic_amt ELSE 0.0 END)) AS pic_1,
                        COALESCE(SUM(CASE WHEN ej.sec_pic_id = {technician_id[0]} THEN ej.sec_pic_amt ELSE 0.0 END)) AS pic_2,
                        COALESCE(SUM(CASE WHEN ej.thrd_pic_id = {technician_id[0]} THEN ej.thrd_pic_amt ELSE 0.0 END)) AS pic_3,
                        COALESCE(SUM(CASE WHEN ej.frth_pic_id = {technician_id[0]} THEN ej.frth_pic_amt ELSE 0.0 END)) AS pic_4,
                        COALESCE(SUM(CASE WHEN ej.lst_pic_id = {technician_id[0]} THEN ej.lst_pic_amt ELSE 0.0 END)) AS pic_5
                FROM (
                    SELECT id
                    FROM jobtype
                ) AS jt
                CROSS JOIN (
                    SELECT DISTINCT month_extracted
                    FROM eachJob
                ) AS months
                LEFT JOIN (
                    SELECT *
                    FROM eachJob
                    WHERE job_date BETWEEN '{start_dt}' AND '{end_dt}'
                ) AS ej ON jt.id = ej.job_type_id AND months.month_extracted = ej.month_extracted
                {where_clause}
                GROUP BY jt.id
                ORDER BY jt.id;
            """
            cur.execute(query)
            datas = cur.fetchall()
            result = [[],[],[],[],[],[]]
            for data in datas:
                for i,dt in enumerate(data):
                    result[i].append(dt)
            result[0].append(sum(result[0]))
            result = [item for subitem in result for item in subitem]
            total_result[technicians_names[idx]] = result
            cur.execute("SELECT name FROM shop WHERE id = %s;",(shop_id,))
            shop_name = cur.fetchall()[0][0]
    else:
        return redirect(url_for('views.home'))
    return render_template('pic_report.html',total_result=total_result,job_types=job_types,extra_datas = [start_dt,end_dt,shop_name])


@views.route("/show-datas/<typ>/<mgs>")
@views.route("/show-datas/<typ>",methods=['GET','POST'])
def show_service_datas(typ,mgs=None):
    conn = db_connect()
    cur = conn.cursor()
    extra_datas = []
    if request.method == 'POST':
        filt = True
        column = request.form.get('column')
        db = request.form.get('database')
        val = request.form.get('filter')
        bol = request.form.get('editOrSubmit')
        if typ == 'service-datas':
            if db == 'eachJob':
                with_id_query =f""" SELECT 
                                        jb.job_date,unit.name || ' | ' || unit.id,shop.name || ' | ' || shop.id,jb.job_no,customer.name,vehicle.plate,vehicle.model,
                                        vehicle.year,jb.invoice_no,jb.job_name,jobType.name,jb.total_amt,t_one.name || ' | ' || t_one.id,t_two.name || ' | ' || t_two.id,
                                        t_three.name|| ' | ' || t_three.id,t_four.name|| ' | ' || t_four.id,t_five.name|| ' | ' || t_five.id,vehicle.id,pic.unique_rate
                                    FROM eachJob jb 
                                    LEFT JOIN res_partner AS unit
                                    ON unit.id = jb.business_unit_id
                                    LEFT JOIN shop
                                    ON shop.id = jb.shop_id
                                    LEFT JOIN customer
                                    ON customer.id = jb.customer_id
                                    LEFT JOIN vehicle
                                    ON vehicle.id = jb.vehicle_id
                                    LEFT JOIN jobType
                                    ON jobType.id = jb.job_type_id
                                    LEFT JOIN technicians AS t_one
                                    ON t_one.id = jb.fst_pic_id 
                                    LEFT JOIN technicians AS t_two
                                    ON t_two.id = jb.sec_pic_id 
                                    LEFT JOIN technicians AS t_three
                                    ON t_three.id = jb.thrd_pic_id 
                                    LEFT JOIN technicians AS t_four
                                    ON t_four.id = jb.frth_pic_id 
                                    LEFT JOIN technicians AS t_five
                                    ON t_five.id = jb.lst_pic_id 
                                    LEFT JOIN pic 
                                    ON pic.id = jb.pic_rate_id
                                    WHERE job_no = '{val}'
                                    ORDER BY jb.job_date DESC,job_no DESC;""" 
                query = f""" WITH month_cte AS (
                    SELECT
                        month_id,
                        TO_CHAR(DATE_TRUNC('month', TIMESTAMP '2000-01-01'::date + (month_id-1  || ' months')::interval), 'Month') AS month_text
                    FROM generate_series(1, 12) AS month_id
                    )
                    SELECT 
                        month_cte.month_text,jb.job_date,unit.name,shop.name,jb.job_no,customer.name,vehicle.plate,vehicle.model,
                        vehicle.year,jb.invoice_no,jb.job_name,jobType.name,jb.total_amt,t_one.name,t_two.name,t_three.name,t_four.name,t_five.name
                    FROM eachJob jb 
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
                    LEFT JOIN jobType
                    ON jobType.id = jb.job_type_id
                    LEFT JOIN technicians AS t_one
                    ON t_one.id = jb.fst_pic_id 
                    LEFT JOIN technicians AS t_two
                    ON t_two.id = jb.sec_pic_id 
                    LEFT JOIN technicians AS t_three
                    ON t_three.id = jb.thrd_pic_id 
                    LEFT JOIN technicians AS t_four
                    ON t_four.id = jb.frth_pic_id 
                    LEFT JOIN technicians AS t_five
                    ON t_five.id = jb.lst_pic_id 
                    WHERE {column} iLIKE '%{val}%'
                    ORDER BY jb.job_date DESC,job_no DESC;"""
                if eval(bol):
                    cur.execute(with_id_query)
                    result = []
                    result.append(cur.fetchall())
                    cur.execute("SELECT plate FROM vehicle;")
                    result.append(cur.fetchall())
                    cur.execute("SELECT id,name FROM res_partner;")
                    result.append(cur.fetchall())
                    cur.execute("SELECT id,name FROM shop;")
                    result.append(cur.fetchall())
                    cur.execute("SELECT id,name FROM technicians;")
                    result.append(cur.fetchall())
                    cur.execute("SELECT id,name FROM jobType;")
                    result.append(cur.fetchall())
                    return render_template('edit_form.html',result = result)
                cur.execute(query)
                result = cur.fetchall()
                cur.execute(f"SELECT count(jb.id) FROM eachJob jb LEFT JOIN vehicle ON vehicle.id = jb.vehicle_id  LEFT JOIN res_partner AS unit ON unit.id = jb.business_unit_id LEFT JOIN shop ON shop.id = jb.shop_id WHERE {column} iLIKE '%{val}%';")
                length = cur.fetchall()
        elif typ == 'technician':
            query = f""" SELECT tech.id,tech.name,bi.name,shop.name FROM technicians tech
            INNER JOIN res_partner bi
            ON bi.id = tech.business_unit_id
            INNER JOIN shop
            ON shop.id = tech.shop_id
            WHERE tech.id != 0 and {column}.name iLike '%{val}%'  ORDER BY tech.name; """
            print(query)
            cur.execute(query)
            result = cur.fetchall()
            db = 'technicians'
            cur.execute("SELECT name  FROM res_partner;")
            extra_datas.append(cur.fetchall())
            cur.execute("SELECT name  FROM shop;")
            extra_datas.append(cur.fetchall())
            length = [(len(result),)]
    else:      
        filt = False 
        extra_datas = []
        if typ == 'service-datas':
            query = """ WITH month_cte AS (
            SELECT
                month_id,
                TO_CHAR(DATE_TRUNC('month', TIMESTAMP '2000-01-01'::date + (month_id-1  || ' months')::interval), 'Month') AS month_text
            FROM generate_series(1, 12) AS month_id
            )
            SELECT 
                month_cte.month_text,jb.job_date,unit.name,shop.name,jb.job_no,customer.name,vehicle.plate,vehicle.model,
                vehicle.year,jb.invoice_no,jb.job_name,jobType.name,jb.total_amt,t_one.name,t_two.name,t_three.name,t_four.name,t_five.name
            FROM eachJob jb 
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
            LEFT JOIN jobType
            ON jobType.id = jb.job_type_id
            LEFT JOIN technicians AS t_one
            ON t_one.id = jb.fst_pic_id 
            LEFT JOIN technicians AS t_two
            ON t_two.id = jb.sec_pic_id 
            LEFT JOIN technicians AS t_three
            ON t_three.id = jb.thrd_pic_id 
            LEFT JOIN technicians AS t_four
            ON t_four.id = jb.frth_pic_id 
            LEFT JOIN technicians AS t_five
            ON t_five.id = jb.lst_pic_id 
            ORDER BY jb.job_date DESC,job_no DESC
            LIMIT 81;"""
            db = 'eachJob'
        elif typ == 'pic-rate':
            query = """ SELECT id,fst_rate,sec_rate,thrd_rate,frth_rate,lst_rate FROM pic ORDER BY id DESC;"""
            db = 'pic'
        elif typ == 'technician':
            query = """ SELECT tech.id,tech.name,bi.name,shop.name FROM technicians tech
                        INNER JOIN res_partner bi
                        ON bi.id = tech.business_unit_id
                        INNER JOIN shop
                        ON shop.id = tech.shop_id
                        WHERE tech.id != 0 ORDER BY tech.name; """
            db = 'technicians'
            cur.execute("SELECT name  FROM res_partner;")
            extra_datas.append(cur.fetchall())
            cur.execute("SELECT name  FROM shop;")
            extra_datas.append(cur.fetchall())
        else:
            db = 'jobType'
            query = """  SELECT id,name FROM jobType ORDER BY name;  """
        cur.execute(query)
        result = cur.fetchall()
        cur.execute("SELECT count(id) FROM %s;" % db)
        length = cur.fetchall()
    return render_template('view_datas.html',mgs=mgs,extra_datas=extra_datas,result=result,length=length,filt = filt,typ=typ)

@views.route("/get-data/<db>/<idd>")
def get_data(db,idd):
    conn = db_connect()
    cur = conn.cursor()
    if db == 'vehicle':
        cur.execute("SELECT vehicle.id,name,model,year,customer.id FROM vehicle LEFT JOIN customer ON customer.id = vehicle.customer_id WHERE plate = %s;",(idd,))
    elif db == 'eachJobDelForm':
        cur.execute("DELETE FROM eachJob WHERE job_no = %s",(idd,))
        conn.commit()
        return "Finished"
    elif db in ('pic','technicians','jobType'):
        cur.execute("DELETE FROM {} WHERE id = %s;".format(db), (idd,))
        conn.commit()
        return "finished"
    datas = cur.fetchall()
    # print(datas)
    return jsonify(datas)


@views.route("/offset-display/<for_what>/<ofset>")
def offset_display(for_what,ofset):
    queries_dct = {
        "job" : f""" WITH month_cte AS (
                        SELECT
                            month_id,
                            TO_CHAR(DATE_TRUNC('month', TIMESTAMP '2000-01-01'::date + (month_id-1  || ' months')::interval), 'Month') AS month_text
                        FROM generate_series(1, 12) AS month_id
                        )
                        SELECT 
                            month_cte.month_text,jb.job_date,unit.name,shop.name,jb.job_no,customer.name,vehicle.plate,vehicle.model,
                            vehicle.year,jb.invoice_no,jb.job_name,jobType.name,jb.total_amt,t_one.name,t_two.name,t_three.name,t_four.name,t_five.name
                        FROM eachJob jb 
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
                        LEFT JOIN jobType
                        ON jobType.id = jb.job_type_id
                        LEFT JOIN technicians AS t_one
                        ON t_one.id = jb.fst_pic_id 
                        LEFT JOIN technicians AS t_two
                        ON t_two.id = jb.sec_pic_id 
                        LEFT JOIN technicians AS t_three
                        ON t_three.id = jb.thrd_pic_id 
                        LEFT JOIN technicians AS t_four
                        ON t_four.id = jb.frth_pic_id 
                        LEFT JOIN technicians AS t_five
                        ON t_five.id = jb.lst_pic_id 
                        ORDER BY jb.job_date DESC,job_no DESC
                        LIMIT 81 OFFSET {ofset};""",
        "dty": f""" SELECT 
                    dty.duty_date,pj.code,pj.name,fv.machine_name,dty.operator_name,dty.morg_start,dty.morg_end,
                    dty.aftn_start,dty.aftn_end,dty.evn_start,dty.evn_end,dty.total_hr,dty.hrper_rate,
                    dty.totaluse_fuel,dty.fuel_price,dty.duty_amt,dty.fuel_amt,dty.total_amt,dty.way,
                    dty.complete_feet, dty.complete_sud 
                    FROM duty_odoo_report dty
                    LEFT JOIN fleet_vehicle fv ON fv.id = dty.machine_id
                    LEFT JOIN analytic_project_code pj ON pj.id = dty.project_id ORDER BY dty.duty_date ASC 
                    LIMIT 81 OFFSET {ofset}""",
        "machine" : f"""SELECT fv.machine_name,mt.name,mc.name,rc.name,mcf.name,vb.name,vo.name 
                        FROM fleet_vehicle fv
                        LEFT JOIN machine_type mt ON mt.id = fv.machine_type_id 
                        LEFT JOIN machine_class mc ON mc.id = fv.machine_class_id
                        LEFT JOIN res_company rc ON rc.id = fv.business_unit_id
                        LEFT JOIN fleet_vehicle_model_brand vb ON vb.id = fv.brand_id
                        LEFT JOIN vehicle_owner vo ON vo.id = fv.owner_name_id
                        LEFT JOIN vehicle_machine_config mcf ON mcf.id = fv.machine_config_id 
                        LIMIT 81 OFFSET {ofset}""",
        "expense" : f"""  SELECT
                            exp.duty_date,pj.code,pj.name,bi.name,exp.expense_amt
                            FROM expense_prepaid AS exp
                            INNER JOIN analytic_project_code AS pj
                            ON pj.id = exp.project_id
                            INNER JOIN res_company bi
                            ON bi.id = exp.res_company_id
                            LIMIT 81 OFFSET {ofset};"""
    }
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(queries_dct[for_what])
    result_datas = cur.fetchall()
    return jsonify(result_datas)

@views.route('dashboard')
def show_dashboard():
    return render_template('dashboard.html')