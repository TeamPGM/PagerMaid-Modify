""" PagerMaid web interface utility. """

from os import environ
from threading import Thread
from distutils.util import strtobool
from importlib import import_module
from cheroot.wsgi import Server as WSGIServer, PathInfoDispatcher
from flask import Flask
from flask.logging import default_handler
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

try:
    from pagermaid import config, working_dir, logs, logging_handler
except ModuleNotFoundError:
    print("出错了呜呜呜 ~ 此模块不应直接运行。")
    exit(1)

app = Flask("pagermaid")
app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = config['web_interface']['secret_key']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{working_dir}/data/web_interface.db"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login = LoginManager()
login.init_app(app)


@app.before_first_request
def init_db():
    db.create_all()


import_module('pagermaid.interface.views')
import_module('pagermaid.interface.modals')

dispatcher = PathInfoDispatcher({'/': app})
web_host = config['web_interface']['host']
try:
    web_port = int(config['web_interface']['port'])
except ValueError:
    web_port = 3333
if environ.get('PORT'):
    web_host = '0.0.0.0'
    try:
        web_port = int(environ.get('PORT'))
    except ValueError:
        web_port = 3333
server = WSGIServer((web_host, web_port), dispatcher)


def start():
    if strtobool(config['web_interface']['enable']) or environ.get('PORT'):
        logs.info(f"已经启动Web界面 {web_host}:{web_port}")
        app.logger.removeHandler(default_handler)
        # app.logger.addHandler(logging_handler)
        try:
            server.start()
        except OSError:
            logs.fatal("出错了呜呜呜 ~ 另一个进程绑定到了 PagerMaid 需要的端口！")
            return
    else:
        logs.info("Web 界面已禁用。")


Thread(target=start).start()
