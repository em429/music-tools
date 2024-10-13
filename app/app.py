from flask import Flask
from models import init_db, close_db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'

    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    init_db(app)
    app.teardown_appcontext(close_db)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5001)
