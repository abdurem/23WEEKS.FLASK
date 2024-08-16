import os
from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import upgrade

app = create_app()
cli = FlaskGroup(app)

if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'migrations')):
            os.system('flask db init')
        os.system('flask db migrate -m "Render deployment migration"')
        upgrade()
    
    from wsgi import app as application
    port = int(os.environ.get("PORT", 10000))
    application.run(host="0.0.0.0", port=port)