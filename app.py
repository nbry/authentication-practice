from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, bcrypt, User, Feedback
from forms import NewUserForm, LoginForm, NewFeedback
from sqlalchemy.exc import IntegrityError, DataError

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

        new_user = User.register(
            username, password, first_name, last_name, email)
        db.session.add(new_user)
        try:
            db.session.commit()
        except DataError:
            form.username.errors.append(
                'Username too long. Must be 20 characters or less')
            return render_template('user_register.html', form=form)

        session['user'] = username
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
        feedback = Feedback.query.filter(Feedback.username == username)
        return render_template('user_details.html', user=user_info, feedback=feedback)
    else:
        flash('Please log in to view content', 'danger')
        return redirect('/login')


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """ Remove a user """
    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop('user')
    flash('User account deleted')
    return redirect('/login')


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    form = NewFeedback()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(
            title=title, content=content, username=username)

        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f'/users/{username}')

    return render_template('feedback_new.html', form=form)


@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    """ Show form for user to update their own feedback item """
    feedback = Feedback.query.get(feedback_id)
    if feedback.user.username != session['user']:
        flash("You do not have access to this route", "danger")
        return redirect(f'/users/{feedback.user.username}')

    form = NewFeedback(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        return redirect(f'/users/{feedback.user.username}')
    else:
        return render_template('feedback_update.html', form=form)


@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """ Allow user to delete their own feedback items """
    feedback = Feedback.query.get(feedback_id)
    if feedback.user.username != session['user']:
        flash("You cannot delete someone else's feedback", "danger")
        return redirect(f'/users/{feedback.user.username}')

    db.session.delete(feedback)
    db.session.commit()
    return redirect(f"/users/{session['user']}")

@app.route('/logout')
def logout_user():
    """ Log Out User """
    flash("logged out", "info")
    session.pop('user')
    return redirect('/login')
