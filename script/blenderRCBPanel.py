bl_info = {
    "name": "Add-on Template",
    "description": "",
    "author": "p2or",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "3D View > Tools",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}


import bpy

import sys
import yarp
import numpy as np
import math

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class MyProperties(PropertyGroup):

    my_bool: BoolProperty(
        name="Dry run",
        description="If ticked, the movement will not replayed",
        default = False
        )

    my_int: IntProperty(
        name = "Int Value",
        description="A integer property",
        default = 23,
        min = 10,
        max = 100
        )

    my_float: FloatProperty(
        name = "Threshold(degrees)",
        description = "Threshold for the safety checks",
        default = 5.0,
        min = 2.0,
        max = 15.0
        )

    my_float_vector: FloatVectorProperty(
        name = "Float Vector Value",
        description="Something",
        default=(0.0, 0.0, 0.0),
        min= 0.0, # float
        max = 0.1
    )

    my_string: StringProperty(
        name="Robot",
        description=":",
        default="icub",
        maxlen=1024,
        )

    my_path: StringProperty(
        name = "Directory",
        description="Choose a directory:",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )

    my_enum: EnumProperty(
        name="Dropdown:",
        description="Parts:",
        items=[ ('head', "Head", ""),
                ('left_arm', "Left arm", ""),
                ('right_arm', "Right arm", ""),
                ('torso', "Torso", ""),
                ('left_leg', "Left leg", ""),
                ('right_leg', "Right leg", ""),
               ]
        )

# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------
def register_rcb(driver, icm, iposDir, ipos, ienc, encs, iax):
    bpy.types.Scene.driver = driver
    bpy.types.Scene.icm = icm
    bpy.types.Scene.iposDir = iposDir
    bpy.types.Scene.ipos = ipos
    bpy.types.Scene.ienc = ienc
    bpy.types.Scene.encs = encs
    bpy.types.Scene.iax = iax

def unregister_rcb():
    try:
        del bpy.types.Scene.driver
        del bpy.types.Scene.icm
        del bpy.types.Scene.iposDir
        del bpy.types.Scene.ipos
        del bpy.types.Scene.ienc
        del bpy.types.Scene.encs
        del bpy.types.Scene.iax
    except:
        pass

def move(dummy):
    threshold = 5.0 # degrees
    # Get the handles
    icm     = bpy.types.Scene.icm
    iposDir = bpy.types.Scene.iposDir
    ipos    = bpy.types.Scene.ipos
    ienc    = bpy.types.Scene.ienc
    encs    = bpy.types.Scene.encs
    iax     = bpy.types.Scene.iax
    # Get the targets from the rig
    ok_enc = ienc.getEncoders(encs.data())
    if not ok_enc:
        print("I cannot read the encoders, skipping")
        return
    for joint in range(0, ipos.getAxes()):
        # TODO handle the name of the armature, just keep iCub for now
        target = math.degrees(bpy.data.objects["iCub"].pose.bones[iax.getAxisName(joint)].rotation_euler[1])

    if abs(encs[joint] - target) > threshold:
        print("The target is too far, reaching in position control")
        # Pause the animation
        bpy.ops.screen.animation_play() # We have to check if it is ok
        # Switch to position control and move to the target
        # TODO try to find a way to use the s methods
        icm.setControlMode(joint, yarp.VOCAB_CM_POSITION)
        ipos.setRefSpeed(joint,10)
        ipos.positionMove(joint,target)
        done = ipos.isMotionDone(joint)
        while not done:
            done = ipos.isMotionDone(joint)
            yarp.delay(0.001);
        # Once finished put the joints in position direct and replay the animation back
        icm.setControlMode(joint, yarp.VOCAB_CM_POSITION_DIRECT)
        bpy.ops.screen.animation_play()
    else:
        iposDir.setPosition(joint,target)

class WM_OT_Connect(Operator):
    bl_label = "Connect"
    bl_idname = "wm.connect"

    def execute(self, context):
        yarp.Network.init()
        if not yarp.Network.checkNetwork():
            print ('YARP server is not running!')
            return {'CANCELLED'}

        if hasattr(bpy.types.Scene, "driver"):
            driver = bpy.types.Scene.driver
        else:
            options = yarp.Property()
            driver = yarp.PolyDriver()

            # set the poly driver options
            options.put("robot", mytool.my_string)
            options.put("device", "remote_controlboard")
            options.put("local", "/blender_controller/client/"+mytool.my_enum)
            options.put("remote", "/"+mytool.my_string+"/"+mytool.my_enum)

            # opening the drivers
            print ('Opening the motor driver...')
            driver.open(options)

        if not driver.isValid():
            print ('Cannot open the driver!')
            return {'CANCELLED'}

        # opening the drivers
        print ('Viewing motor position/encoders...')
        icm  = driver.viewIControlMode()
        iposDir = driver.viewIPositionDirect()
        ipos = driver.viewIPositionControl()
        ienc = driver.viewIEncoders()
        iax = driver.viewIAxisInfo()
        if ienc is None or ipos is None or icm is None or iposDir is None or iax is None:
            print ('Cannot view one of the interfaces!')
        return {'CANCELLED'}

        encs = yarp.Vector(ipos.getAxes())
        for joint in range(0, ipos.getAxes()):
            icm.setControlMode(joint, yarp.VOCAB_CM_POSITION_DIRECT)

        register_rcb(driver, icm, iposDir, ipos, ienc, encs, iax)

        # TODO check if we need this
        #bpy.app.handlers.frame_change_post.clear()
        bpy.app.handlers.frame_change_post.append(move)

        return {'FINISHED'}

# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------

class OBJECT_PT_robot_controller(Panel):
    bl_label = "Robot controller"
    bl_idname = "OBJECT_PT_robot_controller"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tools"
    bl_context = "objectmode"


    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        #layout.prop(mytool, "my_bool")
        layout.prop(mytool, "my_float")
        layout.prop(mytool, "my_enum", text="")
        layout.prop(mytool, "my_string")
        layout.operator("wm.connect")
        layout.separator()

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    WM_OT_Connect,
    OBJECT_PT_robot_controller
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()