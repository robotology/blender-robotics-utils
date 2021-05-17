import bpy, bmesh
from bpy import *
from bpy.utils import *
from bpy.types import *
import copy
import xml.etree.ElementTree as ET
rootp = "C:\\Users\\ngenesio\\robotology\\robotology-superbuild\\robotology\\icub-models\\iCub\\robots\\"
root = ET.parse(rootp+'iCubGazeboV2_5\\model.urdf').getroot()[0]

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
    # Define the armature
    arm_obj = bpy.data.objects['Armature']
    # must be in edit mode to add bones
    bpy.context.scene.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_bones = arm_obj.data.edit_bones

    b = edit_bones.new('bone1')
    # a new bone will have zero length and not be kept
    # move the head/tail to keep the bone
    b.head = (1.0, 1.0, 0.0)
    b.tail = (1.0, 1.0, 1.0)

    b = edit_bones.new('bone2')
    b.head = (1.0, 2.0, 0.0)
    b.tail = (1.0, 2.0, 1.0)

    # exit edit mode to save bones so they can be used in pose mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # make the custom bone shape
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, diameter=0.2, segments=8)
    me = bpy.data.meshes.new("Mesh")
    bm.to_mesh(me)
    bm.free()
    b2_shape = bpy.data.objects.new("bone2_shape", me)
    bpy.context.scene.objects.link(b2_shape)
    b2_shape.layers = [False]*19+[True]

    # use pose.bones for custom shape
    arm_obj.pose.bones['bone2'].custom_shape = b2_shape
    # use data.bones for show_wire
    arm_obj.data.bones['bone2'].show_wire = True



    links = {}
    joints = {}
    # Define all links and joints reading from the urdf.
    for i in root:
        if i.tag == "link":
            links[i.attrib["name"]] = i
        # Add joints, ignoring the "fake ones" (ft and skin)
        if i.tag == "joint" and "_ft_" not in i.attrib["name"] and "_skin_" not in i.attrib["name"]:
            joints[i.attrib["name"]] = i

    l = {}
    tagged = []

    for j in joints:
        axis       = GetTag(["axis", "xyz"], j).text.split()
        parentname = GetTag(["parent"], j).text



# Execute main()
if __name__=='__main__':
    main()
