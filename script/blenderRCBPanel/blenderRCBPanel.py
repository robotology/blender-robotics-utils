# Copyright (C) 2006-2021 Istituto Italiano di Tecnologia (IIT)
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.

import bpy
import os
# import sys
import yarp
import icub
# import numpy as np
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
                    yarp.delay(0.001)
                # Once finished put the joints in position direct and replay the animation back
                icm.setControlMode(joint, yarp.VOCAB_CM_POSITION_DIRECT)
                bpy.ops.screen.animation_play()
            else:
                iposDir.setPosition(joint,target)


def float_callback(self, context):
    # Callback for sliders. Find each object in the links dictionary and set its rotation.
    try:
        joint_tool = context.scene.my_joints
        pose_bones = bpy.data.objects[bpy.context.scene.my_tool.my_armature].pose.bones
        for joint_name, joint_value in joint_tool.items():
            joint = pose_bones[joint_name]
            # It is a prismatic joint (to be tested)
            if joint.lock_rotation[1]:
                joint.delta_location[1] = joint_value
            # It is a revolute joint
            else:
                joint.rotation_euler[1] = joint_value * math.pi / 180.0
                joint.keyframe_insert(data_path="rotation_euler")

    except AttributeError:
        pass

class AllJoints:

    def __init__(self):
        self.annotations = {}
        self.joint_names = []
        self.generate_joint_classes()

    def generate_joint_classes(self):

        self.joint_names = bpy.data.objects[bpy.context.scene.my_tool.my_armature].pose.bones.keys()

        for joint_name, joint in bpy.data.objects[bpy.context.scene.my_tool.my_armature].pose.bones.items():
            
            # Our bones rotate around y (revolute joint), translate along y (prismatic joint), if both are locked, it
            # means it is a fixed joint.
            if joint.lock_rotation[1] and joint.lock_location[1]:
                continue
            
            joint_min = -360
            joint_max =  360
            
            rot_constraint = None
            for constraint in joint.constraints:
                if constraint.type == "LIMIT_ROTATION":
                    rot_constraint = constraint
                    break
            if rot_constraint is not None:
                joint_min = rot_constraint.min_y * 180 / math.pi
                joint_max = rot_constraint.max_y * 180 / math.pi

            self.annotations[joint_name] = FloatProperty(
                name = joint_name,
                description = joint_name,
                default = 0,
                min = joint_min,
                max = joint_max,
                update = float_callback,
            )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class MyProperties(PropertyGroup):

    my_bool: BoolProperty(
        name="Dry run",
        description="If ticked, the movement will not replayed",
        default=False
        )

    my_int: IntProperty(
        name="Int Value",
        description="A integer property",
        default=23,
        min=10,
        max=100
        )

    my_float: FloatProperty(
        name="Threshold(degrees)",
        description="Threshold for the safety checks",
        default=5.0,
        min=2.0,
        max=15.0
        )

    my_float_vector: FloatVectorProperty(
        name="Float Vector Value",
        description="Something",
        default=(0.0, 0.0, 0.0),
        min=0.0,
        max=0.1
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
        name="Directory",
        description="Choose a directory:",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )

    my_reach_x: FloatProperty(
        name="X",
        description="The target along x axis",
        default=0.0,
        min = -100.0,
        max = 100.0
        )

    my_reach_y: FloatProperty(
        name="Y",
        description="The target along y axis",
        default=0.0,
        min=-100.0,
        max=100.0
        )

    my_reach_z: FloatProperty(
        name="Z",
        description="The target along z axis",
        default=0.0,
        min=-100.0,
        max=100.0
        )

    my_reach_pitch: FloatProperty(
        name="Pitch",
        description="The target around Pitch",
        default=0.0,
        min=-360.0,
        max=360.0
        )

    my_reach_yaw: FloatProperty(
        name="Yaw",
        description="The target around Yaw",
        default=0.0,
        min=-360.0,
        max=360.0
        )

    my_reach_roll: FloatProperty(
        name="Roll",
        description="The target around Roll",
        default=0.0,
        min=-360.0,
        max=360.0
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
        icm = driver.viewIControlMode()
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

        try:
            # init the callback
            bpy.app.handlers.frame_change_post.append(move)
        except:
            print("a problem when initialising the callback")

        robot = AllJoints()

        # Dynamically create the same class
        JointProperties = type(
            # Class name
            "JointProperties",

            # Base class
            (bpy.types.PropertyGroup, ),
                {"__annotations__": robot.annotations},
        )

        # OBJECT_PT_robot_controller.set_joint_names(my_list)
        bpy.utils.register_class(JointProperties)
        bpy.types.Scene.my_joints = PointerProperty(type=JointProperties)

        return {'FINISHED'}


class WM_OT_ReachTarget(bpy.types.Operator):
    bl_label = "Reach Target"
    bl_idname = "wm.reach_target"

    bl_description= "Reach the cartesian target"

    def execute(self, context):
        scene = bpy.context.scene
        mytool = scene.my_tool

        limbArm = icub.iCubArm("right")

        chain = limbArm.asChain()

        q0 = chain.getAng()

        pose_target = yarp.Vector([mytool.my_reach_x,
                                   mytool.my_reach_y,
                                   mytool.my_reach_z,
                                   mytool.my_reach_pitch,
                                   mytool.my_reach_yaw,
                                   mytool.my_reach_roll])

        solver = icub.iKinIpOptMin(chain, icub.IKINCTRL_POSE_FULL, 1e-3, 1e-6, 100)
        solver.setUserScaling(True, 100.0, 100.0, 100.0)
        target_angles = solver.solve(q0, pose_target)

        print(target_angles.toString())

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

    joint_name = []

    # @classmethod
    # def poll(cls, context):
    #     return context.object is not None

    @staticmethod
    def set_joint_names(joint_names):
        OBJECT_PT_robot_controller.joint_names = joint_names

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        parts = scene.my_list
        mytool = scene.my_tool
        rcb_wrapper = bpy.types.Scene.rcb_wrapper

        box_configure = layout.box()
        box_configure.prop(mytool, "my_armature")
        box_configure.operator("wm.configure")

        box = layout.box()
        box.label(text="Selection Tools")
        box.template_list("MY_UL_List", "The_List", scene,
                          "my_list", scene, "list_index")

        box.prop(mytool, "my_string")
        row_connect = box.row(align=True)
        row_connect.operator("wm.connect")
        layout.separator()
        row_disconnect = box.row(align=True)
        row_disconnect.operator("wm.disconnect")
        layout.separator()

        reach_box = layout.box()
        reach_box.label(text="Reach target")

        reach_box.label(text="xyz")
        row_reach_xyz = reach_box.row(align=True)
        row_reach_xyz.prop(mytool, "my_reach_x")
        row_reach_xyz.prop(mytool, "my_reach_y")
        row_reach_xyz.prop(mytool, "my_reach_z")

        reach_box.label(text="pitch yaw roll")
        row_reach_rpy = reach_box.row(align=True)
        row_reach_rpy.prop(mytool, "my_reach_pitch")
        row_reach_rpy.prop(mytool, "my_reach_yaw")
        row_reach_rpy.prop(mytool, "my_reach_roll")
        reach_box.operator("wm.reach_target")

        layout.separator()

        box_joints = layout.box()
        box_joints.label(text="joint angles")

        try:
            scene.my_joints
        except AttributeError:
            pass
        else:
            for joint_name, joint in bpy.data.objects[mytool.my_armature].pose.bones.items():
                # Our bones rotate around y (revolute joint), translate along y (prismatic joint), if both are locked, it
                # means it is a fixed joint.
                if joint.lock_rotation[1] and joint.lock_location[1]:
                    continue
                box_joints.prop(scene.my_joints, joint_name)

        if len(context.scene.my_list) == 0:
            box.enabled = False
            box_configure.enabled = True
            box_joints.enabled = False
        else:
            box.enabled = True
            box_configure.enabled = False
            if bpy.context.screen.is_animation_playing:
                row_disconnect.enabled = False
                row_connect.enabled = False
                box_joints.enabled = False
            else:
                box_joints.enabled = True
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

