from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
#from waitress import serve # new

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = 'you-will-never-guess'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models, forms
#serve(app, listen='0.0.0.0:5000', url_scheme='https')

#test 2