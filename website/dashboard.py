from flask import Blueprint,render_template,request,jsonify,url_for,redirect
from website import db_connect
from decimal import Decimal 
from datetime import datetime

dash = Blueprint('dash',__name__)

@dash.route("/")
def home():
    if not request.cookies.get('user_roles') or not request.cookies.get('pg-username'):
        return redirect(url_for('views.home'))
    conn = db_connect()
    cur = conn.cursor()
    user_roles_lst = tuple(request.cookies.get('user_roles').split(","))
    print(user_roles_lst)
    cur.execute("SELECT id,name FROM shop WHERE id in %s;",(user_roles_lst,))
    print(user_roles_lst)
    data_dct = {}
    shop_ids = cur.fetchall()
    print(shop_ids)
    query = """ SELECT DISTINCT psfu.job_no,jb.job_date,car.plate,cus.name,cus.phone FROM psfu
            INNER JOIN eachJob jb
            ON jb.job_no = psfu.job_no
            LEFT JOIN vehicle car
            ON car.id = jb.vehicle_id
            LEFT JOIN customer cus
            ON cus.id = jb.customer_id
            WHERE jb.shop_id = %s and jb.job_date < CURRENT_DATE - 2
            ORDER BY jb.job_date; """
    for shop_id in shop_ids:
        cur.execute(query,(shop_id[0],))
        data_dct[shop_id[1]] = cur.fetchall()
    # print(data_dct)
    return render_template('dashboard.html',data_dct = data_dct)

@dash.route("/admin")
def admin_dashboard():
    if not request.cookies.get('user_roles') or not request.cookies.get('pg-username'):
        return redirect(url_for('views.home'))
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT id,name FROM user_role;")
    role_datas = {str(data[0]) : data[1] for data in cur.fetchall()}
    cur.execute("SELECT name,mail,id,user_roles FROM user_auth WHERE pending = '1' ORDER BY name;")
    result_dct = {}
    for data in cur.fetchall():
        result_dct[data[:3]] = [role_datas[idd] for idd in data[-1].split(",")]
    cur.execute("SELECT id,name,mail FROM user_auth WHERE pending = '0' ORDER BY name;")
    return render_template("admin_panel.html",edit_account = [role_datas,result_dct],pending_users = cur.fetchall())