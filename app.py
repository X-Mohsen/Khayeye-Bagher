import os
from flask import Flask, render_template, send_file, request
import flask_login
from werkzeug.utils import secure_filename

from utils import network, storage


storage_dir_name, storage_path = storage.init()
ip_addr = network.get_local_ipv4()
port = network.port

app = Flask(__name__)
login_manager = flask_login.LoginManager()
app.secret_key = os.urandom(24)
login_manager.init_app(app)

class User(flask_login.UserMixin):
    pass

users = {'admin': {'password': 'admin'}}


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    email = request.form['email']
    if email in users and request.form['password'] == users[email]['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('upload.html', logged_in = True, ip_addr=ip_addr,port=port, storage_dir_name=storage_dir_name)

    return render_template("login.html", error = "Invalid Data !")


@app.route('/protected')
@flask_login.login_required
def protected():
    return render_template("index_files.html")

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template("upload.html", ip_addr=ip_addr,port=port, message = "Logged out.")

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("unauth.html")


@app.route("/")
@app.route("/up")
def upload_func():
    if flask_login.current_user.is_authenticated == False:
        return render_template("upload.html", ip_addr=ip_addr,port=port)
    else:
        return render_template("upload.html", ip_addr=ip_addr,port=port, logged_in = True, )



@app.route("/uploader", methods = ["GET","POST"])
def uploader():
    if request.method == "POST":

        if 'file' not in request.files:
            return render_template("upload.html", message="No selected file")

        file = request.files["file"]
        
        if file.filename == "":
            return render_template("upload.html", message="No selected file")
        
        if file:
            try:
                print("Started saving file ... ")

                # Use a streaming approach to save the file in chunks
                
                file_path = os.path.join(storage_path, file.filename)
                with open(file_path, "wb") as f:
                    while True:
                        chunk = file.stream.read(1024)  # Read 1KB at a time
                        if not chunk:
                            break
                        f.write(chunk)

                print("File saved successfully.")

            except Exception as e:
                return render_template("upload.html", message=f"Error: {str(e)}")

    return render_template("up_done.html")


@app.route("/<path:req_path>")
@flask_login.login_required
def index_files_func(req_path):
    base_dir = "../"
    abs_path = os.path.join(base_dir, req_path)
    
    print(abs_path)
    if not os.path.exists(abs_path):
        return f"{abs_path}"
    if os.path.isfile(abs_path):
        return send_file(abs_path)

    files = os.listdir(abs_path)
    print(files)
    return render_template("index_files.html", files=files)


if __name__ == "__main__":
    app.run(host=ip_addr, port=port, debug=True)