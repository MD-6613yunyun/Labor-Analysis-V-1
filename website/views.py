from flask import Blueprint,render_template,request,jsonify,url_for,redirect
from website import db_connect
from decimal import Decimal
from psycopg2.errors import ForeignKeyViolation 
from datetime import datetime

views = Blueprint('views',__name__)

@views.route("/")
def home():
    if request.cookies.get('pg-username'): 
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT count(id) FROM user_auth WHERE pending = 'f';")
        noti_counts = cur.fetchall()[0][0]
        print(noti_counts)
        return render_template('home.html',noti_counts=noti_counts)
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
            if not request.cookies.get('pg-username'): 
                return redirect(url_for('views.home'))
        where_clause = ""
        where_clause += f"AND ej.business_unit_id = '{bi}' " if bi != '0' else ""
        where_clause += f"AND ej.shop_id = '{shop}' " if shop != '0' else ""
        conn = db_connect()
        cur = conn.cursor()
        technician_where_clause = ""
        if bi != "0":
            technician_where_clause = f"AND business_unit_id = '{bi}'"
        if shop != "0":
            technician_where_clause = f"AND shop_id = '{shop}'" 
        cur.execute(f"SELECT id,name FROM technicians WHERE id != 0 {technician_where_clause} ORDER BY id;")
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
    return render_template('report_graph_view.html',extra_datas=[technicians_names,get_job_types,start_dt,end_dt,shop_name],total_result = total_result,)

@views.route("pic-report",methods=['GET','POST'])
def pic_report():
    if not request.cookies.get('pg-username'): 
        return redirect(url_for('views.home'))
    if request.method == 'POST':
        conn = db_connect()
        cur = conn.cursor()
        start_dt = request.form.get('start-dt')
        end_dt = request.form.get('end-dt')
        bi_id = request.form.get('bi')
        shop_id = request.form.get('shop')
        technician_where_clause = ""
        if bi_id != "0":
            technician_where_clause = f"AND business_unit_id = '{bi_id}'"
        if shop_id != "0":
            technician_where_clause = f"AND shop_id = '{shop_id}'"            
        where_clause = ""
        where_clause += f"AND ej.business_unit_id = '{bi_id}' " if bi_id != '0' else ""
        where_clause += f"AND ej.shop_id = '{shop_id}' " if shop_id != '0' else ""
        cur.execute("SELECT id,name FROM jobType ORDER BY id;")
        job_types = cur.fetchall()
        cur.execute(f"SELECT id,name FROM technicians WHERE id != 0  {technician_where_clause} ORDER BY id;")
        technicians_ids = cur.fetchall()
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
            result = [[] for _ in range(len(job_types))]
            for data in datas:
                for i,dt in enumerate(data[1:]):
                    result[i].append(dt)
            result[0].append(sum(result[0]))
            result = [item for subitem in result for item in subitem]
            total_result[technicians_names[idx]] = result
            if shop_id == '0':
                shop_name = 'ALL SHOPS'
            else:
                cur.execute("SELECT name FROM shop WHERE id = %s;",(shop_id,))        
                shop_name = cur.fetchall()[0][0]
    else:
        return redirect(url_for('views.home'))
    return render_template('pic_report.html',total_result=total_result,job_types=job_types,extra_datas = [start_dt,end_dt,shop_name])


@views.route("/show-datas/<typ>/<mgs>",methods=['GET'])
@views.route("/show-datas/<typ>",methods=['GET','POST'])
def show_service_datas(typ,mgs=None):
    if not request.cookies.get('user_roles') or not request.cookies.get('pg-username'):
        return redirect(url_for('views.home'))
    mgs = request.args.get("mgs")
    conn = db_connect()
    cur = conn.cursor()
    user_roles_lst = request.cookies.get('user_roles')
    extra_datas = []
    if request.method == 'POST':
        filt = True
        column = request.form.get('column')
        db = request.form.get('database')
        val = request.form.get('filter')
        bol = request.form.get('editOrSubmit')
        print(column,'this is filter',bol)
        if typ == 'service-datas':
            if db == 'eachJob':
                with_id_query =f""" SELECT 
                                        jb.job_date,unit.id,shop.id,jb.job_no,customer.name,vehicle.plate,jb.customer_id,jb.vehicle_id,customer.address,
                                        customer.phone,state.name,model.name,brand.name,model.brand_id,model.id,vehicle.year,jb.invoice_no,jb.business_unit_id,
                                        jb.shop_id,jb.job_name,jobType.name,jb.total_amt,t_one.name,t_two.name,
                                        t_three.name,t_four.name,t_five.name,pic.unique_rate,jb.id
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
                                    LEFT JOIN vehicle_model model
                                    ON model.id = vehicle.model_id
                                    LEFT JOIN vehicle_brand brand
                                    ON brand.id = model.brand_id
                                    LEFT JOIN state
                                    ON state.id = customer.state_id
                                    WHERE job_no = '{val}'
                                    ORDER BY jb.job_date DESC,job_no DESC;""" 
                query = f""" WITH month_cte AS (
                    SELECT
                        month_id,
                        TO_CHAR(DATE_TRUNC('month', TIMESTAMP '2000-01-01'::date + (month_id-1  || ' months')::interval), 'Month') AS month_text
                    FROM generate_series(1, 12) AS month_id
                    )
                    SELECT 
                        month_cte.month_text,jb.job_date,unit.name,shop.name,jb.job_no,customer.name,vehicle.plate,model.name,
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
                    LEFT JOIN vehicle_model model
                    ON model.id = vehicle.model_id
                    WHERE {column} iLIKE '%{val}%' AND shop.id IN ({user_roles_lst})
                    ORDER BY jb.job_date DESC,job_no DESC;"""
                print(bol)
                if eval(bol):
                    cur.execute(with_id_query)
                    result = []
                    result.append(cur.fetchall())
                    cur.execute("SELECT id,name FROM technicians WHERE shop_id = %s;",(result[0][0][18],))
                    result.append(cur.fetchall())
                    cur.execute("SELECT id,name FROM jobType;")
                    result.append(cur.fetchall())
                    cur.execute("SELECT unique_rate FROM pic;")
                    result.append(cur.fetchall())
                    result.append(datetime.now().year)
                    result.append(sum(data[21] for data in result[0]))
                    return render_template('edit_form.html',result = result)
                cur.execute(query)
                result = cur.fetchall()
                cur.execute(f"SELECT count(jb.id) FROM eachJob jb LEFT JOIN vehicle ON vehicle.id = jb.vehicle_id  LEFT JOIN res_partner AS unit ON unit.id = jb.business_unit_id LEFT JOIN shop ON shop.id = jb.shop_id LEFT JOIN customer ON customer.id = jb.customer_id WHERE {column} iLIKE '%{val}%';")
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
                return render_template("registration_form.html",result=result,typ=typ)
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
                return render_template("registration_form.html",result=result,typ=typ)
            else:
                cur.execute(f"SELECT car.id,car.plate,brand.name,model.name,car.year FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id WHERE {column} iLIKE '%{val}%' ORDER BY plate desc;")
                result = cur.fetchall()
                cur.execute(f"SELECT count(car.id) FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id  WHERE {column} iLIKE '%{val}%';")  
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
            return render_template('view_datas.html',mgs=mgs,datas_dct=datas_dct,typ='brand')
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
            LEFT JOIN vehicle_model model
            ON model.id = vehicle.model_id
            WHERE shop.id IN ({user_roles_lst})
            ORDER BY jb.job_date DESC,job_no DESC
            LIMIT 81;"""
            length_query = f"SELECT count(eachJob.id) FROM eachJob LEFT JOIN shop ON eachJob.shop_id = shop.id WHERE shop.id in ({user_roles_lst});"
        elif typ == 'pic-rate':
            query = """ SELECT id,fst_rate,sec_rate,thrd_rate,frth_rate,lst_rate FROM pic ORDER BY id DESC;"""
            length_query = "SELECT count(id) FROM pic;"
        elif typ == 'technician':
            query = f""" SELECT tech.id,tech.name,bi.name,shop.name FROM technicians tech
                        INNER JOIN res_partner bi
                        ON bi.id = tech.business_unit_id
                        INNER JOIN shop
                        ON shop.id = tech.shop_id
                        WHERE tech.id != 0  ORDER BY tech.name; """
            cur.execute("SELECT name  FROM res_partner;")
            extra_datas.append(cur.fetchall())
            cur.execute("SELECT name  FROM shop;")
            extra_datas.append(cur.fetchall())
            length_query = f"SELECT count(technicians.id) FROM technicians;"
        elif typ == 'brand':
            cur.execute("select brand.name,model.name from vehicle_brand brand inner join vehicle_model model on brand.id = model.brand_id order by brand.name;")
            datas = cur.fetchall()
            datas_dct = {}
            for data in datas:
                if data[0] not in datas_dct:
                    datas_dct[data[0]] = [data[1]]
                else:
                    datas_dct[data[0]].append(data[1])
            return render_template('view_datas.html',mgs=mgs,datas_dct=datas_dct,typ='brand')
        elif typ == 'customers':
            query = "SELECT customer.id,code,customer.name,COALESCE(address,'Undefined'),COALESCE(state.name,'Undefined'),COALESCE(phone,'undefined') FROM customer LEFT JOIN state ON customer.state_id = state.id LIMIT 81;"
            length_query = "SELECT count(id) FROM customer;"
        elif typ == 'vehicles':
            query = "SELECT car.id,car.plate,brand.name,model.name,car.year FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id ORDER BY plate desc LIMIT 81;"
            length_query = "SELECT count(id) FROM vehicle;"
        else:
            query = """  SELECT id,name FROM jobType ORDER BY name;  """
            length_query = "SELECT count(id) FROM jobType;"
        cur.execute(query)
        result = cur.fetchall()
        cur.execute(length_query)
        length = cur.fetchall()
    print(mgs,"test")
    return render_template('view_datas.html',mgs=mgs,extra_datas=extra_datas,result=result,length=length,filt = filt,typ=typ)

@views.route("/get-data/<db>/<idd>")
def get_data(db,idd:str):
    conn = db_connect()
    cur = conn.cursor()
    if db == 'vehicle':
        plate = idd.split("||")[0]
        cus_id =  f"and customer.id = {idd.split('||')[1]}" if "||" in idd else ""
        cur.execute(f"""SELECT vehicle.plate,brand.name,model.name,customer.name,customer.phone,customer.state_id,customer.id,customer.address,vehicle.year,vehicle.id
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
    elif db == 'autofill-vehicle':
        cur.execute("SELECT car.plate,car.make,car.model,cus.name,cus.phone,state.name,cus.id FROM vehicle AS car INNER JOIN customer AS cus on cus.id = car.customer_id LEFT JOIN state ON state.id = cus.state_id WHERE plate = %s;",(idd,))
    elif db == 'autofill-customer':
        cur.execute("SELECT address,state_id,phone,id FROM customer WHERE name = %s;",(idd,))
    elif db == 'get-brand-model':
        cur.execute("SELECT brand_id,id FROM vehicle_model WHERE name = %s;",(idd,))
    elif db == 'eachJobDelForm':
        cur.execute("DELETE FROM eachJob WHERE job_no = %s;",(idd,))
        cur.execute("DELETE FROM psfu WHERE job_no = %s;",(idd,))
        conn.commit()
        return "Finished"
    elif db in ('pic','technicians','jobType'):
        try:
            cur.execute("DELETE FROM {} WHERE id = %s;".format(db), (idd,))
        except ForeignKeyViolation as err:
            return "failed"
        conn.commit()
        return "finished"
    elif db == 'vehicle_model':
        cur.execute("SELECT name FROM vehicle_model WHERE brand_id = (SELECT id FROM vehicle_brand WHERE name = %s);",(idd,))
    elif db == 'check-technician':
        name , shop_id = idd.split("|")
        print(name,shop_id)
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
        cur.execute("SELECT name FROM technicians WHERE shop_id = %s;",(idd,))
    elif db == 'ownership':
        vehicle_id,customer_id = idd.split("||")
        print(vehicle_id,customer_id)
        cur.execute("""INSERT INTO ownership(vehicle_id,customer_id,start_date,unique_owner)
                VALUES(%s,%s,%s,%s) ON CONFLICT (unique_owner) DO UPDATE set end_date = NULL""",(vehicle_id,customer_id,datetime.now().strftime("%Y-%m-%d"),vehicle_id+'-'+customer_id))
        cur.execute("UPDATE ownership SET end_date = %s WHERE vehicle_id = %s AND customer_id <> %s AND end_date IS  NULL;",(datetime.now().strftime("%Y-%m-%d"),vehicle_id,customer_id))
        conn.commit()
        return "Finished"
    elif db == 'deleteCustomersData':
        try:
            cur.execute("DELETE FROM customer WHERE id = %s;",(idd,))
            cur.execute("DELETE FROM ownership WHERE customer_id = %s RETURNING vehicle_id;",(idd,))
            vehicle_id = cur.fetchall()[0][0]
            cur.execute("DELETE FROM vehicle WHERE id = %s;",(vehicle_id,))
        except ForeignKeyViolation:
            return "failed"
        conn.commit()
        return "Finished"
    elif db == 'deleteVehiclesData':
        try:
            cur.execute("DELETE FROM vehicle WHERE id = %s;",(idd,))
        except ForeignKeyViolation:
            return 'failed'
        conn.commit()
        return "Finished"
    elif db in ('brand','model'):
        update_brand , brand = idd.split("~")
        cur.execute(f"UPDATE vehicle_{db} SET name = '{update_brand}' WHERE TRIM(name) = '{brand}' AND NOT EXISTS (SELECT 1 FROM vehicle_{db} WHERE name = '{update_brand}');")
        conn.commit()
        return "Finished"
    elif db == 'removeCall':
        cur.execute("DELETE FROM psfu WHERE job_no = %s;",(idd,))
        conn.commit()
        return "Finished"
    elif db == 'remove-access':
        user_role_name , mail = idd.split("|") 
        cur.execute("SELECT id FROM user_role WHERE name = %s;",(user_role_name,)) 
        user_role_id = str(cur.fetchall()[0][0])
        cur.execute("SELECT user_roles FROM user_auth WHERE mail = %s;",(mail,))
        user_role_ids = cur.fetchall()[0][0].split(",")
        if len(user_role_ids) > 1:           
            user_role_ids.remove(user_role_id) 
            cur.execute("UPDATE user_auth SET user_roles = %s WHERE mail = %s;",(",".join(map(str,user_role_ids)),mail))             
            conn.commit()
            return "Finished"
        else:
            return "Not"
    elif db == 'add-access':
        user_role_name , mail = idd.split("|")
        cur.execute("SELECT id FROM user_role WHERE name = %s;",(user_role_name,))
        user_role_id = cur.fetchall()
        if len(user_role_id) != 0:
            print(user_role_id)
            cur.execute("SELECT user_roles FROM user_auth WHERE mail = %s;",(mail,))
            user_role_ids = cur.fetchall()[0][0].split(",")
            if str(user_role_id[0][0]) not in user_role_ids:
                user_role_ids.append(user_role_id[0][0])
            cur.execute("UPDATE user_auth SET user_roles = %s WHERE mail = %s;",(",".join(map(str,user_role_ids)),mail))
            conn.commit()
        return f"{len(user_role_id)}"
    elif db == 'checkRegisteredUsers':
        registered_id , what = idd.split("|")
        if what == 't' or what == 'f':
            cur.execute("UPDATE user_auth SET pending = %s WHERE id = %s;",(what,registered_id))
        else:
            cur.execute("DELETE FROM user_auth WHERE id = %s;",(registered_id,))
        conn.commit()
        return "Finished"
    datas = cur.fetchall()
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
                            month_cte.month_text,jb.job_date,unit.name,shop.name,jb.job_no,customer.name,vehicle.plate,model.name,
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
                        LEFT JOIN vehicle_model model
                        ON model.id = jb.vehicle_id
                        ORDER BY jb.job_date DESC,job_no DESC
                        LIMIT 81 OFFSET {ofset};""",
            "customers":f"SELECT customer.id,code,customer.name,COALESCE(address,'Undefined'),COALESCE(state.name,'Undefined'),COALESCE(phone,'undefined') FROM customer LEFT JOIN state ON customer.state_id = state.id LIMIT 81 OFFSET {ofset};",
            "vehicles":f"SELECT car.id,car.plate,brand.name,model.name,car.year FROM vehicle AS car LEFT JOIN vehicle_brand AS brand ON brand.id = car.brand_id LEFT JOIN vehicle_model AS model ON model.id = car.model_id ORDER BY plate desc LIMIT 81 OFFSET {ofset};"
    }
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(queries_dct[for_what])
    result_datas = cur.fetchall()
    return jsonify(result_datas)