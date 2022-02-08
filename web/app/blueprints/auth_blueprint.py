
from datetime import timedelta
from urllib.parse import urlparse, urljoin

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask import make_response
from app.models.auth_models import User, AccessGroup, AccessLink

from app.forms.auth_forms import LoginForm, SignupForm
from app import db



auth = Blueprint('auth', __name__)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def check_user_group_access(group_name: str) -> bool:

    access_group = db.session.query(AccessGroup).filter(AccessGroup.name == group_name).first()
    if access_group:
        has_access = db.session.query(AccessLink).filter_by("access_id" == access_group.id).filter_by("user_id" == current_user.id).first()

        if has_access:
            return True
        else:
            False
    else:
        raise ValueError('No access group found for name: {}'.format(group_name))


@login_required
@auth.route('/access/add/<group_name>', methods=['POST'])
def add_access_group(group_name: str):
    # TODO needs to add check for the user being in admin group
    new_access = AccessGroup(name="group_name")

    # add to sqlalchemy session
    db.session.add(new_access)

    # save to database
    db.session.commit()

    return 'Success'

@login_required
@auth.route('/access/update/<group_id>/<group_name>', methods=['POST'])
def update_access_group(group_id, group_name):
    # TODO needs to add check for the user being in admin group

    access_group_obj = db.session.query(AccessGroup).filter(AccessGroup.id == group_id).first()
    access_group_obj.name = group_name
    # save to database
    db.session.commit()

    return 'Success'

@login_required
@auth.route('/auth/access/add_to_group/<user_id>/<group_id>', methods=['POST'])
def add_user_to_access_group(user_id, group_id):
    # TODO needs to add check for the user being in admin group
    user_obj = db.session.query(User).filter(User.id == user_id).first()

    if user_obj:
        # query access
        access_group = db.session.query(AccessGroup).filter(AccessGroup.id == group_id).first()
        if access_group:
            a = AccessLink()
            a.user_id = user_obj.id
            a.access_id = access_group.id
            db.session.add(a)
            db.session.commit()
            return 'Success'

        else:
            print("No access group found with id: {}".format(db.access_id))
    else:

        print("No user found with id: {}".format(user_id))

@login_required
@auth.route('/auth/access/add_to_group/<user_id>/<group_id>', methods=['POST'])
def remove_user_from_access_group(user_id, group_id):
    # TODO needs to add check for the user being in admin group
    a = db.session.query(AccessLink).filter_by("access_id" == group_id).filter_by("user_id" == user_id).first()

    if a:
        db.session.delete(a)
        db.session.commit()

    else:
        print("No Access Link found for access_id id: {}, and user id {}".format(group_id, user_id))


@auth.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        next_url = request.args.get('next')
        if not is_safe_url(next_url):
            return abort(400)
        return redirect(next_url or url_for('main.index'))

    else:
        # token = request.cookies.get('_oauth2_proxy')
        email = request.headers.get('X-Forwarded-User')
        
        #token = request.cookies.get('_oauth2_proxy')
        
        #if not token:
        #    token = request.cookies.get('corems_oauth2_proxy')
        
        #if email and not token:
        #    response = make_response(redirect("{}oauth2/sign_in".format(request.host_url)))
        #    return response

        if email and request.method == 'GET':
            
            name = request.headers.get('X-Forwarded-User').split('@')[0]
            user = User.query.filter_by(email=email).first()
            if not user:
                new_user = User()
                sliced_name = name.split(".")
                if len(sliced_name) > 1:
                    first_name = sliced_name[0].capitalize()
                    last_name = sliced_name[1].capitalize()
                else:
                    first_name = name.capitalize()
                    last_name = first_name

                new_user = User(email=email, first_name=first_name,
                                last_name=last_name)

                db.session.add(new_user)
                db.session.commit()

                next_url = request.args.get('next')
                
                login_user(new_user, remember=True, duration=timedelta(hours=12))
                if not is_safe_url(next_url):
                    return abort(400)
                return redirect(next_url or url_for('main.index'))

            else:

                next_url = request.args.get('next')
                login_user(user, remember=True, duration=timedelta(hours=12))
                if not is_safe_url(next_url):
                    return abort(400)
                return redirect(next_url or url_for('main.index'))

        else:

            form = LoginForm()
            if request.method == 'POST':
                if form.validate_on_submit():

                    # username = form.username.data
                    email = form.email.data
                    password = form.password.data
                    remember = True if form.remember_user.data else False

                    user = User.query.filter_by(email=email).first()

                    if not user or not user.check_password(password):
                        flash('Incorrect login details, please try again.')
                        return render_template('auth/login.html', form=form)

                    login_user(user, remember=remember, duration=timedelta(hours=12))
                    next_url = request.args.get('next')
                    if not is_safe_url(next_url):
                        return abort(400)
                    return redirect(next_url or url_for('main.index'))
            else:
                # get method
                return render_template('auth/login.html', form=form)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():

    form = SignupForm()

    if form.validate_on_submit():

        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user:  # if a user is found,redirect back to signup page so user can try again
            flash('Email address already exists')
            return redirect(url_for('auth.signup'))
        # code to validate and add user to database goes here
        else:
            new_user = User()
            new_user = User(email=email, first_name=first_name, last_name=last_name)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=True, duration=timedelta(hours=12))
            return redirect(url_for('main.profile'))

    return render_template('auth/signup.html', form=form)

@auth.route('/logout')
@login_required
def logout():

    logout_user()
    email = request.headers.get('X-Forwarded-User')
    if email:

        response = make_response(redirect("{}oauth2/sign_in".format(request.host_url)))
        # response.set_cookie('_oauth2_proxy', request.cookies.get('_oauth2_proxy'))

        return response

    else:

        return redirect(url_for('auth.login'))
