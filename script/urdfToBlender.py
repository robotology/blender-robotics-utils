import bpy, bmesh
import copy
import mathutils
import math
import idyntree.bindings as iDynTree

def getwcoord(o):
    return o.GetMg().off

def setwcoord(o, v):
    o.SetRelPos(v * ~o.GetUpMg())
    return getwcoord(o)

def GetTag(taglist, root):
    if len(taglist) == 0:
        return root
    else:
        r = [i for i in root if i.tag == taglist[0]]
        taglist.pop(0)

    if len(r):
        return GetTag(taglist, r[0])
    else:
        return None

def get_all_objects(op, output):
    while op:
        output.append(op)
        get_all_objects(op.GetDown(), output)
        op = op.GetNext()
    return output

def axisrot(v, op):
    op.SetMl(MatrixRotX(v.x)*MatrixRotX(v.y)*MatrixRotX(v.z))


def applyrot(o, p):
    o.SetMg(MatrixRotX(p.x))
    o.SetMg(MatrixRotY(p.y) * o.GetMg())
    o.SetMg(MatrixRotZ(p.z) * o.GetMg())

def applyrotl(o, p):
    o.SetMl(MatrixRotX(p.x))
    o.SetMl(MatrixRotY(p.y) * o.GetMl())
    o.SetMl(MatrixRotZ(p.z) * o.GetMl())



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

    links = {}
    joints = []

    bone_list = {}
    #print(joints)
    # Loop for defining the hierarchy
    for idyn_joint_idx in range(model.getNrOfJoints()):

        parentname = model.getLinkName(traversal.getParentLinkIndexFromJointIndex(model,
                                                                         idyn_joint_idx))
        childname = model.getLinkName(traversal.getChildLinkIndexFromJointIndex(model,
                                                                         idyn_joint_idx))

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
        #print("Adding", key, parentname, childname, parent_link_position, child_link_position,"LENGTH", bchild.length)
            
        #hide fixed_joint and ft bones (for now just in edit mode :/)
        bone_list[childname] = bchild

    # exit edit mode to save bones so they can be used in pose mode
    bpy.ops.object.mode_set(mode='OBJECT')
    

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
