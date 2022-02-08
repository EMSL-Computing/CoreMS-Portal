
import datetime
import os

import pytz
from flask import Blueprint, render_template, request, url_for, redirect
from flask_login import login_required, current_user

from app.models.ftms_model import FTMS_Result
from app.models.auth_models import User
from app.forms.auth_forms import ProfileForm
from app import db


main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():

    # readme_file = open("README.md", "r")
    # md_template_string = markdown.markdown(
    #     readme_file.read(), extensions=["fenced_code"]
    # )

    # with open(os.getcwd() + '/app/static/help/welcome.md', 'r') as mkdfile:
    #    mkd_text = mkdfile.read()

    # input_file = codecs.open("README.md", mode="r", encoding="utf-8")
    # text = input_file.read()
    # html = markdown(text)

    # print(html)
    return render_template('welcome.html')

@main.route('/help')
@login_required
def help():
    with open(os.getcwd() + '/app/static/help/start.md', 'r') as mkdfile:
        mkd_text = mkdfile.read()
    return render_template('help.html', mkd_text=mkd_text)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    profile_form = ProfileForm()
    if request.method == 'POST':
        if profile_form.validate_on_submit():
            user = User.query.filter_by(email=current_user.email).first()
            user.first_name = profile_form.first_name.data
            user.last_name = profile_form.last_name.data
            db.session.commit()
    else:
        profile_form.email.data = current_user.email
        profile_form.first_name.data = current_user.first_name
        profile_form.last_name.data = current_user.last_name

    return render_template('profile.html', profile_form=profile_form)

@main.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@main.route('/time')
def get_current_time():

    utc_now = pytz.utc.localize(datetime.utcnow())

    pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))

    return {'time': pst_now}
