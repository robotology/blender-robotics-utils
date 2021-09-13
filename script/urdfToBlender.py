# Copyright (C) 2006-2021 Istituto Italiano di Tecnologia (IIT)
# All rights reserved.
#
# This software may be modified and distributed under the terms of the
# BSD-3-Clause license. See the accompanying LICENSE file for details.

import bpy, bmesh
import copy
import mathutils
import math
import os
import idyntree.bindings as iDynTree
import xml.etree.ElementTree as ET

from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator


def createGeometricShape(iDynTree_solidshape):
    if iDynTree_solidshape.isSphere():
        bpy.ops.mesh.primitive_uv_sphere_add(radius=iDynTree_solidshape.asSphere().getRadius())
    elif iDynTree_solidshape.isCylinder():
        cylinder = iDynTree_solidshape.asCylinder()
        bpy.ops.mesh.primitive_cylinder_add(radius=cylinder.getRadius(), depth=cylinder.getLength())
    elif iDynTree_solidshape.isBox():
        box = iDynTree_solidshape.asBox()
        if box.getX() != box.getY() or box.getZ() != box.getX() or box.getZ() != box.getY():
            print("WARNING: the box has different dimensions along the three axis but it will be imported as cube with size equal to the X length")
        bpy.ops.mesh.primitive_cube_add(size=box.getX()) # Seems that blender support only cubes
    else:
        print("Geometric shape not supported")
        return False
    return True

def rigify(path):

    armature_name = ""

    # Get robot name needed until https://github.com/robotology/idyntree/issues/908 is not fixed
    root = ET.parse(path).getroot()
    armature_name = root.attrib["name"]
    # Get the urdf and parse it
    dynComp = iDynTree.KinDynComputations();
    mdlLoader = iDynTree.ModelLoader();
    mdlExporter = iDynTree.ModelExporter();
    mdlLoader.loadModelFromFile(path);

    # Produce the reduced urdf
    model = mdlLoader.model()
    traversal = iDynTree.Traversal()
    ok_traversal = model.computeFullTreeTraversal(traversal)
    print(ok_traversal)
    if not ok_traversal:
        print("Failed to compute the traversal!")
        return 0
    linkVisual=model.visualSolidShapes().getLinkSolidShapes();

    dofs = dynComp.model().getNrOfDOFs();
    s = iDynTree.VectorDynSize(dofs);
    ds = iDynTree.VectorDynSize(dofs);
    dds = iDynTree.VectorDynSize(dofs);
    for dof in range(dofs):
        # For the sake of the example, we fill the joints vector with gibberish data (remember in any case
        # that all quantities are expressed in radians-based units
        s.setVal(dof, 0.0);
        ds.setVal(dof, 0.0);
        dds.setVal(dof, 0.3);


    # The gravity acceleration is a 3d acceleration vector.
    gravity = iDynTree.Vector3();
    gravity.zero();
    gravity.setVal(2, -9.81);
    dynComp.setRobotState(s,ds,gravity);

    dynComp.loadRobotModel(mdlLoader.model());
    print("The loaded model has", dynComp.model().getNrOfDOFs(), \
    "internal degrees of freedom and",dynComp.model().getNrOfLinks(),"links.")

    # Remove meshes leftovers
    # Will collect meshes from delete objects
    meshes = set()
    # Delete all the objects in the scene
    # Get objects in the collection if they are meshes
    for obj in bpy.data.objects:
        # Store the internal mesh
        if obj.type == 'MESH':
            meshes.add( obj.data )
        # Delete the object
        bpy.data.objects.remove( obj )
    # Look at meshes that are orphean after objects removal
    for mesh in [m for m in meshes if m.users == 0]:
        # Delete the meshes
        bpy.data.meshes.remove( mesh )

    # Check if there are still orphean meshes
    # It may happens when you delete the object from UI
    for mesh in bpy.data.meshes:
       if mesh.name not in  bpy.data.objects.keys():
           bpy.data.meshes.remove( mesh )

    # Import the meshes
    meshMap = {}
    meshesInfo = {}

    # import meshes and do the mapping to the link
    for link_id in range(model.getNrOfLinks()):
        if len(linkVisual[link_id]) == 0:
            continue
        meshesInfo[model.getLinkName(link_id)] = linkVisual[link_id][0]
        linkname = model.getLinkName(link_id)
        if meshesInfo[model.getLinkName(link_id)].isExternalMesh():
            # import the mesh
            filePath = meshesInfo[model.getLinkName(link_id)].asExternalMesh().getFileLocationOnLocalFileSystem()
            if ".stl" in filePath:
                bpy.ops.import_mesh.stl(filepath=os.path.join(filePath),global_scale=0.001)
            elif ".ply" in filePath:
                bpy.ops.import_mesh.ply(filepath=os.path.join(filePath),global_scale=0.001)
            elif ".dae" in filePath:
                bpy.ops.wm.collada_import(filepath=os.path.join(filePath), import_units=True) #TODO check how to handle scale here !
        else:
            # it is a basic geometry(sphere, cylinder, box)
            if not createGeometricShape(meshesInfo[model.getLinkName(link_id)]):
                continue
        meshName = ""
        # We are assuming we are starting in a clean environment
        if not meshMap.keys() :
            meshName = bpy.data.objects.keys()[0]
        else:
            for mesh in bpy.data.objects:
                if mesh.name not in meshMap.values():
                    meshName = mesh.name
                    break
        meshMap[linkname] = meshName

    # Place the meshes
    for link_id in range(model.getNrOfLinks()):
        linkname = model.getLinkName(link_id)
        if linkname not in meshMap.keys():
            continue
        meshname = meshMap[linkname]
        meshobj = bpy.data.objects[meshname]
        # root->link transform
        RtoLinktransform = dynComp.getRelativeTransform("root_link", linkname)
        # link->geometry transform
        LinkToGtransform = meshesInfo[linkname].getLink_H_geometry()
        # root->geometry transform
        RToGtransform = RtoLinktransform * LinkToGtransform

        meshobj.location = RToGtransform.getPosition().toNumPy()
        meshobj.rotation_mode = "QUATERNION"
        meshobj.rotation_quaternion = RToGtransform.getRotation().asQuaternion()

    # Define the armature
    # Create armature and armature object
    try:
        armature_object = bpy.data.objects[armature_name]
    except KeyError:
    # create armature
        armature = bpy.data.armatures.new(armature_name)
        armature_object = bpy.data.objects.new(armature_name, armature)
        # Link armature object to our scene
        bpy.context.scene.collection.objects.link(armature_object)

    #Make a coding shortcut
    armature_data = bpy.data.objects[armature_name]
    # must be in edit mode to add bones
    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature_data.data.edit_bones
    pose_bones = armature_data.pose.bones

    limits = {}
    bone_list = {}
    # Loop for defining the hierarchy of the bonse and its locations
    for idyn_joint_idx in range(model.getNrOfJoints()):
        parentIdx = traversal.getParentLinkIndexFromJointIndex(model,
                                                               idyn_joint_idx)
        childIdx = traversal.getChildLinkIndexFromJointIndex(model,
                                                              idyn_joint_idx)
        parentname = model.getLinkName(parentIdx)
        childname = model.getLinkName(childIdx)
        joint = model.getJoint(idyn_joint_idx)
        jointtype = ""
        if joint.isRevoluteJoint():
            joint = joint.asRevoluteJoint()
            jointtype = "REVOLUTE"
            direction =	joint.getAxis(childIdx,parentIdx).getDirection().toNumPy()
        # This is missing from idyntree api :(
        #elif joint.isPrismaticJoint():
        #    joint = joint.asPrismaticJoint()
        #    jointtype = "PRISMATIC"
        elif joint.isFixedJoint():
            joint = joint.asFixedJoint()
            jointtype = "FIXED"
        #else:
        #    joint = joint.asRevoluteJoint()
        #    jointtype = "REVOLUTE"
        #    direction =	joint.getAxis(childIdx,parentIdx).getDirection().toNumPy()
        min = joint.getMinPosLimit(0)
        max = joint.getMaxPosLimit(0)
        bparent = None
        if parentname in bone_list.keys():
            bparent = bone_list[parentname]
        else:
            if parentname != "root_link":
                for i in range(model.getNrOfJoints()):
                    childname_prev = model.getLinkName(traversal.getChildLinkIndexFromJointIndex(model,
                                                                         i))
                    if childname_prev == parentname:
                        bonename = model.getJointName(i)
                        if bonename not in edit_bones.keys():
                            bparent = edit_bones.new(bonename)
                        else:
                            bparent = edit_bones[bonename]
                        break
            else:
                bparent = edit_bones.new(parentname)
            # TODO I have to put random value for head and tail bones otherwise bones with 0 lenght are removed
            bparent.head = (0,0,0)
            bparent.tail = (0,0,-0.01)
            bone_list[parentname] = bparent

        bonename = model.getJointName(idyn_joint_idx)
        if bonename not in edit_bones.keys():
            bchild = edit_bones.new(bonename)
        else:
            bchild = edit_bones[bonename]

        if bparent:
            bchild.parent = bparent

        parent_link_transform = dynComp.getRelativeTransform("root_link", parentname)
        parent_link_position  = parent_link_transform.getPosition().toNumPy();
        child_link_transform  = dynComp.getRelativeTransform("root_link", childname)
        child_link_position   = child_link_transform.getPosition().toNumPy();
        child_link_rotation   = mathutils.Matrix(child_link_transform.getRotation().toNumPy());
        # Start defining the bone like parent->child link
        bchild.head = parent_link_position
        bchild.tail = child_link_position
        if jointtype == "REVOLUTE":
            length = bchild.length
            if length == 0.0:
                length = 0.01 # bones with zero length are deleted by Blender
            direction = mathutils.Vector(direction).normalized()
            direction.rotate(child_link_rotation)
            # In our representation the revolute joint is a bone placed in the child origin
            # oriented towards the axis of the joint.
            bchild.head = child_link_position
            bchild.tail = bchild.head + direction * length

        bone_list[childname] = bchild
        # Consider the y-axis orientation in the limits
        limits[model.getJointName(idyn_joint_idx)] = [min, max, jointtype]

    # exit edit mode to save bones so they can be used in pose mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # just for checking that the map link->mesh is ok.
    #for k,v in meshMap.items():
    #    print(k,v)

    # Now iterate over all the joints(bones) and link them to the meshes.
    for idyn_joint_idx in range(model.getNrOfJoints()):
        # The joint should move the child link(?)
        childIdx = traversal.getChildLinkIndexFromJointIndex(model,
                                                              idyn_joint_idx)
        childname = model.getLinkName(childIdx)
        if childname not in meshMap.keys():
            continue
        jointname = model.getJointName(idyn_joint_idx)
        meshname = meshMap[childname]
        meshobj = bpy.data.objects[meshname]

        bpy.ops.object.select_all(action='DESELECT')
        armature_data.select_set(True)
        bpy.context.view_layer.objects.active = armature_data

        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones.active = edit_bones[jointname]

        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT') #deselect all objects
        meshobj.select_set(True)
        armature_data.select_set(True)
        bpy.context.view_layer.objects.active = armature_data     #the active object will be the parent of all selected object

        bpy.ops.object.parent_set(type='BONE', keep_transform=True)

    # configure the bones limits
    bpy.ops.object.mode_set(mode='POSE')
    for pbone in pose_bones:
        bone_name = pbone.basename
        pbone.lock_location = (True, True, True)
        pbone.lock_rotation = (True, True, True)
        pbone.lock_scale = (True, True, True)
        # root_link is a special case, it is a bone that has not correspondences to the joints
        if bone_name == "root_link":
            continue
        lim = limits[bone_name]
        # check the nr of DOFs
        if lim[2] == "FIXED" :
            continue

        c = pbone.constraints.new('LIMIT_ROTATION')
        c.owner_space = 'LOCAL'

        if lim[2] == "REVOLUTE":
            # The bones should rotate around y-axis
            pbone.lock_rotation[1] = False
        elif lim[2] == "PRISMATIC":
            # The bones should move along y-axis
            pbone.lock_location[1] = False
        if lim:
            c.use_limit_y = True
            # TODO maybe we have to put also the ik constraints ???
            #print(bone_name, math.degrees(lim[0]), math.degrees(lim[1]))
            c.min_y = lim[0] # min
            c.max_y = lim[1] # max

        # TODO not sure if it is the right rotation_mode
        pbone.rotation_mode = 'XYZ'

    bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'


class OT_TestOpenFilebrowser(Operator, ImportHelper):

    bl_idname = "test.open_filebrowser"
    bl_label = "Select the urdf"

    filter_glob: StringProperty(
        default='*.urdf',
        options={'HIDDEN'}
    )

    def execute(self, context):
        """Do something with the selected file(s)."""

        filename, extension = os.path.splitext(self.filepath)

        print('Selected file:', self.filepath)
        print('File name:', filename)
        print('File extension:', extension)
        rigify(self.filepath)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(OT_TestOpenFilebrowser)

def unregister():
    bpy.utils.unregister_class(OT_TestOpenFilebrowser)

# Main function
def main():
    register()
    bpy.ops.test.open_filebrowser('INVOKE_DEFAULT')



# Execute main()
if __name__=='__main__':
    main()
