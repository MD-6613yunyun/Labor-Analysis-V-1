from flask import Flask,render_template,abort,session
import psycopg2
    
def db_connect():
    # Database connection details
    host = 'localhost'
    port = '5432'  # Default PostgreSQL port
    database = 'mmm_pandg'
    user = 'postgres'
    password = 'md-6613'

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            client_encoding = 'UTF8'
        )
        print('Connected to the database successfully!')
        return conn
    except psycopg2.Error as e:
        print('Error connecting to the database:', e)

def catch_db_insert_error(cur,con,queries):
    try:
        for query in queries:
            cur.execute(query)
        con.commit()
    except psycopg2.IntegrityError as e:
        print(e)
        con.rollback()
        return str(e).title()
    else:
        return None
    
def extract_shop_datas(cur):
    cur.execute(""" SELECT user_auth.id,is_admin,shop.id,shop.name,bi.id,bi.name
                            FROM user_auth 
                        INNER JOIN 
                            shop ON  
                        shop.id =  ANY(SELECT * from UNNEST(user_auth.shop_ids))
                        LEFT JOIN
                            res_partner AS bi
                        ON bi.id = shop.business_unit_id
                        WHERE user_auth.id = %s;""",(session['pg_id'],))
    credentials = cur.fetchall()
    print(credentials)
    b_units = set([(dt[4],dt[5]) for dt in credentials])
    print(b_units)    
    return credentials , b_units

def create_app():
    app = Flask(__name__)
    app.config['secret_key'] = "95d7a5e73fab58a0c004f12a79b80969b1310f9ef8dad1ff2cce0f87ff36a6de"
    app.secret_key = app.config['secret_key']
    from .views import views
    from .auth import auth
    from .imports import imports
    from .dashboard import dash
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth,url_prefix='/auth')
    app.register_blueprint(imports,url_prefix='/import')
    app.register_blueprint(dash,url_prefix='/dashboard')

    #Handling error 404 and displaying relevant web page
    @app.errorhandler(404)
    @app.errorhandler(500)
    def handle_error(error):
        return render_template('error_pages.html',error=error),error.code

    return app
