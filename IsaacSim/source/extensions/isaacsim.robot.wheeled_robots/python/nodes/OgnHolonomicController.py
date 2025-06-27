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


import numpy as np
from isaacsim.core.nodes import BaseResetNode
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.robot.wheeled_robots.controllers.holonomic_controller import HolonomicController
from isaacsim.robot.wheeled_robots.ogn.OgnHolonomicControllerDatabase import OgnHolonomicControllerDatabase


class OgnHolonomicControllerInternalState(BaseResetNode):
    def __init__(self):
        self.wheel_radius = [0.0]
        self.wheel_positions = np.array([])
        self.wheel_orientations = np.array([])
        self.mecanum_angles = [0.0]
        self.wheel_axis = np.array([1.0, 0, 0])
        self.up_axis = np.array([0, 0, 1])
        self.controller_handle = None
        self.max_linear_speed = 1.0e20
        self.max_angular_speed = 1.0e20
        self.max_wheel_speed = 1.0e20
        self.linear_gain = 1.0
        self.angular_gain = 1.0
        self.node = None
        self.graph_id = None
        super().__init__(initialize=False)

    def initialize_controller(self) -> None:
        self.controller_handle = HolonomicController(
            name="holonomic_controller",
            wheel_radius=np.asarray(self.wheel_radius),
            wheel_positions=np.asarray(self.wheel_positions),
            wheel_orientations=np.asarray(self.wheel_orientations),
            mecanum_angles=np.asarray(self.mecanum_angles),
            wheel_axis=self.wheel_axis,
            up_axis=self.up_axis,
            max_linear_speed=self.max_linear_speed,
            max_angular_speed=self.max_angular_speed,
            max_wheel_speed=self.max_wheel_speed,
            linear_gain=self.linear_gain,
            angular_gain=self.angular_gain,
        )
        self.initialized = True

    def forward(self, command: np.ndarray) -> ArticulationAction:
        return self.controller_handle.forward(command)

    def custom_reset(self):
        if self.initialized:
            self.node.get_attribute("inputs:inputVelocity").set([0, 0, 0])
            self.node.get_attribute("outputs:jointVelocityCommand").set([0, 0, 0])


class OgnHolonomicController:
    """
    nodes for moving an articulated robot with joint commands
    """

    @staticmethod
    def init_instance(node, graph_instance_id):
        state = OgnHolonomicControllerDatabase.get_internal_state(node, graph_instance_id)
        state.node = node
        state.graph_id = graph_instance_id

    @staticmethod
    def release_instance(node, graph_instance_id):
        try:
            state = OgnHolonomicControllerDatabase.get_internal_state(node, graph_instance_id)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
            state.initialized = False

    @staticmethod
    def internal_state():
        return OgnHolonomicControllerInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.per_instance_state

        try:
            if not state.initialized:
                state.wheel_radius = db.inputs.wheelRadius
                state.wheel_positions = db.inputs.wheelPositions
                state.wheel_orientations = db.inputs.wheelOrientations
                state.mecanum_angles = db.inputs.mecanumAngles
                state.wheel_axis = db.inputs.wheelAxis
                state.up_axis = db.inputs.upAxis
                state.max_linear_speed = db.inputs.maxLinearSpeed
                state.max_angular_speed = db.inputs.maxAngularSpeed
                state.max_wheel_speed = db.inputs.maxWheelSpeed
                state.linear_gain = db.inputs.linearGain
                state.angular_gain = db.inputs.angularGain

                state.initialize_controller()

            joint_actions = state.forward(np.array(db.inputs.inputVelocity))

            if joint_actions.joint_velocities is not None:
                db.outputs.jointVelocityCommand = joint_actions.joint_velocities

        except Exception as error:
            db.log_warning(str(error))
            return False

        return True
