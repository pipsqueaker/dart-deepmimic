from asf_skeleton import ASF_Skeleton
from transformations import euler_from_matrix, compose_matrix
from xml.dom import minidom
from xml.etree import ElementTree
import argparse
import math
import numpy as np
import os
import re
import utils
import xml.etree.ElementTree as ET

CYLINDER_RADIUS = .5

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    # Sourced from https://pymotw.com/2/xml/etree/ElementTree/create.html
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def num2string(num):
    """
    Function to provide common file-wide number formatting
    """

    # The "+ 0" gets rid of "-0"s being printed
    return "{0:.5f}".format(num + 0)

def vec2string(vec):
    """
    Return a space-delineated string of numbers in the vector, with no enclosing
    brackets. Uses num2string internally
    """
    return " ".join([num2string(i) for i in vec])

def bodyname(joint):
    """
    Returns the name of a joint
    """
    return joint.name + "_body"

def add_cylinder(xml_parent, length):

    geo_xml = ET.SubElement(xml_parent, "geometry")

    geo_cylinder = ET.SubElement(geo_xml, "cylinder")
    radius = ET.SubElement(geo_cylinder, "radius")
    height = ET.SubElement(geo_cylinder, "height")
    radius.text = num2string(CYLINDER_RADIUS)
    height.text = num2string(length)

def add_box(xml_parent, length):
    geo_xml = ET.SubElement(xml_parent, "geometry")
    geo_box = ET.SubElement(geo_xml, "box")
    box_size = ET.SubElement(geo_box, "size")
    box_size.text = vec2string([length, 2 * CYLINDER_RADIUS, CYLINDER_RADIUS])

def dump_bodies(asf_skeleton, skeleton_xml):
    """
    Given an XML element (an ETElement), dump the skeleton's joint objects
    as the element's children

    This method expects all joint angles in the skeleton to be zero. Else, all
    the axes and angles will be messed up

    It also handles all the calculations concerning axes and joints
    """

    # Ensure all positions are at their "default" values; also, we need to make
    # use of the per-instance attributes which update_joint_positions adds/sets
    asf_skeleton.update_joint_positions()

    for joint in [asf_skeleton.root] + asf_skeleton.joints:

        body_xml = ET.SubElement(skeleton_xml, "body")
        body_xml.set("name", bodyname(joint))

        ################################
        # POSITION AND COORDINATE AXES #
        ################################

        rmatrix = joint.ctrans
        tform_text = vec2string(np.append(joint.base_pos,
                                          euler_from_matrix(rmatrix[:3, :3],
                                                            axes="rxyz")))
        ET.SubElement(body_xml, "transformation").text = tform_text

        ########################################
        # VISUALIZATION AND COLLISION GEOMETRY #
        ########################################

        # Direction vectors and axes are specified wrt to global reference
        # frame in asf files (and thus in joints), so we construct a
        # transformation to the local reference frame (as dart expects it)
        local_direction = np.matmul(joint.ctrans_inv[:3, :3], joint.direction)
        direction_matrix = utils.rmatrix_x2v(local_direction)
        rangles = utils.rotationMatrixToEulerAngles(direction_matrix)
        trans_offset = joint.length * local_direction / 2
        tform_vector = np.append(trans_offset, rangles)

        for shape in ["visualization", "collision"]:
            shape_xml = ET.SubElement(body_xml, shape + "_shape")
            ET.SubElement(shape_xml, "transformation").text = vec2string(tform_vector)
            add_box(shape_xml, joint.length)

        ###################
        # INERTIA SECTION #
        ###################

        inertia_xml = ET.SubElement(body_xml, "inertia")
        mass_xml = ET.SubElement(inertia_xml, "mass")
        mass_xml.text = str(1)
        ET.SubElement(inertia_xml, "offset").text = vec2string(trans_offset)

def write_joint_xml(skeleton_xml, joint):

    joint_xml = ET.SubElement(skeleton_xml, "joint")

    ET.SubElement(joint_xml, "parent").text = bodyname(joint.parent)
    ET.SubElement(joint_xml, "child").text = bodyname(joint)
    joint_xml.set("name", joint.name)

    ET.SubElement(joint_xml, "transformation").text = "0 0 0 "\
                                                      "0 0 0"

    jtype = ""
    if len(joint.dofs) == 0:
        jtype = "fixed"
    elif len(joint.dofs) == 1:
        jtype = "revolute"
    elif len(joint.dofs) == 2:
        jtype = "universal"
    elif len(joint.dofs) == 3:
        jtype = "euler"
        ET.SubElement(joint_xml, "axis_order").text = "xyz"
    else:
        raise RuntimeError("Invalid number of axes")

    # Dart doesn't support fixed joints, so my current workaround is to use a
    # revolute joint with limits (0, 0)
    if jtype == "fixed":
        joint_xml.set("type", "revolute")
        axis_xml = ET.SubElement(joint_xml, "axis")
        ET.SubElement(axis_xml, "xyz").text = "1 0 0"
        limit_xml = ET.SubElement(axis_xml, "limit")
        ET.SubElement(limit_xml, "lower").text = "0"
        ET.SubElement(limit_xml, "upper").text = "0"
        return

    joint_xml.set("type", jtype)
    for index, axis in enumerate(joint.dofs):
        axis_tag = "axis" + ("" if index == 0 else str(index + 1))

        axis_vstr = ""
        if axis == "x":
            axis_vstr = "1 0 0"
        elif axis == "y":
            axis_vstr = "0 1 0"
        elif axis == "z":
            axis_vstr = "0 0 1"

        axis_xml = ET.SubElement(joint_xml, axis_tag)

        ET.SubElement(axis_xml, "xyz").text = axis_vstr
        # TODO implement joint limits!!
        # limit_xml = ET.SubElement(axis_xml, "limit")
        # ET.SubElement(limit_xml, "lower").text = "-3"
        # ET.SubElement(limit_xml, "upper").text = "3"

        # TODO implement dynamics
        # dynamics = ET.SubElement(axis_xml, "dynamics")
        # ET.SubElement(dynamics, "damping").text = "1"
        # ET.SubElement(dynamics, "stiffness").text = "0"

def dump_joints(asf_skeleton, skeleton_xml):
    """
    Given a skeleton object and an xml root, dump joints
    """

    # Setup a special joint for the root
    root_joint = ET.SubElement(skeleton_xml, "joint")
    root_joint.set("name", "root")
    ET.SubElement(root_joint, "parent").text = "world"
    ET.SubElement(root_joint, "child").text = bodyname(asf_skeleton.root)
    root_joint.set("type", "free")

    for joint in asf_skeleton.joints:

        write_joint_xml(skeleton_xml, joint)

def dump_asf_to_skel(asf_skeleton):

    skeleton_xml = ET.Element("skeleton")
    skeleton_xml.set("name", asf_skeleton.name)
    ET.SubElement(skeleton_xml, "transformation").text = "0 0 0 0 0 0"
    dump_bodies(asf_skeleton, skeleton_xml)
    dump_joints(asf_skeleton, skeleton_xml)

    # The first line is always <xml_version 1.0>, so skip that
    return "\n".join(prettify(skeleton_xml).splitlines()[1:])

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Dumps an asf file to a .skel")

    parser.add_argument("--asf", dest="asf_path", default=False)

    args = parser.parse_args()

    skel = ASF_Skeleton(args.asf_path)

    new_skel = dump_asf_to_skel(skel)

    start_flag = r"<!--START-->"
    end_flag = r"<!--END-->"
    source_fname = r"test/original/human_box.skel"
    dest_fname = r"test/human.skel"

    with open(source_fname, "r") as f:
        file_text = "".join(f.readlines())

    try:
        os.remove(dest_fname)
    except FileNotFoundError:
        pass

    with open(dest_fname, "w") as f:
        file_text = re.sub(start_flag + ".*" + end_flag,
                           start_flag + "\n" + new_skel + "\n" + end_flag,
                           file_text, flags=re.DOTALL)
        f.write(file_text)
