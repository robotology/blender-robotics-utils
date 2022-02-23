# Copyright (C) 2006-2022 Istituto Italiano di Tecnologia (IIT)
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.


import bpy
from  distutils import dir_util
import os

addon_path = bpy.utils.user_resource('SCRIPTS', path="addons", create=True)
print("Installing blender addons in", addon_path)
addon_urdfToBlender = os.path.join(addon_path, 'urdfToBlender')
addon_blenderRCBPanel = os.path.join(addon_path, 'blenderRCBPanel')

origin_path_urdfToBlender = os.path.abspath('urdfToBlender/')
origin_path_blenderRCBPanel = os.path.abspath('blenderRCBPanel/')

dir_util.copy_tree(origin_path_urdfToBlender, addon_urdfToBlender)
dir_util.copy_tree(origin_path_blenderRCBPanel, addon_blenderRCBPanel)

bpy.ops.preferences.addon_enable(module='urdfToBlender')
bpy.ops.preferences.addon_enable(module='blenderRCBPanel')
bpy.ops.wm.save_userpref()