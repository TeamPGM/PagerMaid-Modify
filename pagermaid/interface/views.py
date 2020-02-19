""" Static views generated for PagerMaid. """

from pathlib import Path
from psutil import virtual_memory
from os.path import exists
from sys import platform
from platform import uname, python_version
from telethon import version as telethon_version
from flask import render_template, request, url_for, redirect, send_from_directory
from flask_login import login_user, logout_user, current_user
from pagermaid import logs, redis_status
from pagermaid.interface import app, login
from pagermaid.interface.modals import User
from pagermaid.interface.forms import LoginForm, SetupForm, ModifyForm


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/setup", methods=['GET', 'POST'])
def setup():
    form = SetupForm(request.form)
    msg = None
    if request.method == 'GET':
        if exists('data/.user_configured'):
            return redirect(url_for('login'), code=302)
        return render_template('pages/setup.html', form=form, msg=msg)
    if form.validate_on_submit():
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str)
        email = request.form.get('email', '', type=str)
        user = User.query.filter_by(user=username).first()
        user_by_email = User.query.filter_by(email=email).first()
        if user or user_by_email:
            msg = 'This email already exist on this system, sign in if it is yours.'
        else:
            pw_hash = password
            user = User(username, email, pw_hash)
            user.save()
            Path('data/.user_configured').touch()
            return redirect(url_for('login'), code=302)
    else:
        msg = 'Invalid input.'
    return render_template('pages/setup.html', form=form, msg=msg)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not exists('data/.user_configured'):
        return redirect(url_for('setup'), code=302)
    form = LoginForm(request.form)
    msg = None
    if form.validate_on_submit():
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str)
        user = User.query.filter_by(user=username).first()
        if user:
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                msg = "用户名或密码错误。"
        else:
            msg = "此用户不存在"
    return render_template('pages/login.html', form=form, msg=msg)


@app.route('/style.css')
def style():
    return send_from_directory('static', 'style.css')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')


@app.route('/settings')
def settings():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('pages/settings.html')


@app.route('/profile')
def profile():
    if not current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = ModifyForm(request.form)
    msg = None
    return render_template('pages/profile.html', form=form, msg=msg)


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    memory = virtual_memory()
    memory_total = memory.total
    memory_available = memory.available
    memory_available_percentage = round(100 * float(memory_available)/float(memory_total), 2)
    memory_free = memory.free
    memory_free_percentage = round(100 * float(memory_free) / float(memory_total), 2)
    memory_buffered = memory.buffers
    memory_buffered_percentage = round(100 * float(memory_buffered) / float(memory_total), 2)
    memory_cached = memory.cached
    memory_cached_percentage = round(100 * float(memory_cached) / float(memory_total), 2)
    return render_template('pages/index.html',
                           hostname=uname().node,
                           platform=platform,
                           kernel=uname().release,
                           python=python_version(),
                           telethon=telethon_version.__version__,
                           redis="Connected" if redis_status() else "Disconnected",
                           memory_total=round(memory_total/1048576, 2),
                           memory_available=round(memory_available/1048576, 2),
                           memory_available_percentage=memory_available_percentage,
                           memory_free=round(memory_free/1048576, 2),
                           memory_free_percentage=memory_free_percentage,
                           memory_buffered=round(memory_buffered/1048576, 2),
                           memory_buffered_percentage=memory_buffered_percentage,
                           memory_cached=round(memory_cached/1048576, 2),
                           memory_cached_percentage=memory_cached_percentage)


@app.errorhandler(404)
def no_such_file_or_directory(exception):
    logs.debug(exception)
    return render_template('pages/404.html')


@app.errorhandler(500)
def internal_server_error(exception):
    logs.error(exception)
    return render_template('pages/500.html')
