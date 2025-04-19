import bpy

bl_info = {
    "name": "ToPu_AutoGizmoDisplay",
    "author": "http4211",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "description": "Add-on that automatically displays the appropriate gizmo according to the transform operation.",
}

_last_operator_id = None
_last_gizmo_type = None
_gizmo_toggle_enabled = False


# ------------------------ Preferences ------------------------

class AutoGizmoAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    default_enabled: bpy.props.BoolProperty(
        name="Enable automatic gizmo display at startup",
        description="Whether to enable automatic gizmo display when the add-on is activated",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Initial state when add-on is enabled:", icon='TOOL_SETTINGS')

        row = layout.row(align=True)
        op_on = row.operator("auto_gizmo.set_default", text="ON", depress=self.default_enabled)
        op_on.enable = True

        op_off = row.operator("auto_gizmo.set_default", text="OFF", depress=not self.default_enabled)
        op_off.enable = False



class AUTO_GIZMO_OT_SetDefault(bpy.types.Operator):
    bl_idname = "auto_gizmo.set_default"
    bl_label = "Auto Gizmo Initial state setting"
    bl_description = "Toggles the initial state when the add-on is launched"
    bl_options = {'INTERNAL'}

    enable: bpy.props.BoolProperty()

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        prefs.default_enabled = self.enable
        return {'FINISHED'}


# ------------------------ Core Logic ------------------------

def show_gizmo_by_type(gizmo_type):
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            if not space.show_gizmo:
                continue
            space.show_gizmo_object_translate = (gizmo_type == 'translate')
            space.show_gizmo_object_rotate = (gizmo_type == 'rotate')
            space.show_gizmo_object_scale = (gizmo_type == 'scale')


def check_transform_operator():
    global _last_operator_id, _last_gizmo_type

    if not _gizmo_toggle_enabled:
        return 0.1

    ops = bpy.context.window_manager.operators
    if not ops:
        return 0.1

    last_op = ops[-1]
    op_id = last_op.bl_idname

    if op_id != _last_operator_id:
        _last_operator_id = op_id

        gizmo_type = None
        if op_id == "TRANSFORM_OT_translate":
            gizmo_type = 'translate'
        elif op_id == "TRANSFORM_OT_rotate":
            gizmo_type = 'rotate'
        elif op_id == "TRANSFORM_OT_resize":
            gizmo_type = 'scale'

        if gizmo_type and gizmo_type != _last_gizmo_type:
            _last_gizmo_type = gizmo_type
            show_gizmo_by_type(gizmo_type)

    return 0.1


def _toggle_gizmo_monitor(state):
    global _gizmo_toggle_enabled
    _gizmo_toggle_enabled = state

    if state:
        bpy.app.timers.register(check_transform_operator, persistent=True)
        if _last_gizmo_type:
            show_gizmo_by_type(_last_gizmo_type)
    else:
        try:
            bpy.app.timers.unregister(check_transform_operator)
        except ValueError:
            pass

        for area in bpy.context.window.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.show_gizmo_object_translate = False
                space.show_gizmo_object_rotate = False
                space.show_gizmo_object_scale = False


# ------------------------ UI Panel Integration ------------------------

def draw_gizmo_toggle(self, context):
    layout = self.layout
    layout.separator()
    layout.prop(context.scene, "auto_gizmo_display", toggle=True, icon='GIZMO')


# ------------------------ Register / Unregister ------------------------

def register():
    global _gizmo_toggle_enabled

    bpy.utils.register_class(AutoGizmoAddonPreferences)
    bpy.utils.register_class(AUTO_GIZMO_OT_SetDefault)

    addon_prefs = bpy.context.preferences.addons[__name__].preferences
    default_state = addon_prefs.default_enabled

    bpy.types.Scene.auto_gizmo_display = bpy.props.BoolProperty(
        name="Auto Gizmo",
        description="Automatic gizmo display in response to movement, rotation, and scaling operations",
        default=default_state,
        update=lambda self, ctx: _toggle_gizmo_monitor(ctx.scene.auto_gizmo_display)
    )

    bpy.types.VIEW3D_PT_gizmo_display.append(draw_gizmo_toggle)
    _toggle_gizmo_monitor(default_state)


def unregister():
    global _gizmo_toggle_enabled

    _toggle_gizmo_monitor(False)

    del bpy.types.Scene.auto_gizmo_display
    bpy.types.VIEW3D_PT_gizmo_display.remove(draw_gizmo_toggle)

    bpy.utils.unregister_class(AUTO_GIZMO_OT_SetDefault)
    bpy.utils.unregister_class(AutoGizmoAddonPreferences)


if __name__ == "__main__":
    register()
