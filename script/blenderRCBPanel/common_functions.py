import bpy
import math
import idyntree.bindings as iDynTree


class IkVariables:
    inverseKinematics = iDynTree.InverseKinematics()
    dynComp = iDynTree.KinDynComputations()
    iDynTreeModel = None


def printError(object, *args):
    object.report({"ERROR"}, " ".join(args))


class InverseKinematics:

    def __init__(self):
        pass

    @staticmethod
    def execute(object, xyz=[], rpy=[]):
        scene = bpy.context.scene
        considered_joints = []
        ik = IkVariables.inverseKinematics
        model = ik.fullModel()

        # bpy.ops.object.wm_ot_reachTarget
        mytool = scene.my_tool

        base_frame = mytool.my_baseframeenum
        endeffector_frame = mytool.my_eeframeenum

        if base_frame == endeffector_frame:
            printError(object, "Base frame and end-effector frame are coincident!")
            return {'CANCELLED'}

        # TODO substitute the traversal part with this block after
        # DHChain has been added to the bindings
        # dhChain = iDynTree.DHChain()
        # dhChain.fromModel(model, base_frame, endeffector_frame)

        # for chain_idx in range(dhChain.getNrOfDOFs()):
        #    considered_joints.append(dhChain.getDOFName(chain_idx))

        traversal = iDynTree.Traversal()
        ok_traversal = model.computeFullTreeTraversal(traversal)

        if not ok_traversal:
            printError(object, "Unable to get the traversal")
            return {'CANCELLED'}

        base_link_idx = model.getLinkIndex(base_frame)
        endeffector_link_idx = model.getLinkIndex(endeffector_frame)
        if base_link_idx < 0 or endeffector_link_idx < 0:
            return {'CANCELLED'}

        visitedLinkIdx = endeffector_link_idx
        # create the list of considered joints, it is the list of the joints of
        # the selected chain
        while visitedLinkIdx != base_link_idx:
            parentLink = traversal.getParentLinkFromLinkIndex(visitedLinkIdx)
            if parentLink is None:
                printError(object, "Unable to find a single chain that goes from", base_frame, "to", endeffector_frame)
                return {'CANCELLED'}
            parentLinkIdx = parentLink.getIndex()
            joint = traversal.getParentJointFromLinkIndex(visitedLinkIdx)
            visitedLinkIdx = parentLinkIdx
            if joint.getNrOfDOFs() == 0:
                continue
            considered_joints.append(model.getJointName(joint.getIndex()))

        # Extract reduced model

        ik.setModel(model, considered_joints)
        IkVariables.dynComp.loadRobotModel(ik.reducedModel())
        joint_positions = iDynTree.VectorDynSize(ik.reducedModel().getNrOfDOFs())

        # Note: the InverseKinematics class actually implements a floating base inverse kinematics,
        # meaning that both the joint position and the robot base are optimized to reach the desired cartesian position
        world_H_base = IkVariables.dynComp.getWorldTransform(base_frame)

        ok = IkVariables.inverseKinematics.setFloatingBaseOnFrameNamed(base_frame)

        ik.addFrameConstraint(base_frame, world_H_base)

        # base_H_ee_initial = IkVariables.dynComp.getRelativeTransform(base_frame, endeffector_frame);

        if not rpy:
            iDynTreeRotation = iDynTree.Rotation.RPY(mytool.my_reach_roll * math.pi / 180,
                                                     mytool.my_reach_pitch * math.pi / 180,
                                                     mytool.my_reach_yaw * math.pi / 180)
        else:
            iDynTreeRotation = iDynTree.Rotation.RPY(rpy[0] * math.pi / 180,
                                                     rpy[1] * math.pi / 180,
                                                     rpy[2] * math.pi / 180)

        if not xyz:
            iDynTreePosition = iDynTree.Position(mytool.my_reach_x, mytool.my_reach_y, mytool.my_reach_z)
        else:
            iDynTreePosition = iDynTree.Position(-xyz[0], xyz[1], xyz[2])

        # Define the transform of the selected cartesian target
        base_H_ee_desired = iDynTree.Transform(iDynTreeRotation, iDynTreePosition)

        # We want that the end effector reaches the target
        ok = ik.addTarget(endeffector_frame, base_H_ee_desired)
        if not ok:
            ok = ik.updateTarget(endeffector_frame, base_H_ee_desired)
            if not ok:
                printError(object, "Impossible to add target on ", endeffector_frame)
                return {'CANCELLED'}
        # Initialize ik
        IkVariables.dynComp.getJointPos(joint_positions)
        ik.setReducedInitialCondition(world_H_base, joint_positions)
        # ik.setDesiredReducedJointConfiguration(joint_positions)

        # TODO: The following line generated the WARNING:
        #  [WARNING] InverseKinematics: joint l_elbow (index 20)
        #           initial condition is outside the limits 0.261799 1.85005. Actual value: 0
        #  [WARNING] InverseKinematics: joint r_elbow (index 28)
        #           initial condition is outside the limits 0.261799 1.85005. Actual value: 0
        ok = ik.solve()

        if not ok:
            printError(object, "Impossible to solve inverse kinematics problem.")
            return {'CANCELLED'}

        base_transform = iDynTree.Transform.Identity()

        # Get the solution
        ik.getReducedSolution(base_transform, joint_positions)
        IkVariables.dynComp.setJointPos(joint_positions)

        pose_bones = bpy.data.objects[bpy.context.scene.my_tool.my_armature].pose.bones
        for idyn_joint_idx in range(ik.reducedModel().getNrOfDOFs()):

            # It is a prismatic joint (to be tested)
            joint_name = ik.reducedModel().getJointName(idyn_joint_idx)

            joint = pose_bones[joint_name]
            joint_value = joint_positions[idyn_joint_idx]

            if joint.lock_rotation[1]:
                joint.delta_location[1] = joint_value
            # It is a revolute joint
            else:
                joint.rotation_euler[1] = joint_value
                joint.keyframe_insert(data_path="rotation_euler")

        return {'FINISHED'}
