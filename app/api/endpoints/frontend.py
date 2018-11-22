from flask import send_file
from app.core import app
import os


@app.route('/')
def front_end():
    index_path = os.path.join(app.static_folder, 'index.html')
    return send_file(index_path)


# TODO - Check Angular router to get static files instead of this
# Everything not declared before (not a Flask route / API endpoint)...
@app.route('/<path:path>')
def route_frontend(path):
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(app.static_folder, 'index.html')
        return send_file(index_path)
