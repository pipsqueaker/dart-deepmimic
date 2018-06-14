
from cgkit.asfamc import AMCReader
from joint import expand_angle
from asf_skeleton import ASF_Skeleton
from transformations import compose_matrix, euler_from_matrix
import math
import numpy as np

class AMC:
    """
    Parent class representing information from a .amc file
    """

    def __init__(self, amc_filename, skeleton):

        self.name = None
        self.frames = []
        self.skeleton = skeleton

        def __init_frame(framenum, data):
            self.frames.append(data)

        reader = AMCReader(amc_filename)
        reader.onFrame = __init_frame
        reader.read()

    def sync_angles(self, framenum):
        """
        Call this method to set all of the skeleton's angles to the values in the
        corresponding frame of the AMC (where 0 is the first frame)
        """
        raise NotImplementedError("Abstract class, use either ASF or SKEL AMC classes")

class ASF_AMC(AMC):

    def sync_angles(self, framenum):

        frame = self.frames[framenum]
        root_data = frame[0][1]
        self.skeleton.root.direction = np.array(root_data[0:3])
        self.skeleton.root.theta_degrees = np.array(root_data[3:])

        for joint_name, joint_data in frame[1:]:
            joint = self.skeleton.name2joint[joint_name].theta_degrees
            joint.theta_degrees = expand_angle(joint_data, joint.dofs)

def sequential_to_rotating_radians(rvector):

    rmatrix = compose_matrix(angles=rvector, angle_order="sxyz")
    return euler_from_matrix(rmatrix[:3, :3], axes="rxyz")


class Skel_AMC(AMC):
    """
    A class to sync AMC frames with a Dart Skeleton object

    TODO Because dart offers no faculties for reading exactly what axes a joint
    rotates on, there's no way for sync_angles to know how to expand an angle
    with a dart skeleton alone. As a workaround, I require an ASFSkeleton to be
    passed in so that axis information can be read
    """

    def __init__(self, dart_skeleton, amc_filename, asf_filename):
        """
        dart_skeleton is not a filename; it's an object like world.skeletons[0]
        """
        super(Skel_AMC, self).__init__(amc_filename, dart_skeleton)

        # Set up a map of joint names to dof indices
        # start index and window length tuple
        self.joint2window = {}
        asf_skeleton = ASF_Skeleton(asf_filename)

        for joint in self.skeleton.joints:
            i = 0
            while True:
                if self.skeleton.dofs[i].name[:len(joint.name)] == joint.name:
                    self.joint2window[joint.name] = (i, joint.num_dofs(), \
                                        asf_skeleton.name2joint[joint.name].dofs)
                    break
                i += 1

    def sync_angles(self, framenum):

        frame = self.frames[framenum]
        root_data = frame[0][1]

        def zip_dofs(dof_list, pos_list):

            for dof, pos in zip(dof_list, pos_list):
                dof.set_position(pos)

        zip_dofs(self.skeleton.dofs[3:6], root_data[:3])
        zip_dofs(self.skeleton.dofs[0:3],
                 sequential_to_rotating_radians(np.multiply(math.pi / 180,
                                                            root_data[3:])))

        for joint_name, joint_angles in frame[1:]:
            start_index, num_dofs, order = self.joint2window[joint_name]

            theta = expand_angle(np.multiply(math.pi / 180, joint_angles),
                                 order)
            rotation_euler = sequential_to_rotating_radians(theta)

            zip_dofs(self.skeleton.dofs[start_index : start_index + num_dofs],
                     rotation_euler)
