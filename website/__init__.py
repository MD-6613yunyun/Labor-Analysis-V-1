from flask import Flask
import psycopg2
    
def db_connect():
    # Database connection details
    host = '192.168.0.167'
    port = '9876'  # Default PostgreSQL port
    database = 'mmm_test'
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

def create_app():
    app = Flask(__name__)
    app.config['secret_key'] = "maMA123jeh3ojdojfioejjr(3eeijej3)"

    from .views import views
    from .auth import auth
    from .imports import imports
    # from .imports import imports

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth,url_prefix='/auth')
    app.register_blueprint(imports,url_prefix='/import')
    # app.register_blueprint(exports,url_prefix='/export')
    # app.register_blueprint(imports,url_prefix='/import')

    return app
