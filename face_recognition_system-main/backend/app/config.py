import os

class Config:

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_12345')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt_secret_key_67890')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES=120
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_FAILED_ATTEMPTS = 5
    LOCK_DURATION_MINUTES = 30
    SESSION_DURATION_HOURS = 2
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'  # Dạng: Bearer <token>
    MIN_PASSWORD_LENGTH = 6
    MAX_LOGIN_ATTEMPTS = 5


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'