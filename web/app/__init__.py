__version__ = "3.9.7.beta"

from datetime import datetime
import logging
import os
import base64
import json
import re


from celery import Celery
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flaskext.markdown import Markdown

from app.config import Config
from app.s3 import s3_init, minio_init, check_create_buckets
# init SQLAlchemy so we can use it later in our models
# session_options={'autocommit': True}

# do not change the order of minio and s3 initi


minio = minio_init()
s3, s3_client = s3_init()

db = SQLAlchemy()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

def formart_json(input_dict):

    output = json.dumps(input_dict, sort_keys=False, indent=4, separators=(',', ': '))
    return re.sub(r'",\s+', '", ', output)

def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    celery.conf.update(app.config)
    # celery.config_from_object('celeryconfig')
    md = Markdown(app,
                  extensions=['nl2br'],
                  safe_mode=True,
                  output_format='html4',
                  )

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('corems')

    db.init_app(app)

    migrate = Migrate()
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = "strong"
    login_manager.init_app(app)

    from app.models.auth_models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    '''
    @login_manager.request_loader
    def load_user_from_request(request):

        # first, try to login using the api_key url arg
        api_key = request.args.get('api_key')
        if api_key:
            user = User.query.filter_by(api_key=api_key).first()
            if user:
                return user

        # next, try to login using Basic Auth
        api_key = request.headers.get('Authorization')
        if api_key:
            api_key = api_key.replace('Basic ', '', 1)
            try:
                api_key = base64.b64decode(api_key)
            except TypeError:
                pass
            user = User.query.filter_by(api_key=api_key).first()
            if user:
                return user

        # finally, return None if both methods did not login the user
        return None
    '''
    # blueprint for auth routes in our app
    from app.blueprints.auth_blueprint import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from app.blueprints.main_blueprint import main as main_blueprint
    from app.blueprints.gcms.gcms_blueprint import gcms as gcms_blueprint
    from app.blueprints.ftms.ftms_blueprint import fticrms as ftms_blueprint
    from app.blueprints.instrument.ftms_inst_blueprint import ftms_instrument as ftms_inst_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(gcms_blueprint)
    app.register_blueprint(ftms_blueprint)
    app.register_blueprint(ftms_inst_blueprint)

    check_create_buckets(minio, ['fticr-data', 'gcms-data'])

    @app.context_processor
    def utility_processor():
        def c_version():
            return str(__version__)
        return dict(current_version=c_version())

    return app
