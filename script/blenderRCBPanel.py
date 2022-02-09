# Copyright (C) 2006-2021 Istituto Italiano di Tecnologia (IIT)
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.

bl_info = {
    "name": "Robotics Utils",
    "description": "",
    "author": "Nicogene",
    "version": (0, 0, 1),
    "blender": (2, 93, 3),
    "location": "3D View > Tools",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}


import bpy
import os
import sys
import yarp
import numpy as np
import math
import json
from bpy_extras.io_utils import ImportHelper

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       UIList
                       )

# ------------------------------------------------------------------------
#    Structures
# ------------------------------------------------------------------------

class rcb_wrapper():
    def __init__(self, driver, icm, iposDir, ipos, ienc, encs, iax, joint_limits):
        self.driver = driver
        self.icm = icm
        self.iposDir = iposDir
        self.ipos = ipos
        self.ienc = ienc
        self.encs = encs
        self.iax = iax
        self.joint_limits = joint_limits


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
    threshold = 10.0 # degrees
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
        joint_limits     = rcb_instance.joint_limits
        # Get the targets from the rig
        ok_enc = ienc.getEncoders(encs.data())
        if not ok_enc:
            print("I cannot read the encoders, skipping")
            return
        for joint in range(0, ipos.getAxes()):
            # TODO handle the name of the armature, just keep iCub for now
            joint_name = iax.getAxisName(joint)
            if joint_name not in bpy.data.objects[mytool.my_armature].pose.bones.keys():
                continue

            target = math.degrees(bpy.data.objects[mytool.my_armature].pose.bones[joint_name].rotation_euler[1])
            min    = joint_limits[joint][0]
            max    = joint_limits[joint][1]
            if target < min or target > max:
                print("The target", target, "it is outside the boundaries (", min, ",", max, "), skipping.")
                continue

            safety_check=None
            # The icub hands encoders are not reliable for the safety check.
            if mytool.my_armature == "iCub" and joint > 5 :
                safety_check = False
            else:
                safety_check = (abs(encs[joint] - target) > threshold)

            if safety_check:
                print("The target is too far, reaching in position control, for joint", joint_name, "by ", abs(encs[joint] - target), " degrees" )

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

class ListItem(PropertyGroup):
    value: StringProperty(
           name="Name",
           description="A name for this item",
           default="Untitled")

    viewValue: StringProperty(
           name="Displayed Name",
           description="",
           default="")
    
    isConnected: BoolProperty(
        name="",
        default = False
    )

class MY_UL_List(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        if (item.isConnected):
            custom_icon = 'LINKED' 
        else: 
            custom_icon = 'UNLINKED'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.viewValue, icon = custom_icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.viewValue, icon = custom_icon)

class WM_OT_Disconnect(bpy.types.Operator):
    bl_label = "Disconnect"
    bl_idname = "wm.disconnect"
    bl_description= "disconnect the selected part(s)"

    def execute(self, context):
        scene = bpy.context.scene
        parts = scene.my_list
        rcb_instance = bpy.types.Scene.rcb_wrapper[getattr(parts[scene.list_index], "value")]

        if rcb_instance is None:
            return {'CANCELLED'}
        rcb_instance.driver.close()

        del bpy.types.Scene.rcb_wrapper[getattr(parts[scene.list_index], "value")]
        
        setattr(parts[scene.list_index], "isConnected", False)

        return {'FINISHED'}

class WM_OT_Connect(bpy.types.Operator):
    bl_label = "Connect"
    bl_idname = "wm.connect"
    bl_description= "connect the selected part(s)"

    def execute(self, context):
        scene = bpy.context.scene
        parts = scene.my_list
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
        options.put("local", "/blender_controller/client/"+getattr(parts[scene.list_index], "value"))
        options.put("remote", "/"+mytool.my_string+"/"+getattr(parts[scene.list_index], "value"))

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
        ilim = driver.viewIControlLimits()
        if ienc is None or ipos is None or icm is None or iposDir is None or iax is None or ilim is None:
            print ('Cannot view one of the interfaces!')
            return {'CANCELLED'}

        encs = yarp.Vector(ipos.getAxes())
        joint_limits = []

        for joint in range(0, ipos.getAxes()):
            min = yarp.Vector(1)
            max = yarp.Vector(1)
            icm.setControlMode(joint, yarp.VOCAB_CM_POSITION_DIRECT)
            ilim.getLimits(joint, min.data(), max.data())
            joint_limits.append([min.get(0), max.get(0)])

        register_rcb(rcb_wrapper(driver, icm, iposDir, ipos, ienc, encs, iax, joint_limits), getattr(parts[scene.list_index], "value"))
        
        setattr(parts[scene.list_index], "isConnected", True)
        
        # TODO check if we need this
        #bpy.app.handlers.frame_change_post.clear()
        #bpy.app.handlers.frame_change_post.append(move)

        return {'FINISHED'}

class WM_OT_Configure(bpy.types.Operator):
    bl_label = "Configure"
    bl_idname = "wm.configure"
    bl_description= "configure the parts by uploading a configuration file (.json format)"

    def execute(self, context):
        scene = bpy.context.scene
        mytool = scene.my_tool

        bpy.ops.rcb_panel.open_filebrowser('INVOKE_DEFAULT')

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
    row_connect = None
    row_disconnect = None
    row_configure = None

    # @classmethod
    # def poll(cls, context):
    #     return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        parts = scene.my_list
        mytool = scene.my_tool
        rcb_wrapper = bpy.types.Scene.rcb_wrapper
        row_configure = layout.row(align=True)
        row_configure.operator("wm.configure")
        box = layout.box()
        box.label(text="Selection Tools")
        box.template_list("MY_UL_List", "The_List", scene,
                          "my_list", scene, "list_index")

        box.prop(mytool, "my_armature")
        box.prop(mytool, "my_string")
        row_connect = box.row(align=True)
        row_connect.operator("wm.connect")
        layout.separator()
        row_disconnect = box.row(align=True)
        row_disconnect.operator("wm.disconnect")
        layout.separator()

        if len(context.scene.my_list) == 0:
            box.enabled = False
        else:
            box.enabled = True
            if bpy.context.screen.is_animation_playing:
                row_disconnect.enabled = False
                row_connect.enabled = False
            else:
                if getattr(parts[scene.list_index], "value") in rcb_wrapper.keys():
                    row_disconnect.enabled = True
                    row_connect.enabled = False
                else:
                    row_disconnect.enabled = False
                    row_connect.enabled = True


class OT_OpenConfigurationFile(Operator, ImportHelper):

    bl_idname = "rcb_panel.open_filebrowser"
    bl_label = "Select the configuration file"

    filter_glob: StringProperty(
        default='*.json',
        options={'HIDDEN'}
    )

    def parse_conf(self, filepath, context):
        f = open(filepath)
        data = json.load(f)
        context.scene.my_list.clear()

        for p in data['parts']:
            item = context.scene.my_list.add()
            item.value = p[0]
            item.viewValue = p[1]  

    def execute(self, context):
        filename, extension = os.path.splitext(self.filepath)
        self.parse_conf(self.filepath, context)
        return {'FINISHED'}
    
# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    WM_OT_Disconnect,
    WM_OT_Connect,
    WM_OT_Configure,
    OBJECT_PT_robot_controller,
    OT_OpenConfigurationFile,
    ListItem,
    MY_UL_List
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)
    bpy.types.Scene.my_list = CollectionProperty(type=ListItem)
    bpy.types.Scene.list_index = IntProperty(name="Index for my_list",
                                             default=0)

    # initialize the dict
    bpy.types.Scene.rcb_wrapper = {}

    # init the callback
    bpy.app.handlers.frame_change_post.append(move)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            print("An exception was raised when unregistering the class")
    try:
        del bpy.types.Scene.my_tool
        del bpy.types.Scene.my_list
        del bpy.types.Scene.list_index
    except:
        print("Exception raised when deleting the scene.")

    try:
        # remove the callback
        bpy.app.handlers.frame_change_post.clear()
    except:
        print("Exception raised when removing the callback")


if __name__ == "__main__":
    register()