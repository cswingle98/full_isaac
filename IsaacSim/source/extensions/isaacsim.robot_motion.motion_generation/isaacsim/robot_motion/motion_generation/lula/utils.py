# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import lula
from isaacsim.core.prims import SingleXFormPrim
from isaacsim.core.utils.numpy.rotations import quats_to_rot_matrices


def get_prim_pose_in_meters(prim: SingleXFormPrim, meters_per_unit: float):
    pos, quat_rot = prim.get_world_pose()
    rot = quats_to_rot_matrices(quat_rot)
    pos *= meters_per_unit
    return pos, rot


def get_prim_pose_in_meters_rel_robot_base(prim, meters_per_unit, robot_pos, robot_rot):
    # returns the position of a prim relative to the position of the robot
    trans, rot = get_prim_pose_in_meters(prim, meters_per_unit)
    return get_pose_rel_robot_base(trans, rot, robot_pos, robot_rot)


def get_pose_rel_robot_base(trans, rot, robot_pos, robot_rot):
    inv_rob_rot = robot_rot.T

    if trans is not None:
        trans_rel = inv_rob_rot @ (trans - robot_pos)
    else:
        trans_rel = None

    if rot is not None:
        rot_rel = inv_rob_rot @ rot
    else:
        rot_rel = None

    return trans_rel, rot_rel


def get_pose3(trans=None, rot_mat=None, rot_quat=None) -> lula.Pose3:
    """
    Get lula.Pose3 type representing a transformation.
    rot_mat will take precedence over rot_quat if both are supplied
    """

    if trans is None and rot_mat is None and rot_quat is None:
        return lula.Pose3()

    if trans is None:
        if rot_mat is not None:
            return lula.Pose3.from_rotation(lula.Rotation3(rot_mat))
        else:
            return lula.Pose3.from_rotation(lula.Rotation3(*rot_quat))

    if rot_mat is None and rot_quat is None:
        return lula.Pose3.from_translation(trans)

    if rot_mat is not None:
        return lula.Pose3(lula.Rotation3(rot_mat), trans)
    else:
        return lula.Pose3(lula.Rotation3(*rot_quat), trans)
