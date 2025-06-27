# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import asyncio
import gc
import os
import weakref

import carb
import omni.appwindow
import omni.ext
import omni.graph.core as og
import omni.kit.commands
import omni.ui as ui
import usdrt.Sdf
from isaacsim.core.api import PhysicsContext
from isaacsim.core.utils.prims import create_prim
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.examples.browser import get_instance as get_browser_instance
from isaacsim.gui.components.ui_utils import setup_ui_headers
from isaacsim.storage.native import get_assets_root_path
from pxr import Gf

MENU_NAME = "MoveIt"
FRANKA_STAGE_PATH = "/Franka"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._ext_id = ext_id
        """Initialize extension and UI elements"""
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()

        get_browser_instance().register_example(
            name="Franka MoveIt", execute_entrypoint=self.build_window, ui_hook=self.build_ui, category="ROS2/MoveIt"
        )

    def build_window(self):
        pass

    def build_ui(self):
        # check if ros2 bridge is enabled before proceeding
        extension_enabled = omni.kit.app.get_app().get_extension_manager().is_extension_enabled("isaacsim.ros2.bridge")
        if not extension_enabled:
            msg = "ROS2 Bridge is not enabled. Please enable the extension to use this feature."
            carb.log_error(msg)
        else:
            overview = "This sample demonstrates how to use MoveIt with Isaac Sim. \n\n The Environment Loaded already contains the OmniGraphs needed to connect with MoveIt."
            self._main_stack = ui.VStack(spacing=5, height=0)
            with self._main_stack:
                setup_ui_headers(
                    self._ext_id,
                    file_path=os.path.abspath(__file__),
                    title="MoveIt Example Environment",
                    overview=overview,
                    info_collapsed=False,
                )
                ui.Button("Load Sample Scene", clicked_fn=self._on_environment_setup)

    def create_ros_action_graph(self, franka_stage_path):
        try:
            og.Controller.edit(
                {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
                {
                    og.Controller.Keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
                        ("Context", "isaacsim.ros2.bridge.ROS2Context"),
                        ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
                        ("SubscribeJointState", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
                        ("ArticulationController", "isaacsim.core.nodes.IsaacArticulationController"),
                        ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
                    ],
                    og.Controller.Keys.CONNECT: [
                        ("OnPlaybackTick.outputs:tick", "PublishJointState.inputs:execIn"),
                        ("OnPlaybackTick.outputs:tick", "SubscribeJointState.inputs:execIn"),
                        ("OnPlaybackTick.outputs:tick", "PublishClock.inputs:execIn"),
                        ("OnPlaybackTick.outputs:tick", "ArticulationController.inputs:execIn"),
                        ("Context.outputs:context", "PublishJointState.inputs:context"),
                        ("Context.outputs:context", "SubscribeJointState.inputs:context"),
                        ("Context.outputs:context", "PublishClock.inputs:context"),
                        ("ReadSimTime.outputs:simulationTime", "PublishJointState.inputs:timeStamp"),
                        ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
                        ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                        (
                            "SubscribeJointState.outputs:positionCommand",
                            "ArticulationController.inputs:positionCommand",
                        ),
                        (
                            "SubscribeJointState.outputs:velocityCommand",
                            "ArticulationController.inputs:velocityCommand",
                        ),
                        ("SubscribeJointState.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),
                    ],
                    og.Controller.Keys.SET_VALUES: [
                        # Setting the /Franka target prim to Articulation Controller node
                        ("ArticulationController.inputs:robotPath", franka_stage_path),
                        ("PublishJointState.inputs:topicName", "isaac_joint_states"),
                        ("SubscribeJointState.inputs:topicName", "isaac_joint_commands"),
                        ("PublishJointState.inputs:targetPrim", [usdrt.Sdf.Path(franka_stage_path)]),
                    ],
                },
            )
        except Exception as e:
            print(e)
        pass

    def create_franka(self, stage_path):
        usd_path = "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        asset_path = self._assets_root_path + usd_path
        prim = self._stage.DefinePrim(stage_path, "Xform")
        prim.GetReferences().AddReference(asset_path)

        prim.GetVariantSet("Gripper").SetVariantSelection("AlternateFinger")
        prim.GetVariantSet("Mesh").SetVariantSelection("Quality")

        rot_mat = Gf.Matrix3d(Gf.Rotation((0, 0, 1), 90))
        omni.kit.commands.execute(
            "TransformPrimCommand",
            path=prim.GetPath(),
            old_transform_matrix=None,
            new_transform_matrix=Gf.Matrix4d().SetRotate(rot_mat).SetTranslateOnly(Gf.Vec3d(0, -0.64, 0)),
        )
        pass

    async def _create_moveit_sample(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        set_camera_view(eye=[1.20, 1.20, 0.80], target=[0, 0, 0.50], camera_prim_path="/OmniverseKit_Persp")
        self._stage = self._usd_context.get_stage()

        self.create_franka(FRANKA_STAGE_PATH)
        await omni.kit.app.get_app().next_update_async()
        create_prim(
            prim_path="/background", usd_path=self._assets_root_path + "/Isaac/Environments/Simple_Room/simple_room.usd"
        )
        await omni.kit.app.get_app().next_update_async()
        PhysicsContext(physics_dt=1.0 / 60.0)
        await omni.kit.app.get_app().next_update_async()
        self.create_ros_action_graph(FRANKA_STAGE_PATH)
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()

    def _on_environment_setup(self):

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        asyncio.ensure_future(self._create_moveit_sample())

    def on_shutdown(self):
        """Cleanup objects on extension shutdown"""
        get_browser_instance().deregister_example(name=MENU_NAME, category="ROS2")
        self._timeline.stop()
        gc.collect()
