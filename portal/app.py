from waitress import serve

from src import create_app

if __name__ == "__main__":
    app = create_app()
    # more threads since we may be blocking quite a bit for waiting for job pod completion
    serve(app, port=5000, threads=32)
