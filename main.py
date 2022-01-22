import os

from flask import Flask, render_template, url_for, flash, request, redirect, session, current_app, send_from_directory
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from colorize import Colorizer
from sketch import Sketcher

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phomas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    surname = db.Column(db.String(250), nullable=False)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.Text, nullable=False)


class Images(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    img_owner = db.Column(db.String(250), nullable=False)
    img_name = db.Column(db.String(250), nullable=False)
    img_output = db.Column(db.String(250), nullable=False)

# db.create_all()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template("index.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        session['username'] = username
        user = Users.query.filter_by(username=username).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That username does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop("username", None)
    return redirect(url_for('home'))


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        if Users.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = Users(
            name=request.form.get('name'),
            surname=request.form.get('surname'),
            username=request.form.get('username'),
            email=request.form.get('email'),
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        username = request.form.get('username')
        session['username'] = username
        user_folder = os.path.join(f'static/uploaded_imgs/', username)
        if not os.path.exists(user_folder):
            os.mkdir(user_folder)
        user_out_folder = os.path.join(f'static/imgs_out/', username)
        if not os.path.exists(user_out_folder):
            os.mkdir(user_out_folder)
        return redirect(url_for("home"))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/colorize', methods=['GET', 'POST'])
@login_required
def colorizer():
    filename = ""
    current_username = "%s" % session['username']
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('Please select file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            user_folder = os.path.join(f'static/uploaded_imgs/', current_username)
            if not os.path.exists(f'{user_folder}/{filename}'):
                file.save(os.path.join(user_folder, f'{filename}'))
                lets_colorize = Colorizer(username=current_username, filename=filename)
                lets_colorize.colorize()
                new_image = Images(
                    img_owner=current_username,
                    img_name=filename,
                    img_output="colorized"
                )
                original_image = Images(
                    img_owner=current_username,
                    img_name=filename,
                    img_output="original"
                )
                db.session.add(new_image)
                db.session.add(original_image)
                db.session.commit()
            else:
                flash("You already uploaded selected image! If you think you don't then change your image name.")
                return redirect(url_for('profile'))

    return render_template("colorizer.html", username=current_username,
                           filename=filename, logged_in=current_user.is_authenticated)


@app.route('/colorize/<string:filename>', methods=['GET', 'POST'])
@login_required
def colorizer_uploaded(filename):
    current_username = "%s" % session['username']
    user_folder = os.path.join(f'static/uploaded_imgs/', current_username)
    if not os.path.exists(f'{user_folder}/{filename}'):
        lets_colorize = Colorizer(username=current_username, filename=filename)
        lets_colorize.colorize()
        new_image = Images(
            img_owner=current_username,
            img_name=filename,
            img_output="colorized"
        )
        db.session.add(new_image)
        db.session.commit()

        return redirect(url_for('profile'))
    else:
        flash("You already colorized selected image! Please take a look at 'Colorized Images' section.")
        return redirect(url_for('profile'))


@app.route('/sketcher', methods=['GET', 'POST'])
@login_required
def sketcher():
    filename = ""
    current_username = "%s" % session['username']
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('Please select file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            user_folder = os.path.join(f'static/uploaded_imgs/', current_username)
            if not os.path.exists(f'{user_folder}/{filename}'):
                file.save(os.path.join(user_folder, f'{filename}'))
                lets_sketch = Sketcher(username=current_username, filename=filename)
                lets_sketch.sketch()
                new_image = Images(
                    img_owner=current_username,
                    img_name=filename,
                    img_output="sketched"
                )
                original_image = Images(
                    img_owner=current_username,
                    img_name=filename,
                    img_output="original"
                )
                db.session.add(new_image)
                db.session.add(original_image)
                db.session.commit()
            else:
                flash("You already uploaded selected image! If you think you don't then change your image name.")
                return redirect(url_for('profile'))

    return render_template("sketcher.html", username=current_username,
                           filename=filename, logged_in=current_user.is_authenticated)


@app.route('/sketch/<string:filename>', methods=['GET', 'POST'])
@login_required
def sketcher_uploaded(filename):
    current_username = "%s" % session['username']
    user_folder = os.path.join(f'static/uploaded_imgs/', current_username)
    if not os.path.exists(f'{user_folder}/{filename}'):
        lets_sketch = Sketcher(username=current_username, filename=filename)
        lets_sketch.sketch()
        new_image = Images(
            img_owner=current_username,
            img_name=filename,
            img_output="sketched"
        )
        db.session.add(new_image)
        db.session.commit()
        return redirect(url_for('profile'))
    else:
        flash("You already sketched selected image! Please take a look at 'Sketched Images' section.")
        return redirect(url_for('profile'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    images = Images.query.all()
    current_username = "%s" % session['username']
    image_owner_list = []
    colorized_exists = False
    sketched_exists = False

    for image in images:
        image_owner_list.append(image.img_owner)
        if os.path.exists(f'static/imgs_out/{current_username}/colorized_{image.img_name}'):
            colorized_exists = True
        if os.path.exists(f'static/imgs_out/{current_username}/sketched_{image.img_name}'):
            sketched_exists = True
    if current_username in image_owner_list:
        empty_profile = False
    else:
        empty_profile = True

    return render_template("profile.html", images=images, username=current_username,
                           logged_in=current_user.is_authenticated, colorized_exists=colorized_exists,
                           sketched_exists=sketched_exists, empty_profile=empty_profile)


@app.route('/profile/<string:file_type>/<path:filename>', methods=['GET', 'POST'])
@login_required
def open_img(filename, file_type):
    current_username = "%s" % session['username']
    if file_type == "output":
        images = os.path.join(current_app.root_path, f"static/imgs_out/{current_username}")
    elif file_type == "upload":
        images = os.path.join(current_app.root_path, f"static/uploaded_imgs/{current_username}")

    return send_from_directory(directory=images, path=filename)


@app.route('/delete_image/<int:img_id>/<string:img_type>/<string:filename>', methods=['GET', 'POST'])
@login_required
def delete_img(img_id, filename, img_type):
    current_username = "%s" % session['username']
    new_id = img_id
    output_path = f"static/imgs_out/{current_username}/"
    upload_path = f"static/uploaded_imgs/{current_username}/"
    if img_type == "original":
        os.remove(os.path.join(upload_path, filename))
    else:
        os.remove(os.path.join(output_path, f"{img_type}_{filename}"))
    db.session.query(Images).filter_by(id=new_id).delete()
    db.session.commit()
    return redirect(url_for('profile'))


@app.route('/<string:page>', methods=['GET', 'POST'])
@login_manager.unauthorized_handler
def unauthorized_callback(page):
    return render_template(page)


if __name__ == "__main__":
    app.run(debug=True)
