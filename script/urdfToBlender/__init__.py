# Copyright (C) 2006-2022 Istituto Italiano di Tecnologia (IIT)
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.

bl_info = {
    "name": "URDF to Blender Panel",
    "description": "Panel converting urdf to .blend",
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

from .urdfToBlender import (OBJECT_PT_urdf2blender_converter,
                            WM_OT_OpenFilebrowser)

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    WM_OT_OpenFilebrowser,
    OBJECT_PT_urdf2blender_converter
)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except:
            print("an exception when registering the class")

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            print("An exception was raised when unregistering the class")


if __name__ == "__main__":
    register()
