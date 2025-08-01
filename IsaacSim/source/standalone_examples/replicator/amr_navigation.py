# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Generate synthetic data from an AMR navigating to random locations
"""

from isaacsim import SimulationApp

simulation_app = SimulationApp(launch_config={"headless": False})

import argparse
import builtins
import os
import random
from itertools import cycle

import carb.settings
import omni.client
import omni.kit.app
import omni.replicator.core as rep
import omni.timeline
import omni.usd
import omni.usd.commands
from isaacsim.core.utils.stage import add_reference_to_stage, create_new_stage
from isaacsim.storage.native import get_assets_root_path
from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdLux, UsdPhysics


class NavSDGDemo:
    CARTER_URL = "/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd"
    DOLLY_URL = "/Isaac/Props/Dolly/dolly.usd"
    PROPS_URL = "/Isaac/Props/YCB/Axis_Aligned_Physics"
    LEFT_CAMERA_PATH = "/NavWorld/CarterNav/chassis_link/sensors/front_hawk/left/camera_left"
    RIGHT_CAMERA_PATH = "/NavWorld/CarterNav/chassis_link/sensors/front_hawk/right/camera_right"

    def __init__(self):
        self._carter_chassis = None
        self._carter_nav_target = None
        self._dolly = None
        self._dolly_light = None
        self._props = []
        self._cycled_env_urls = None
        self._env_interval = 1
        self._timeline = None
        self._timeline_sub = None
        self._stage_event_sub = None
        self._stage = None
        self._trigger_distance = 2.0
        self._num_frames = 0
        self._frame_counter = 0
        self._writer = None
        self._out_dir = None
        self._render_products = []
        self._use_temp_rp = False
        self._in_running_state = False

    def start(
        self,
        num_frames=10,
        out_dir=None,
        env_urls=[],
        env_interval=3,
        use_temp_rp=False,
        seed=None,
    ):
        print(f"[NavSDGDemo] Starting")
        if seed is not None:
            random.seed(seed)
        self._num_frames = num_frames
        self._out_dir = out_dir if out_dir is not None else os.path.join(os.getcwd(), "_out_nav_sdg_demo")
        self._cycled_env_urls = cycle(env_urls)
        self._env_interval = env_interval
        self._use_temp_rp = use_temp_rp
        self._frame_counter = 0
        self._trigger_distance = 2.0
        self._load_env()
        self._randomize_dolly_pose()
        self._randomize_dolly_light()
        self._randomize_prop_poses()
        self._setup_sdg()
        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.play()
        self._timeline_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
            int(omni.timeline.TimelineEventType.CURRENT_TIME_TICKED), self._on_timeline_event
        )
        self._stage_event_sub = (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop_by_type(int(omni.usd.StageEventType.CLOSING), self._on_stage_closing_event)
        )
        self._in_running_state = True

    def clear(self):
        self._cycled_env_urls = None
        self._carter_chassis = None
        self._carter_nav_target = None
        self._dolly = None
        self._dolly_light = None
        self._timeline = None
        self._frame_counter = 0
        if self._stage_event_sub:
            self._stage_event_sub.unsubscribe()
        self._stage_event_sub = None
        if self._timeline_sub:
            self._timeline_sub.unsubscribe()
        self._timeline_sub = None
        self._clear_sdg_render_products()
        self._stage = None
        self._in_running_state = False

    def is_running(self):
        return self._in_running_state

    def _is_running_in_script_editor(self):
        return builtins.ISAAC_LAUNCHED_FROM_TERMINAL is True

    def _on_stage_closing_event(self, e: carb.events.IEvent):
        self.clear()

    def _load_env(self):
        # Fresh stage with custom physics scene for Nova Carter's navigation
        create_new_stage()
        self._stage = omni.usd.get_context().get_stage()
        self._add_physics_scene()

        # Environment
        assets_root_path = get_assets_root_path()
        add_reference_to_stage(usd_path=assets_root_path + next(self._cycled_env_urls), prim_path="/Environment")

        # Nova Carter
        add_reference_to_stage(usd_path=assets_root_path + self.CARTER_URL, prim_path="/NavWorld/CarterNav")
        self._carter_nav_target = self._stage.GetPrimAtPath("/NavWorld/CarterNav/targetXform")
        self._carter_chassis = self._stage.GetPrimAtPath("/NavWorld/CarterNav/chassis_link")

        # Dolly
        add_reference_to_stage(usd_path=assets_root_path + self.DOLLY_URL, prim_path="/NavWorld/Dolly")
        self._dolly = self._stage.GetPrimAtPath("/NavWorld/Dolly")
        if not self._dolly.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(self._dolly).AddTranslateOp()
        if not self._dolly.GetAttribute("xformOp:rotateXYZ"):
            UsdGeom.Xformable(self._dolly).AddRotateXYZOp()
        # Add colliders to the mesh and primitive types of the dolly descendent prims
        for desc_prim in Usd.PrimRange(self._dolly):
            # Enable collisions if the prim is of type mesh or gprim (primitive)
            if desc_prim.IsA(UsdGeom.Mesh) or desc_prim.IsA(UsdGeom.Gprim):
                if not desc_prim.HasAPI(UsdPhysics.CollisionAPI):
                    collision_api = UsdPhysics.CollisionAPI.Apply(desc_prim)
                else:
                    collision_api = UsdPhysics.CollisionAPI(desc_prim)
                collision_api.CreateCollisionEnabledAttr(True)
            # If the prim is a mesh add a collider aproximation type
            if desc_prim.IsA(UsdGeom.Mesh):
                if not desc_prim.HasAPI(UsdPhysics.MeshCollisionAPI):
                    mesh_collision_api = UsdPhysics.MeshCollisionAPI.Apply(desc_prim)
                else:
                    mesh_collision_api = UsdPhysics.MeshCollisionAPI(desc_prim)
                # The prim is static, setting the collider type to "none" (defaulting to "TriangleMesh", e.g. no approx)
                mesh_collision_api.CreateApproximationAttr().Set("none")

        # Light
        light = UsdLux.SphereLight.Define(self._stage, f"/NavWorld/DollyLight")
        light.CreateRadiusAttr(0.5)
        light.CreateIntensityAttr(35000)
        light.CreateColorAttr(Gf.Vec3f(1.0, 1.0, 1.0))
        self._dolly_light = light.GetPrim()
        if not self._dolly_light.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(self._dolly_light).AddTranslateOp()

        # Props
        props_urls = []
        props_folder_path = assets_root_path + self.PROPS_URL
        result, entries = omni.client.list(props_folder_path)
        if result != omni.client.Result.OK:
            carb.log_error(f"Could not list assets in path: {props_folder_path}")
            return
        for entry in entries:
            _, ext = os.path.splitext(entry.relative_path)
            if ext == ".usd":
                props_urls.append(f"{props_folder_path}/{entry.relative_path}")

        cycled_props_url = cycle(props_urls)
        for i in range(15):
            prop_url = next(cycled_props_url)
            prop_name = os.path.splitext(os.path.basename(prop_url))[0]
            path = f"/NavWorld/Props/Prop_{prop_name}_{i}"
            prim = self._stage.DefinePrim(path, "Xform")
            prim.GetReferences().AddReference(prop_url)
            self._props.append(prim)

    def _add_physics_scene(self):
        # Physics setup specific for the navigation graph
        physics_scene = UsdPhysics.Scene.Define(self._stage, "/physicsScene")
        physx_scene = PhysxSchema.PhysxSceneAPI.Apply(self._stage.GetPrimAtPath("/physicsScene"))
        physx_scene.GetEnableCCDAttr().Set(True)
        physx_scene.GetEnableGPUDynamicsAttr().Set(False)
        physx_scene.GetBroadphaseTypeAttr().Set("MBP")

    def _randomize_dolly_pose(self):
        min_dist_from_carter = 4
        carter_loc = self._carter_chassis.GetAttribute("xformOp:translate").Get()
        for _ in range(100):
            x, y = random.uniform(-6, 6), random.uniform(-6, 6)
            dist = (Gf.Vec2f(x, y) - Gf.Vec2f(carter_loc[0], carter_loc[1])).GetLength()
            if dist > min_dist_from_carter:
                self._dolly.GetAttribute("xformOp:translate").Set((x, y, 0))
                self._carter_nav_target.GetAttribute("xformOp:translate").Set((x, y, 0))
                break
        self._dolly.GetAttribute("xformOp:rotateXYZ").Set((0, 0, random.uniform(-180, 180)))

    def _randomize_dolly_light(self):
        dolly_loc = self._dolly.GetAttribute("xformOp:translate").Get()
        self._dolly_light.GetAttribute("xformOp:translate").Set(dolly_loc + (0, 0, 2.5))
        self._dolly_light.GetAttribute("inputs:color").Set(
            (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
        )

    def _randomize_prop_poses(self):
        spawn_loc = self._dolly.GetAttribute("xformOp:translate").Get()
        spawn_loc[2] = spawn_loc[2] + 0.5
        for prop in self._props:
            prop.GetAttribute("xformOp:translate").Set(spawn_loc + (random.uniform(-1, 1), random.uniform(-1, 1), 0))
            spawn_loc[2] = spawn_loc[2] + 0.2

    def _setup_sdg(self):
        # Disable capture on play and async rendering
        carb.settings.get_settings().set("/omni/replicator/captureOnPlay", False)
        carb.settings.get_settings().set("/omni/replicator/asyncRendering", False)
        carb.settings.get_settings().set("/app/asyncRendering", False)

        # Set camera sensors fStop to 0.0 to get well lit sharp images
        left_camera_prim = self._stage.GetPrimAtPath(self.LEFT_CAMERA_PATH)
        left_camera_prim.GetAttribute("fStop").Set(0.0)
        right_camera_prim = self._stage.GetPrimAtPath(self.RIGHT_CAMERA_PATH)
        right_camera_prim.GetAttribute("fStop").Set(0.0)

        self._writer = rep.WriterRegistry.get("BasicWriter")
        self._writer.initialize(output_dir=self._out_dir, rgb=True)
        self._setup_sdg_render_products()

    def _setup_sdg_render_products(self):
        print(f"[NavSDGDemo] Creating SDG render products")
        rp_left = rep.create.render_product(
            self.LEFT_CAMERA_PATH,
            (1024, 1024),
            name="left_sensor",
            force_new=True,
        )
        rp_right = rep.create.render_product(
            self.RIGHT_CAMERA_PATH,
            (1024, 1024),
            name="right_sensor",
            force_new=True,
        )
        self._render_products = [rp_left, rp_right]
        # For better performance the render products can be disabled when not in use, and re-enabled only during SDG
        if self._use_temp_rp:
            self._disable_render_products()
        self._writer.attach(self._render_products)
        rep.orchestrator.preview()

    def _clear_sdg_render_products(self):
        print(f"[NavSDGDemo] Clearing SDG render products")
        if self._writer:
            self._writer.detach()
        for rp in self._render_products:
            rp.destroy()
        self._render_products.clear()
        if self._stage.GetPrimAtPath("/Replicator"):
            omni.kit.commands.execute("DeletePrimsCommand", paths=["/Replicator"])

    def _enable_render_products(self):
        print(f"[NavSDGDemo] Enabling render products for SDG..")
        for rp in self._render_products:
            rp.hydra_texture.set_updates_enabled(True)

    def _disable_render_products(self):
        print(f"[NavSDGDemo] Disabling render products (enabled only during SDG)..")
        for rp in self._render_products:
            rp.hydra_texture.set_updates_enabled(False)

    def _run_sdg(self):
        if self._use_temp_rp:
            self._enable_render_products()
        rep.orchestrator.step(rt_subframes=16)
        if self._use_temp_rp:
            self._disable_render_products()

    async def _run_sdg_async(self):
        if self._use_temp_rp:
            self._enable_render_products()
        await rep.orchestrator.step_async(rt_subframes=16)
        if self._use_temp_rp:
            self._disable_render_products()

    def _load_next_env(self):
        if self._stage.GetPrimAtPath("/Environment"):
            omni.kit.commands.execute("DeletePrimsCommand", paths=["/Environment"])
        assets_root_path = get_assets_root_path()
        add_reference_to_stage(usd_path=assets_root_path + next(self._cycled_env_urls), prim_path="/Environment")

    def _on_sdg_done(self, task):
        self._setup_next_frame()

    def _setup_next_frame(self):
        self._frame_counter += 1
        if self._frame_counter >= self._num_frames:
            print(f"[NavSDGDemo] Finished")
            # Make sure the data has been written to disk before clearing the state
            if self._is_running_in_script_editor():
                import asyncio

                task = asyncio.ensure_future(rep.orchestrator.wait_until_complete_async())
                task.add_done_callback(lambda t: self.clear())
            else:
                rep.orchestrator.wait_until_complete()
                self.clear()
            return

        self._randomize_dolly_pose()
        self._randomize_dolly_light()
        self._randomize_prop_poses()
        if self._frame_counter % self._env_interval == 0:
            self._load_next_env()
        # Set a new random distance from which to take capture the next frame
        self._trigger_distance = random.uniform(1.75, 2.5)
        self._timeline.play()
        self._timeline_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
            int(omni.timeline.TimelineEventType.CURRENT_TIME_TICKED), self._on_timeline_event
        )

    def _on_timeline_event(self, e: carb.events.IEvent):
        carter_loc = self._carter_chassis.GetAttribute("xformOp:translate").Get()
        dolly_loc = self._dolly.GetAttribute("xformOp:translate").Get()
        dist = (Gf.Vec2f(dolly_loc[0], dolly_loc[1]) - Gf.Vec2f(carter_loc[0], carter_loc[1])).GetLength()
        if dist < self._trigger_distance:
            print(f"[NavSDGDemo] Starting SDG for frame no. {self._frame_counter}")
            self._timeline.pause()
            self._timeline_sub.unsubscribe()
            if self._is_running_in_script_editor():
                import asyncio

                task = asyncio.ensure_future(self._run_sdg_async())
                task.add_done_callback(self._on_sdg_done)
            else:
                self._run_sdg()
                self._setup_next_frame()


ENV_URLS = [
    "/Isaac/Environments/Grid/default_environment.usd",
    "/Isaac/Environments/Simple_Warehouse/warehouse.usd",
    "/Isaac/Environments/Grid/gridroom_black.usd",
]

parser = argparse.ArgumentParser()
parser.add_argument("--use_temp_rp", action="store_true", help="Create and destroy render products for each SDG frame")
parser.add_argument("--num_frames", type=int, default=9, help="The number of frames to capture")
parser.add_argument("--env_interval", type=int, default=3, help="Interval at which to change the environments")
args, unknown = parser.parse_known_args()

out_dir = os.path.join(os.getcwd(), "_out_nav_sdg_demo", "")
nav_demo = NavSDGDemo()
nav_demo.start(
    num_frames=args.num_frames,
    out_dir=out_dir,
    env_urls=ENV_URLS,
    env_interval=args.env_interval,
    use_temp_rp=args.use_temp_rp,
    seed=22,
)

while simulation_app.is_running() and nav_demo.is_running():
    simulation_app.update()

simulation_app.close()
