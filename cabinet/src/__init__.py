import os
import logging
from flask import Flask, session
#from flask_session import Session
from redis import StrictRedis
#from sqlalchemy import text

#from src.db import db, migrate
#from src.login import login
#from src.routes import routes

# Configure logging to output to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Get the root logger and add the console handler
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    PREFERRED_URL_SCHEME = "https"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_SERIALIZATION_FORMAT = "json"
    logger.info("Configuration of SESSION_REDIS")
    SESSION_REDIS = StrictRedis(
        host=os.getenv("REDIS_HOST", "cache"),
        port=6379,
        db=0,
    )

def create_app():
    logger.info("Starting application creation")
    
    app = Flask(__name__)
    logger.info("Flask app instance created")

    logger.info("Import flask_sesson")
    from flask_session import Session
    logger.info("flask_sesson imported")
    logger.info("Import src.routes")
    from src.routes import routes 
    logger.info("src.routes imported")
    logger.info("Load Config class")
    app.config.from_object(Config)
    logger.info("Configuration loaded from Config class")
    
    # Initialize login manager
    from src.login import login
    login.init_app(app)
    login.login_view = "routes.login"
    logger.info("Login manager initialized with login view set to 'routes.login'")
    
    # Initialize session
    Session(app)
    logger.info("Session initialized")
    
    # Initialize database
    from src.routes import routes
    from src.db import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    logger.info("Database and migrations initialized")
    
    # Register blueprint
    from src.routes import routes
    app.register_blueprint(routes)
    logger.info("Routes blueprint registered")
    
    # Uncomment if you want to test database connection on startup
    # with app.app_context():
    #    try:
    #        db.session.execute(text("SELECT 1"))
    #        logger.info("Database connection test successful")
    #    except Exception as exc:
    #        logger.critical(f"Database connection failed: {exc}")
    #        # violently quit :)
    #        os._exit(1)

    # Log environment variables
    #logger.info("Environment variables:")
    #for k, v in os.environ.items():
    #    logger.debug(f"{k}: {v}")
    
    logger.debug("Application creation completed")
    return app
