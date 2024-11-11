from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()  # Create an instance of Migrate

def create_app():
    app = Flask(__name__)

    # Configuring database URI from environment variable
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://thesis_db_ed13_user:2EynCtGQrO7mnQIFGerPNqcrdC0Eozr3@dpg-crl4ncij1k6c73flts5g-a/thesis_db_ed13'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    
    # Additional configurations
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SECRET_KEY'] = 'thesis_local'

    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate with the app and database

    # Register blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Create database and add initial users
    from .db_model import User
    from .initial_users import add_initial_users

    create_database(app)
    add_initial_users(app)

    # Login management
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    # Only useful for SQLite in local development
    with app.app_context():
        db.create_all()
    print('Database initialized!')