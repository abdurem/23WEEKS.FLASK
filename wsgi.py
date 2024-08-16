import os
from flask_migrate import upgrade
from app import create_app, db

app = create_app()

def run_migrations():
    with app.app_context():
        upgrade()

if __name__ == "__main__":
    run_migrations()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)