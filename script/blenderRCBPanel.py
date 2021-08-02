# Copyright (C) 2006-2021 Istituto Italiano di Tecnologia (IIT)
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.

bl_info = {
    "name": "Add-on Template",
    "description": "",
    "author": "Nicogene",
    "version": (0, 0, 1),
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
#    Structures
# ------------------------------------------------------------------------

class rcb_wrapper():
    def __init__(self, driver, icm, iposDir, ipos, ienc, encs, iax):
        self.driver = driver
        self.icm = icm
        self.iposDir = iposDir
        self.ipos = ipos
        self.ienc = ienc
        self.encs = encs
        self.iax = iax


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------
def register_rcb(rcb_instance, rcb_name):
    scene = bpy.types.Scene
    scene.rcb_wrapper[rcb_name] = rcb_instance


def unregister_rcb(rcb_name):
    try:
        del bpy.types.Scene.rcb_wrapper[rcb_name]
    except:
        pass

def move(dummy):
    threshold = 5.0 # degrees
    scene   = bpy.types.Scene
    mytool = bpy.context.scene.my_tool
    for key in scene.rcb_wrapper:
        rcb_instance = scene.rcb_wrapper[key]
        # Get the handles
        icm     = rcb_instance.icm
        iposDir = rcb_instance.iposDir
        ipos    = rcb_instance.ipos
        ienc    = rcb_instance.ienc
        encs    = rcb_instance.encs
        iax     = rcb_instance.iax
        # Get the targets from the rig
        ok_enc = ienc.getEncoders(encs.data())
        if not ok_enc:
            print("I cannot read the encoders, skipping")
            return
        for joint in range(0, ipos.getAxes()):
            # TODO handle the name of the armature, just keep iCub for now
            target = math.degrees(bpy.data.objects[mytool.my_armature].pose.bones[iax.getAxisName(joint)].rotation_euler[1])
        
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
        
    my_armature: StringProperty(
        name="Armature name",
        description=":",
        default="iCub",
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

class WM_OT_Disconnect(bpy.types.Operator):
    bl_label = "Disconnect"
    bl_idname = "wm.disconnect"

    def execute(self, context):
        scene = bpy.context.scene
        mytool = scene.my_tool

        rcb_instance = bpy.types.Scene.rcb_wrapper[mytool.my_enum]
        
        if rcb_instance is None:
            return {'CANCELLED'}
        rcb_instance.driver.close()

        del bpy.types.Scene.rcb_wrapper[mytool.my_enum]
        
        
        return {'FINISHED'}

class WM_OT_Connect(bpy.types.Operator):
    bl_label = "Connect"
    bl_idname = "wm.connect"

    def execute(self, context):
        scene = bpy.context.scene
        mytool = scene.my_tool
        yarp.Network.init()
        if not yarp.Network.checkNetwork():
            print ('YARP server is not running!')
            return {'CANCELLED'}

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

        
        register_rcb(rcb_wrapper(driver, icm, iposDir, ipos, ienc, encs, iax), mytool.my_enum)

        # TODO check if we need this
        #bpy.app.handlers.frame_change_post.clear()
        #bpy.app.handlers.frame_change_post.append(move)

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
    bl_context = "posemode"


    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        #layout.prop(mytool, "my_bool")
        layout.prop(mytool, "my_enum", text="")
        layout.prop(mytool, "my_armature") 
        layout.prop(mytool, "my_string")
        layout.operator("wm.connect")
        layout.separator()
        layout.operator("wm.disconnect")
        layout.separator()

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    WM_OT_Disconnect,
    WM_OT_Connect,
    OBJECT_PT_robot_controller
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

    # initialize the dict
    bpy.types.Scene.rcb_wrapper = {}

    # init the callback
    bpy.app.handlers.frame_change_post.append(move)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool

    # remove the callback
    bpy.app.handlers.frame_change_post.clear()


if __name__ == "__main__":
    register()