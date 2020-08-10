from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, bcrypt, User
from forms import NewUserForm, LoginForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():
    """ [TEMPORARY] redirects to /register """
    return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """ Show form that will register/create a user, and handle posting """
    form = NewUserForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password, first_name, last_name, email)
        db.session.add(new_user)
        db.session.commit()
        return redirect(f'/users/{username}')
    else:
        return render_template('user_register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """ Show log in form, and handle posting """
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)

        if user:
            flash(f"Welcome back, {user.first_name}", "success")
            session['user'] = user.username
            return redirect(f'/users/{username}')
        else:
            form.username.errors = ['Invalid username/password']

    return render_template('user_login.html', form=form)


@app.route('/users/<username>')
def show_user_details(username):
    """ This page can only be accessed by logged in users """
    if 'user' in session:
        user_info = User.query.get(username)
        return render_template('user_details.html', user=user_info)
    else:
        flash('Please log in to view content', 'danger')
        return redirect('/login')

@app.route('/logout')
def logout_user():
    """ Log Out User """
    flash("logged out", "info")
    session.pop('user')
    return redirect('/login')