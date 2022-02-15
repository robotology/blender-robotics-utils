# Copyright (C) 2006-2022 Istituto Italiano di Tecnologia (IIT)
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.

bl_info = {
    "name": "RemoteControlBoard Panel",
    "description": "Panel for attaching the remote_controlboard of a YARP-based robot",
    "author": "Nicogene",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "3D View > Tools",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty
                       )

from .blenderRCBPanel import (MyProperties,
                              WM_OT_Disconnect,
                              WM_OT_Connect,
                              WM_OT_Configure,
                              OBJECT_PT_robot_controller,
                              OT_OpenConfigurationFile,
                              ListItem,
                              MY_UL_List,
                              )

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
        try:
            bpy.utils.register_class(cls)
        except:
            print("an exception when registering the class")

    try:
        bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)
        bpy.types.Scene.my_list = CollectionProperty(type=ListItem)
        bpy.types.Scene.list_index = IntProperty(name="Index for my_list",
                                                 default=0)
    except:
        print("A problem in the registration occurred")


    # initialize the dict
    bpy.types.Scene.rcb_wrapper = {}

    try:
        # init the callback
        bpy.app.handlers.frame_change_post.append(move)
    except:
        print("a problem when initialising the callback")

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
