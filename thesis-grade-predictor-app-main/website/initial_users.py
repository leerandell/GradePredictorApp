from .db_model import User
from . import db
from werkzeug.security import generate_password_hash

def add_initial_users(app):
    with app.app_context():
        if not User.query.first():
            # Add initial users with a valid 'name'
            user1 = User(email='user1@gmail.com', name='Teacher 1', password=generate_password_hash('password1'))
            user2 = User(email='user2@gmail.com', name='Teacher 2', password=generate_password_hash('password2'))

            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            print('Initial users added!')
