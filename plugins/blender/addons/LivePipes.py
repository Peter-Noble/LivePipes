import bpy
import requests
import os

from bpy.app.handlers import persistent

bl_info = {
    "name": "LivePipes",
    "author": "Peter Noble",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "VIEW_3D > ...",
    "description": "Pipeline tool for LiveWires",
    "warning": "",
    "wiki_url": "",
    "category": "System"}


class LivePipesPanel(bpy.types.Panel):
    bl_label = "LivePipes"
    bl_idname = "SCENE_PT_livepipes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LiveWires"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        lp = scene.LivePipes

        row = layout.row()
        row.prop(lp, "server_address")

        row = layout.row()
        row.prop(lp, "file_path")

        row = layout.row()
        if lp.current_user.strip() != "" and lp.current_user != "<Select user>":
            row.label(text="Logged in as: {}".format(lp.current_user))
        else:
            row.label(text="Please select a user")

        row.operator("lp.select_user", text="", icon="DISCLOSURE_TRI_DOWN")

        row = layout.row()
        if lp.current_project.strip() != "" and lp.current_project != "<Select project>":
            row.label(text="Current project: {}".format(lp.current_project))
        else:
            row.label(text="No project open")

        row.operator("lp.select_project", text="", icon="DISCLOSURE_TRI_DOWN")

        row = layout.row()
        row.prop(lp, "new_project_name")

        row = layout.row()
        row.operator("lp.new_project")


temp_user_list = []
temp_project_list = []

def user_list(self, context):
    lp = context.scene.LivePipes
    current = lp.current_user
    current_id = lp.current_user_id
    user_list = [(str(u["id"]),
                  "{} {}".format(u["first_name"], u["surname"]),
                  "") for u in temp_user_list]
    missing = current_id not in [x[0] for x in user_list]
    if current_id != "-1" and missing:
        user_list = [(str(current_id), current, "")] + user_list
    else:
        user_list = [(str(-1), "<Select user>", "")] + user_list

    return user_list

def update_current_user(self, context):
    ul = user_list(self, context)
    lp = context.scene.LivePipes
    context.scene.LivePipes.current_user_id = lp.user_list
    for user in ul:
        if user[0] == lp.user_list:
            lp.current_user = user[1]


def project_list(self, context):
    lp = context.scene.LivePipes
    current = lp.current_project
    current_id = lp.current_project_id
    project_list = [(str(u["id"]),
                    u["name"],
                    "") for u in temp_project_list]
    missing = current_id not in [x[0] for x in project_list]
    if current_id != "-1" and missing:
        project_list = [(str(current_id), current, "")] + project_list
    else:
        project_list = [(str(-1), "<Select project>", "")] + project_list

    return project_list

def update_current_project(self, context):
    pl = project_list(self, context)
    lp = context.scene.LivePipes
    context.scene.LivePipes.current_project_id = lp.project_list
    for project in pl:
        if project[0] == lp.project_list:
            lp.current_project = project[1]
    for proj in temp_project_list:
        if proj["id"] == int(lp.current_project_id):
            to_open = os.path.join(lp.file_path, proj["dir_name"], proj["file_name"])
            bpy.ops.wm.open_mainfile(filepath=to_open)
    # TODO load the new project file
    #    Setting these variables shouldn't be necessary as scene load handler will take care of it.


@persistent
def LivePipes_load_handler(dummy):
    lp = bpy.context.scene.LivePipes
    lp.user_list = lp.current_user_id
    lp.project_list = lp.current_project_id
    # TODO look up project ID with server.
    #    Validate that the rest of the info in the project file path matches
    #    Set current_user, current_user_id, current_project and current_project_id


def select_user_popup(self, context):
    lp = context.scene.LivePipes
    self.layout.prop(lp, "user_list")


class LivePipesSelectUser(bpy.types.Operator):
    bl_idname = "lp.select_user"
    bl_label = "Select user"

    def execute(self, context):
        lp = context.scene.LivePipes

        r = requests.get(url=lp.server_address + "/user_list",
                         params={})
        data = r.json()

        global temp_user_list
        temp_user_list = data

        lp.user_list = str(lp.current_user_id)
        bpy.context.window_manager.popup_menu(select_user_popup, title="Select user", icon='INFO')

        return {"FINISHED"}


def select_project_popup(self, context):
    lp = context.scene.LivePipes
    self.layout.prop(lp, "project_list")


class LivePipesSelectProject(bpy.types.Operator):
    bl_idname = "lp.select_project"
    bl_label = "Select project"

    def execute(self, context):
        lp = context.scene.LivePipes

        r = requests.get(url=lp.server_address + "/project_list",
                         params={"user_id": lp.current_user_id})
        data = r.json()

        global temp_project_list
        temp_project_list = data

        lp.project_list = str(lp.current_project_id)
        bpy.context.window_manager.popup_menu(select_project_popup, title="Select project", icon='INFO')

        return {"FINISHED"}

    @classmethod
    def poll(self, context):
        lp = context.scene.LivePipes
        return lp.current_user.strip() != "" and lp.current_user != "<Select user>"


def save_all_images():
    """Blender doesn't automatically save all the textures that have been painted
    and they will be deleted when the project is saved"""
    for image in bpy.data.images:
        if image.is_dirty:
            if image.filepath == "":
                image.save_render(bpy.path.abspath("//{}.png".format(image.name)))
            else:
                image.save()

def project_location():

    return ""


class LivePipesNewProject(bpy.types.Operator):
    bl_idname = "lp.new_project"
    bl_label = "Create new project"

    def execute(self, context):
        lp = context.scene.LivePipes

        if lp.new_project_name.strip() != "":
            sw_version = "{}.{}".format(bpy.app.version[0], bpy.app.version[1])
            r = requests.post(url=lp.server_address + "/new_project",
                              data={"project_name": lp.new_project_name,
                                      "category": 0, #  0 - Blender,
                                      "sw_version": sw_version,
                                      "user_id": lp.current_user_id
                                      })
            np = r.json()

            abs_path = bpy.path.abspath(lp.file_path)
            if "id" in np:
                proj_name = "{}_{}_{}".format(np["id"], lp.current_user, lp.new_project_name)
                proj_name = proj_name.replace(" ", "_")
                proj_path = os.path.join(abs_path, proj_name)
                if not os.path.isdir(proj_path):
                    os.mkdir(proj_path)

                proj_version = "v001"
                file_name = "{}.{}.blend".format(proj_name, proj_version)
                full_file_path = os.path.join(proj_path, file_name)
                lp.new_project_name = ""

                bpy.ops.wm.save_as_mainfile(filepath=full_file_path)

                save_all_images()

                lp.current_project = np["id"]
                lp.current_project_id = np["name"]

        return {"FINISHED"}


class LivePipesSaveProject(bpy.types.Operator):
    bl_idname = "lp.save_project"
    bl_label = "Save project"

    def execute(self, context):
        lp = context.scene.LivePipes

        save_all_images()
        bpy.ops.wm.save_mainfile()

        return {"FINISHED"}


class LivePipesProperties(bpy.types.PropertyGroup):
    server_address = bpy.props.StringProperty(name="Server address")
    file_path = bpy.props.StringProperty(name="File path", subtype="DIR_PATH")
    current_user = bpy.props.StringProperty(name="Current user", default=" ")
    current_user_id = bpy.props.StringProperty(name="Current user ID", default="-1")
    user_list = bpy.props.EnumProperty(name="Users", items=user_list, update=update_current_user)
    current_project = bpy.props.StringProperty(name="Current project", default=" ")
    current_project_id = bpy.props.StringProperty(name="Current project ID", default="-1")
    project_list = bpy.props.EnumProperty(name="Projects", items=project_list, update=update_current_project)
    new_project_name = bpy.props.StringProperty(name="Project name")


def register():
    bpy.utils.register_class(LivePipesPanel)
    bpy.utils.register_class(LivePipesProperties)
    bpy.utils.register_class(LivePipesNewProject)
    bpy.utils.register_class(LivePipesSelectUser)
    bpy.utils.register_class(LivePipesSelectProject)

    bpy.types.Scene.LivePipes = bpy.props.PointerProperty(type=LivePipesProperties)

    bpy.app.handlers.load_post.append(LivePipes_load_handler)


def unregister():
    bpy.utils.unregister_class(LivePipesPanel)
    bpy.utils.unregister_class(LivePipesProperties)
    bpy.utils.unregister_class(LivePipesNewProject)
    bpy.utils.unregister_class(LivePipesSelectUser)
    bpy.utils.unregister_class(LivePipesSelectProject)

    del bpy.types.Scene.LivePipes

    bpy.app.handlers.load_post.remove(LivePipes_load_handler)


if __name__ == "__main__":
    register()
