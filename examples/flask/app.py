from sqlalchemy.exc import OperationalError
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from tri.form.views import create_object, edit_object

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.debug = True
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return '<User %r>' % self.username


@app.route('/create/', methods=('GET', 'POST'))
def create():
    return create_object(request, User, save__db=db)


@app.route('/<int:user_id>/edit/', methods=('GET', 'POST'))
def edit(user_id):
    return edit_object(request, User.query.get(user_id), save__db=db)


@app.route('/')
def index():
    try:
        users = User.query.all()
    except OperationalError:
        db.create_all()
        users = User.query.all()
    user_list = ''.join(['<li><a href=/%s/edit/>%s</li>' % (x.id, x.username) for x in users])
    return """
        <a href="/create/">Create user</a>

        <p/>

        <ul>
            %s
        </ul>
        """ % user_list

if __name__ == '__main__':
    app.run()
