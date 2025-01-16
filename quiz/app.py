from waitress import serve

from src import create_app

if __name__ == "__main__":
    app = create_app()
    serve(app, port=5000)
