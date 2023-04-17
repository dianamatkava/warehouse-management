import os

from environs import Env
from flask import Flask
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, current_user, login_required

from arb.models import *
from auth.models import *
from extensions import admin, db, migrate

env = Env()
env.read_env()


def create_app():
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Configs
    app.config.from_mapping(
        FLASK_APP = env.str('FLASK_APP', default='app.py'),
        FLASK_DEBUG = env.str('FLASK_DEBUG', default=True),
        SECRET_KEY = env.str(
            'SECRET_KEY', default='MY_SECRET_KEY'
        ),
        SQLALCHEMY_DATABASE_URI = env.str(
            'SQLALCHEMY_DATABASE_URI', default='sqlite:///arb.sqlite3'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS = True,
        FLASK_ADMIN_SWATCH = 'cerulean'
    )
        
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Registered extensions
    with app.app_context():
        db.init_app(app)
        db.create_all()
        
    
    # Apps
    migrate.init_app(app, db, render_as_batch=True)
    admin.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    
    # Protect Admin Middleware
    class CustomModelView(ModelView):
        @login_required
        def is_accessible(self):
            return current_user.is_authenticated
    
    # Register admin tables
    admin.add_view(CustomModelView(CustomerData, db.session))
    admin.add_view(CustomModelView(Translation, db.session))
    
    
    # Register blueprints
    from auth.routes import auth as blueprint
    app.register_blueprint(blueprint)
    
    from arb.routes import arb
    app.register_blueprint(arb)

    return app

app = create_app()
