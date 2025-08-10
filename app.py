from flask import Flask
from views import views
from models import db
from flask_migrate import Migrate
import os

app = Flask(__name__)

db_url = os.getenv('DATABASE_URL', 'sqlite:///galery.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ayan.dev-secret-key")

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(views)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()