
from app import create_app
from app.s3 import check_create_buckets
# from livereload import Server

app = create_app()

# app.debug = True
# server = Server(app.wsgi_app)
# server.serve()
