from flask import Blueprint,render_template,request,redirect,url_for,after_this_request
from website import db_connect
from psycopg2 import IntegrityError
from datetime import datetime,timedelta
auth = Blueprint('auth',__name__)


@auth.route("/")
@auth.route("/<typ>",methods = ['GET','POST'])
def authenticate(typ='log'):
    if request.method == 'POST':
        conn = db_connect()
        cur = conn.cursor()
        if typ == 'log':
            mail = request.form.get("email")
            pwd = request.form.get("password")
            print(mail,pwd)
            cur.execute("SELECT pwd,name FROM user_auth WHERE mail = %s",(mail,))
            db_data = cur.fetchall()
            db_pwd = db_data[0][0] if db_data != [] else None
            print(pwd,db_pwd)
            if db_pwd == pwd:
                @after_this_request
                def after_index(response):
                    response.set_cookie("username",db_data[0][1],expires=datetime.now() + timedelta(seconds=10))
                    return response
                return redirect(url_for('views.home'))
            else:
                return render_template('auth.html',mgs='Wrong Credentials',typ='log')
        else:
            name = request.form.get("username")
            mail = request.form.get("email")
            pwd = request.form.get("password")
            confirmPwd = request.form.get("confirmPassword")
            print(name,mail,pwd,confirmPwd)
            if typ == 'reg':
                if pwd == confirmPwd:
                    try:
                        cur.execute("INSERT INTO user_auth (name,mail,pwd) VALUES (%s,%s,%s)",(name,mail,pwd))
                        conn.commit()
                        return redirect(url_for('auth.authenticate',typ='log'))
                    except IntegrityError as err:
                        print(err)
                        return render_template('auth.html',mgs='Already Registered',typ='reg')
                else:
                    return render_template('auth.html',mgs='Unmatched Password',typ='reg')
            elif typ == 'forgot':
                cur.execute("SELECT name FROM user_auth WHERE mail = %s",(mail,))
                data = cur.fetchall()
                db_name = data[0][0] if data != [] else None
                if db_name == name:
                    if pwd == confirmPwd:
                        cur.execute("UPDATE user_auth SET pwd = %s WHERE mail = %s;",(pwd,mail))
                        conn.commit()
                        return redirect(url_for('auth.authenticate',typ='log'))
                    else:
                        return render_template('auth.html',mgs='Unmatched Password',typ='forgot')
                else:
                    return render_template('auth.html',mgs='Invalid Credentials',typ='forgot')
    else:
        return render_template('auth.html',typ=typ,mgs=None)

@auth.route("auth/checkforget/<email>/<name>")
def checkforget(name,email):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT name FROM user_auth WHERE mail = %s;",(email,))
    db_data = cur.fetchall()
    db_name = db_data[0][0] if db_data != [] else None
    if db_name == name:
        return [1]
    else:
        return [0]