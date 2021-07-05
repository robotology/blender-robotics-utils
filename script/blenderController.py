# Copyright (C) 2006-2021 Istituto Italiano di Tecnologia (IIT)
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.

import sys
import yarp
import numpy as np
import bpy
import math

def register(driver, icm, iposDir, ipos, ienc):
    bpy.types.Scene.driver = driver
    bpy.types.Scene.icm = icm
    bpy.types.Scene.iposDir = iposDir
    bpy.types.Scene.ipos = ipos
    bpy.types.Scene.ienc = ienc

def unregister():
    try:
        del bpy.types.Scene.driver
        del bpy.types.Scene.icm
        del bpy.types.Scene.iposDir
        del bpy.types.Scene.ipos
        del bpy.types.Scene.ienc
    except: 
        pass        
    
def move(dummy):
    target_roll = math.degrees(bpy.data.objects["iCub"].pose.bones["torso_roll"].rotation_euler[1]) 
    print("Target roll:", target_roll)
    bpy.types.Scene.iposDir.setPosition(1, target_roll);
        
if __name__ == "__main__":
        
    yarp.Network.init()

    unregister()
    
    if not yarp.Network.checkNetwork():
        print ('YARP server is not running!')
        sys.exit()
        
    if hasattr(bpy.types.Scene, "driver"):
        driver = bpy.types.Scene.driver
    else:
        options = yarp.Property()
        driver = yarp.PolyDriver()
       
        # set the poly driver options
        options.put("robot", "icubSim")
        options.put("device", "remote_controlboard")
        options.put("local", "/example_enc/client")
        options.put("remote", "/icubSim/torso")

        # opening the drivers
        print ('Opening the motor driver...')
        driver.open(options)
        
    if not driver.isValid():
        print ('Cannot open the driver!')
        sys.exit()
     
    # opening the drivers
    print ('Viewing motor position/encoders...')
    icm  = driver.viewIControlMode()
    iposDir = driver.viewIPositionDirect()
    ipos = driver.viewIPositionControl()
    ienc = driver.viewIEncoders()
    if ienc is None or ipos is None or icm is None or iposDir is None:
        print ('Cannot view one of the interfaces!')
        sys.exit()
        
    icm.setControlMode(0, yarp.VOCAB_CM_POSITION_DIRECT)
    icm.setControlMode(1, yarp.VOCAB_CM_POSITION_DIRECT)
    icm.setControlMode(2, yarp.VOCAB_CM_POSITION_DIRECT)

    register(driver, icm, iposDir, ipos, ienc)

    bpy.app.handlers.frame_change_post.clear()
    bpy.app.handlers.frame_change_post.append(move)    