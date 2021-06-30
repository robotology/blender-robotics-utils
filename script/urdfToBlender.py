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
    # Remove fixed joints
    considered_joints = []
    for j_id in range(mdlLoader.model().getNrOfJoints()):
        joint = mdlLoader.model().getJoint(j_id)
        joint_name = mdlLoader.model().getJointName(j_id)
        if joint.getNrOfDOFs() == 0:
            continue
        considered_joints.append(joint_name)
        
    # Produce the reduced urdf    
    mdlLoader.loadReducedModelFromFullModel(mdlLoader.model(), considered_joints)
    model = mdlLoader.model()
    traversal = iDynTree.Traversal()
    ok_traversal = model.computeFullTreeTraversal(traversal)
    
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
    #print(joints)
    # Loop for defining the hierarchy of the bonse and its locations
    for idyn_joint_idx in range(model.getNrOfJoints()):
        parentIdx = traversal.getParentLinkIndexFromJointIndex(model,
                                                               idyn_joint_idx)
        childIdx = traversal.getChildLinkIndexFromJointIndex(model,
                                                              idyn_joint_idx)
        parentname = model.getLinkName(parentIdx)
        childname = model.getLinkName(childIdx)
        joint = model.getJoint(idyn_joint_idx).asRevoluteJoint()
        min = joint.getMinPosLimit(0)
        max = joint.getMaxPosLimit(0)
        direction =	joint.getAxis(childIdx,parentIdx).getDirection().toNumPy()
        bparent = None
        if parentname in bone_list.keys():
            bparent = bone_list[parentname]
        else:
            if parentname != "root_link":
                for i in range(model.getNrOfJoints()):
                    childname_prev = model.getLinkName(traversal.getChildLinkIndexFromJointIndex(model,
                                                                         i))
                    if childname_prev == parentname:
                        bparent = edit_bones.new(model.getJointName(i))
                        break
            else:
                bparent = edit_bones.new(parentname)
            # TODO I have to put random value for head and tail bones otherwise bones with 0 lenght are removed
            bparent.head = (0,0,0)
            bparent.tail = (0,0,-0.01)
            bone_list[parentname] = bparent

        bchild = edit_bones.new(model.getJointName(idyn_joint_idx))
        if bparent:
            bchild.parent = bparent
        
        parent_link_position = dynComp.getRelativeTransform("root_link", parentname).getPosition().toNumPy();
        child_link_position  = dynComp.getRelativeTransform("root_link", childname).getPosition().toNumPy();

        bchild.head = parent_link_position
        bchild.tail = child_link_position
        length = bchild.length
        direction = mathutils.Vector(direction).normalized()
        bchild.tail = bchild.head + direction * length 
        
        bone_list[childname] = bchild
        # Consider the y-axis orientation in the limits
        limit_y_lower = min if (direction[1] > 0) else -max
        limit_y_upper = max if (direction[1] > 0) else -min
        limits[model.getJointName(idyn_joint_idx)] = [limit_y_lower, limit_y_upper]


    # configure the bones limits    
    bpy.ops.object.mode_set(mode='POSE')
    for pbone in pose_bones:
        bone_name = pbone.basename
        pbone.lock_location = (True, True, True)
        pbone.lock_rotation = (True, True, True)
        pbone.lock_scale = (True, True, True)
        
        # root_link is fixed
        if bone_name == "root_link":
            continue
        
        c = pbone.constraints.new('LIMIT_ROTATION')
        c.owner_space = 'LOCAL'

        # The bones should rotate around y-axis
        pbone.lock_rotation[1] = False
        lim = limits[bone_name]
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
        meshesInfo[model.getLinkName(link_id)] = linkVisual[link_id][0].asExternalMesh()
        filePath = meshesInfo[model.getLinkName(link_id)].getFileLocationOnLocalFileSystem()
        linkname = model.getLinkName(link_id)
        # import the mesh
        bpy.ops.import_mesh.stl(filepath=os.path.join(filePath),global_scale=0.001)
        meshName = ""
        # We are assuming we are starting in a clean environment
        if not meshMap.keys() :
            meshName = bpy.data.meshes.keys()[0]
            print(linkname, meshName)
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
        #RtoLinklocation = RtoLinktransform.getPosition().toNumPy()
        #RtoLinkrotation = RtoLinktransform.getRotation().asQuaternion()
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
    


    # make the custom bone shape
    #bm = bmesh.new()
    #bmesh.ops.create_circle(bm, cap_ends=False, diameter=0.2, segments=8)
    #me = bpy.data.meshes.new("Mesh")
    #bm.to_mesh(me)
    #bm.free()
    #b2_shape = bpy.data.objects.new("bone2_shape", me)
    #bpy.context.scene.objects.link(b2_shape)
    #b2_shape.layers = [False]*19+[True]

    # use pose.bones for custom shape
    #arm_obj.pose.bones['bone2'].custom_shape = b2_shape
    # use data.bones for show_wire
    #arm_obj.data.bones['bone2'].show_wire = True





# Execute main()
if __name__=='__main__':
    main()
