from flask import Blueprint, render_template, abort, redirect, url_for, request, current_app
import json
from werkzeug.utils import secure_filename
from models import db, Poster
import os
import uuid

views = Blueprint('views', __name__)

@views.route("/")
def index():
    posters = Poster.query.all()
    return render_template('index.html', posters=posters)

@views.route("/<string:p_title>/<int:poster_id>")
def gallery(p_title, poster_id):
    poster = Poster.query.get_or_404(poster_id)
    if poster.title.lower().replace(" ", "-") != p_title.lower().replace(" ", "-"):
        return redirect(
            url_for(
                'views.gallery',
                p_title = poster.title.lower().replace(" ", "-"),
                poster_id = poster.poster_id
            )
        )
    return render_template("poster_view.html", poster=poster)
    

@views.route("/explore")
def explore():
    with open("info.json", "r") as f:
        data = json.load(f)    
    return render_template('explore.html', data=data)

@views.route("/explore/<int:p_id>")
def poster(p_id):
    with open("info.json", "r") as f:
        data = json.load(f)
    poster = next(
        (item for item in data if item.get("id") == p_id), 
        None
    )
    if not poster:
        abort(404)
    return render_template("poster.html", poster=poster)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route("/create", methods=["POST", "GET"])
def create():
    """Create new poster."""
    if request.method == "POST":
        owner = request.form.get('owner')
        title = request.form.get('title')
        file = request.files.get('poster_img')

        # Validation
        if not owner or not title:
            return "Owner and Title are required!", 400

        if not file or file.filename == '':
            return "No file selected", 400

        if not allowed_file(file.filename):
            return "File type not allowed", 400

        # Build a unique filename (preserve original name + unique suffix)
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"

        # Ensure upload folder exists (default to static/uploads if not configured)
        upload_folder = current_app.config.get(
            'UPLOAD_FOLDER',
            os.path.join(current_app.static_folder, 'uploads')
        )
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, unique_filename)

        # Save file + store DB record. Rollback & cleanup if something goes wrong.
        try:
            file.save(file_path)

            # Store a relative path that your templates can use via url_for('static', filename=...)
            # e.g. if upload_folder is static/uploads, store "uploads/<filename>"
            relative_path = os.path.join('uploads', unique_filename).replace('\\', '/')

            new_poster = Poster(owner=owner, title=title, poster_img=relative_path)
            db.session.add(new_poster)
            db.session.commit()

        except Exception as e:
            # if file was written but DB failed, remove the file to avoid orphans
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    current_app.logger.exception("Failed to delete uploaded file after DB error.")
            db.session.rollback()
            current_app.logger.exception("Failed to save poster")
            return "Internal Server Error", 500

        return redirect(url_for('views.index'))

    return render_template('create.html')

@views.route("/search", methods=["GET", "POST"])
def search():
    query = request.args.get("q", "").strip()

    if query:
        posters = Poster.query.filter(
            Poster.title.ilike(f"%{query}%") | Poster.owner.ilike(f"%{query}%")
        ).all()

        with open("info.json", "r") as f:
            data = json.load(f)
            json_results = [
                item for item in data
                if query in item.get("title", "").lower() or query in item.get("owner", "").lower()
            ]
    else:
        posters = []
        json_results = []
    
    return render_template(
        "search.html", 
        posters=posters, 
        json_results=json_results,
        query=query
    )
