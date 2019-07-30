from dbms import create_database, Base
from db_schema import User, Project, ProjectOwner, Version
from flask import Flask, render_template, send_file, request
from flask_socketio import send, emit, SocketIO
import json
import os

db_path = "LivePipes2019.db"
engine, Session = create_database(db_path)

session = Session()
Base.metadata.create_all(engine)

session.commit()
session.close()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html",
                           db_path="LivePipes2019.db")

@app.route("/user_list")
def user_list():
    session = Session()
    user_json = session.query(User).filter_by(is_active=True).all()
    result = [u.to_dict() for u in user_json]
    session.commit()
    session.close()
    return json.dumps(result)

@app.route("/project_list")
def project_list():
    session = Session()
    data = dict(request.args)
    if "user_id" in data:
        q = session.query(Project, User, ProjectOwner).\
                filter(User.id == ProjectOwner.user_id).\
                filter(Project.id == ProjectOwner.project_id).\
                filter(User.id == data["user_id"])
        project_json = q.all()
        result = [u[0].to_dict() for u in project_json]
    else:
        q = session.query(Project)
        project_json = q.all()
        result = [q.to_dict() for u in project_json]
    session.commit()
    session.close()
    return json.dumps(result)

@app.route("/update_project", methods=["POST"])
def update_project():
    return ""

@app.route("/submit_render", methods=["POST"])
def submit_render():
    return ""

@app.route("/get_render_queue")
def submit_render():
    return ""

@app.route("/cancel_render", methods=["POST"])
def cancel_render():
    return ""


def emit_user_list(broadcast=True):
    session = Session()
    user_json = json.dumps([x.to_dict() for x in session.query(User).all()])
    socketio.emit("user list", user_json, broadcast=broadcast)
    session.commit()
    session.close()

@app.route("/new_user", methods=["POST"])
def new_user():
    session = Session()
    data = dict(request.form)
    new_user = User(first_name=data["first_name"],
                    surname=data["surname"],
                    is_yp=data["is_yp"] == "true",
                    is_active=True)
    session.add(new_user)
    session.commit()
    session.close()

    emit_user_list()
    return "User created"

def emit_project_list(broadcast=True):
    session = Session()
    q = session.query(Project, User, ProjectOwner).\
            filter(User.id == ProjectOwner.user_id).\
            filter(Project.id == ProjectOwner.project_id).\
            group_by(Project.id)
    projects = []
    for x in q.all():
        if len(projects) == 0 or x[0].id != projects[-1]["id"]:
            projects.append(x[0].to_dict())
            projects[-1]["users"] = [x[1].to_dict()]
        else:
            projects[-1]["users"].append(x[1].to_dict())

    project_json = json.dumps(projects)
    socketio.emit("project list", project_json, broadcast=broadcast)
    session.commit()
    session.close()

@app.route("/new_project", methods=["POST"])
def new_project():
    session = Session()
    data = dict(request.form)
    new_project = Project(name=data["project_name"],
                          category=data["category"],
                          sw_version=data["sw_version"])
    session.add(new_project)
    session.commit()  # needed so that new_project gets assigned an ID
    new_project_owner = ProjectOwner(user_id=data["user_id"],
                                     project_id=new_project.id)
    session.add(new_project_owner)
    session.commit()
    result = new_project.to_dict()
    new_project_version = Version(project_id=new_project.id,
                                  version_number=1)
    session.add(new_project_owner)
    session.commit()
    session.close()
    emit_project_list()
    return result

@app.route("/new_version", methods=["POST"])
def new_version():
    session = Session()
    data = dict(request.form)
    new_project_version = Version(project_id=data["project_id"],
                                  version_number=data["version_number"],
                                  file_path=data["file_path"])
    session.add(new_project_version)
    session.commit()
    session.close()
    return ""


@app.route("/delete_user", methods=["POST"])
def delete_user():
    session = Session()
    data = dict(request.form)
    selected_user = session.query(User).filter_by(id=data["user_id"]).first()
    session.delete(selected_user)
    session.commit()
    session.close()
    emit_user_list()
    return "User deleted"

socketio = SocketIO(app)

@socketio.on('client_connected')
def handle_client_connect_event(data):
    emit_user_list(broadcast=False)
    emit_project_list(broadcast=False)

if __name__ == '__main__':
    # app.run(debug=True, host="0.0.0.0")
    socketio.run()
    #app.run()
