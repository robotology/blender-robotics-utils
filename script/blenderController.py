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

def register(driver, icm, iposDir, ipos, ienc, encs):
    bpy.types.Scene.driver = driver
    bpy.types.Scene.icm = icm
    bpy.types.Scene.iposDir = iposDir
    bpy.types.Scene.ipos = ipos
    bpy.types.Scene.ienc = ienc
    bpy.types.Scene.encs = encs

def unregister():
    try:
        del bpy.types.Scene.driver
        del bpy.types.Scene.icm
        del bpy.types.Scene.iposDir
        del bpy.types.Scene.ipos
        del bpy.types.Scene.ienc
        del bpy.types.Scene.encs
    except:
        pass

def move(dummy):
    threshold = 5.0 # degrees
    # Get the handles
    icm     = bpy.types.Scene.icm
    iposDir = bpy.types.Scene.iposDir
    ipos    = bpy.types.Scene.ipos
    ienc    = bpy.types.Scene.ienc
    encs    = bpy.types.Scene.iposDir.encs
    # Get the targets from the rig
    target_pitch = math.degrees(bpy.data.objects["iCub"].pose.bones["neck_pitch"].rotation_euler[1])
    target_roll  = math.degrees(bpy.data.objects["iCub"].pose.bones["neck_roll"].rotation_euler[1])
    target_yaw   = math.degrees(bpy.data.objects["iCub"].pose.bones["neck_yaw"].rotation_euler[1])
    # Read the current state of the robot
    ok_enc = ienc.getEncoders(encs.data())
    if not ok_enc:
        print("I cannot read the encoders, skipping")
        return
    if abs(encs[0] - target_pitch) > threshold or abs(encs[1] - target_roll) > threshold or abs(encs[2] - target_yaw) > threshold:
        print("The target is too far, reaching in position control")
        # Pause the animation
        bpy.ops.screen.animation_cancel(True) # We have to check if it is ok
        # Switch to position control and move to the target
        icm.setControlModes([yarp.VOCAB_CM_POSITION, yarp.VOCAB_CM_POSITION, yarp.VOCAB_CM_POSITION])
        ipos.setRefSpeeds([10, 10, 10])
        ipos.positionMove([target_pitch, target_roll, target_yaw])
        done = False
        # Await that the movement is finished
        ipos.checkMotionDone(done)
        while not done:
            ipos.checkMotionDone(done)
            yarp.delay(0.001);
        # Once finished put the joints in position direct and replay the animation back
        icm.setControlModes([yarp.VOCAB_CM_POSITION_DIRECT, yarp.VOCAB_CM_POSITION_DIRECT, yarp.VOCAB_CM_POSITION_DIRECT])
        bpy.ops.screen.animation_play()
    else:
        iposDir.setPositions([target_pitch, target_roll, target_yaw]);

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
        options.put("remote", "/icubSim/head")

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

    encs = yarp.Vector(ipos.getAxes())
    icm.setControlModes([yarp.VOCAB_CM_POSITION_DIRECT, yarp.VOCAB_CM_POSITION_DIRECT, yarp.VOCAB_CM_POSITION_DIRECT])

    register(driver, icm, iposDir, ipos, ienc, encs)

    bpy.app.handlers.frame_change_post.clear()
    bpy.app.handlers.frame_change_post.append(move)