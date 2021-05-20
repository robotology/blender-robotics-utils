import bpy, bmesh
import copy
import xml.etree.ElementTree as ET

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
    root = ET.parse(rootp+'iCubGazeboV2_5\\model.urdf').getroot()

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
    joints = {}
    print("starting urdf parsing loop")
    # Define all links and joints reading from the urdf.
    for i in root:
        # Ignore fake links/joints
        if "name" in i.attrib.keys():
            if "_skin_" in i.attrib["name"] or "_dh_frame" in i.attrib["name"] or "_back_contact" in i.attrib["name"] or "_fixed_joint" in i.attrib["name"]:
                continue
        if i.tag == "link":
            links[i.attrib["name"]] = i
            #print("Link:")
            #print(i.attrib["name"])
        # Add joints
        if i.tag == "joint":
            joints[i.attrib["name"]] = i
            #print("joint:")
            #print(i)

    bone_list = {}
    print("starting urdf parsing ")
    #print(joints)
    # Loop for defining the hierarchy
    for key, value in joints.items():

        try:
            axis        = [float(s) for s in GetTag(["axis"], value).attrib["xyz"].split()]
            origin      = [float(s) for s in GetTag(["origin"], value).attrib["xyz"].split()]
        except:
            pass

        parentname  = GetTag(["parent"], value).attrib["link"]
        childname   = GetTag(["child"], value).attrib["link"]

        #try:
        #    b = bpy.data.objects[value.attrib["name"]]
        #except KeyError:
        #    b = edit_bones.new(value.attrib["name"])

        #print("Adding bone:")
        #print(value.attrib["name"])
        #print("With axis:")
        #print(axis)
        bparent = None
        if parentname in bone_list.keys():
            bparent = bone_list[parentname]
        else:
            if parentname != "root_link":
                for k,v in joints.items():
                    if GetTag(["child"], v).attrib["link"] == parentname:
                        bparent = edit_bones.new(v.attrib["name"])
                        break
            else:
                bparent = edit_bones.new(parentname)
            # TODO I have to put random value for head and tail bones otherwise bones with 0 lenght are removed
            bparent.head = (0,0,0)
            bparent.tail = (0,0,1)
            bone_list[parentname] = bparent

        bchild = edit_bones.new(value.attrib["name"])
        if bparent:
            bchild.parent = bparent
        bone_list[childname] = bchild
        # TODO I have to put random value for head and tail bones otherwise bones with 0 lenght are removed
        bchild.head = (0,0,0)
        bchild.tail = (0,0,1)
        # No idea where to put the axis




        # Loop for the joint position and limits.
        #if parentname == "root_link":
            #b.head = (origin[0], origin[1], origin[2])
        #else:
            #bparent = bpy.data.objects[parentname]
            #b.head = (bparent.head[0] + origin[0], bparent.head[1] + origin[1], bparent.head[2] + origin[2])

        #b.tail = (b.head[0] + axis[0], b.head[1] + axis[1], b.head[2] + axis[2])

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
