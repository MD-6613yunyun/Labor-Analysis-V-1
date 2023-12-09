from flask import Blueprint,render_template,request,jsonify,url_for,redirect, session
from website import db_connect, extract_shop_datas
from decimal import Decimal 
from datetime import datetime

dash = Blueprint('dash',__name__)

@dash.route("/")
def home():
    if 'pg_username' not in session or "pg_id" not in session:
        return redirect(url_for('views.home'))
    conn = db_connect()
    cur = conn.cursor()
    credentials , b_units = extract_shop_datas(cur)
    data_dct = {}
    max_psfu_dct = {}
    query = """ SELECT form.job_no,form.job_date,car.plate,cus.name,cus.phone,form.id,psfu.id,form.shop_id FROM psfu_call AS psfu
            INNER JOIN eachJobFORM AS form
            ON form.id = psfu.form_id
            LEFT JOIN vehicle car
            ON car.id = form.vehicle_id
            LEFT JOIN customer cus
            ON cus.id = form.customer_id
            WHERE form.shop_id = %s and form.job_date < CURRENT_DATE - 2 AND psfu.call_status_id IS NULL
            ORDER BY form.job_date LIMIT 20;"""
    for shop_id in credentials:
        cur.execute(query,(shop_id[2],))
        data_dct[shop_id[3]] = cur.fetchall()
        cur.execute("""
            SELECT COUNT(form.id) FROM psfu_call AS psfu
            INNER JOIN eachJobFORM AS form
            ON form.id = psfu.form_id
            WHERE form.shop_id = %s and form.job_date < CURRENT_DATE - 2;  """,(shop_id[2],))
        max_psfu_dct[shop_id[3]] = cur.fetchone()[0]
    cur.execute("SELECT id,name FROM call_status;")
    psfu_status = cur.fetchall()
    return render_template('dashboard.html',data_dct = data_dct,credentials = credentials,b_units = b_units,max_psfu_dct=max_psfu_dct,psfu_status=psfu_status)

@dash.route("/admin")
def admin_dashboard():
    if 'pg_username' not in session or "pg_id" not in session:
        return redirect(url_for('views.home'))
    conn = db_connect()
    cur = conn.cursor()
    credentials , b_units = extract_shop_datas(cur)
    cur.execute("SELECT id,name FROM user_role;")
    role_datas = {data[0] : data[1] for data in cur.fetchall()}
    cur.execute("SELECT name,mail,id,shop_ids FROM user_auth WHERE pending = '1' ORDER BY name;")
    result_dct = {}
    for data in cur.fetchall():
        result_dct[data[:3]] = [role_datas[idd] for idd in data[3]]
    cur.execute("SELECT id,name,mail FROM user_auth WHERE pending = '0' ORDER BY name;")
    return render_template("admin_panel.html",edit_account = [role_datas,result_dct],pending_users = cur.fetchall(),credentials=credentials,b_units=b_units)