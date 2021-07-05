import bpy, bmesh
import copy
import mathutils
import math
import os
import idyntree.bindings as iDynTree



# Main function
def main():

    # Get the urdf and parse it
    rootp = "C:\\Users\\ngenesio\\robotology\\robotology-superbuild\\robotology\\icub-models\\iCub\\robots\\"
    
    URDF_FILE = rootp+'iCubGazeboV2_5\\model.urdf';

    dynComp = iDynTree.KinDynComputations();
    mdlLoader = iDynTree.ModelLoader();
    mdlExporter = iDynTree.ModelExporter();
    mdlLoader.loadModelFromFile(URDF_FILE);
        
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
    # Define the armature
    # Create armature and armature object
    armature_name = "iCub"
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

        bchild.head = parent_link_position
        bchild.tail = child_link_position
        if jointtype != "FIXED":
            length = bchild.length
            if length == 0.0:
                length = 0.01 # bones with zero length are deleted by Blender
            direction = mathutils.Vector(direction).normalized()
            direction.rotate(child_link_rotation)
            bchild.tail = bchild.head + direction * length 
        
        bone_list[childname] = bchild
        # Consider the y-axis orientation in the limits
        limit_y_lower = min if (direction[1] > 0) else -max
        limit_y_upper = max if (direction[1] > 0) else -min
        limits[model.getJointName(idyn_joint_idx)] = [limit_y_lower, limit_y_upper, jointtype]

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
        
    # exit edit mode to save bones so they can be used in pose mode
    bpy.ops.object.mode_set(mode='OBJECT')
    meshMap = {}
    meshesInfo = {}
    
    # Remove meshes leftovers
    collection_name = "Collection"
    # Get the collection from its name
    collection = bpy.data.collections[collection_name]

    # Will collect meshes from delete objects
    meshes = set()
    # Get objects in the collection if they are meshes
    for obj in [o for o in collection.objects if o.type == 'MESH']:
        # Store the internal mesh
        meshes.add( obj.data )
        # Delete the object
        bpy.data.objects.remove( obj )
    # Look at meshes that are orphean after objects removal
    for mesh in [m for m in meshes if m.users == 0]:
        # Delete the meshes
        bpy.data.meshes.remove( mesh )
    # import meshes and do the mapping to the link
    
    for link_id in range(model.getNrOfLinks()):
        if len(linkVisual[link_id]) == 0:
            continue
        if not linkVisual[link_id][0].isExternalMesh():
            continue
        meshesInfo[model.getLinkName(link_id)] = linkVisual[link_id][0].asExternalMesh()
        filePath = meshesInfo[model.getLinkName(link_id)].getFileLocationOnLocalFileSystem()
        linkname = model.getLinkName(link_id)
        # import the mesh
        if ".stl" in filePath:
            bpy.ops.import_mesh.stl(filepath=os.path.join(filePath),global_scale=0.001)
        elif ".ply" in filePath:
            bpy.ops.import_mesh.ply(filepath=os.path.join(filePath),global_scale=0.001)
        elif ".dae" in filePath:
            bpy.ops.wm.collada_import(filepath=os.path.join(filePath)) #TODO check how to handle scale here !
        meshName = ""
        # We are assuming we are starting in a clean environment
        if not meshMap.keys() :
            meshName = bpy.data.meshes.keys()[0]
        else:
            for mesh in bpy.data.meshes:
                if mesh.name not in meshMap.values():
                    meshName = mesh.name
                    break
        meshMap[linkname] = meshName
    
    # just for checking that the map link->mesh is ok.
    #for k,v in meshMap.items():
    #    print(k,v)

    # Place the meshes
    for link_id in range(model.getNrOfLinks()):
        linkname = model.getLinkName(link_id)
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
        #print(meshesInfo[linkname].getLink_H_geometry())
        #print(bone_list[linkname].name)
        #bpy.data.objects[meshname].parent_type = 'BONE'
       #bpy.data.objects[meshname].parent   = bpy.data.objects[linkname]
    
    # Now iterate over all the joints(bones) and link them to the meshes.
    for idyn_joint_idx in range(model.getNrOfJoints()):
        # The joint should move the child link(?)
        childIdx = traversal.getChildLinkIndexFromJointIndex(model,
                                                              idyn_joint_idx)
        childname = model.getLinkName(childIdx)
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





# Execute main()
if __name__=='__main__':
    main()
