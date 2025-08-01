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

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import argparse

import carb
import numpy as np
import omni.appwindow  # Contains handle to keyboard
from isaacsim.core.api import World
from isaacsim.core.utils.prims import define_prim, get_prim_at_path
from isaacsim.robot.policy.examples.robots import H1FlatTerrainPolicy
from isaacsim.storage.native import get_assets_root_path

parser = argparse.ArgumentParser(description="Define the number of robots.")
parser.add_argument("--num-robots", type=int, default=1, help="Number of robots (default: 1)")
parser.add_argument(
    "--env-url",
    default="/Isaac/Environments/Grid/default_environment.usd",
    required=False,
    help="Path to the environment url",
)
args = parser.parse_args()
print(f"Number of robots: {args.num_robots}")

first_step = True
reset_needed = False
robots = []


# initialize robot on first step, run robot advance
def on_physics_step(step_size) -> None:
    global first_step
    global reset_needed
    if first_step:
        for robot in robots:
            robot.initialize()
        first_step = False
    elif reset_needed:
        my_world.reset(True)
        reset_needed = False
        first_step = True
    else:
        for robot in robots:
            robot.forward(step_size, base_command)


# spawn world
my_world = World(stage_units_in_meters=1.0, physics_dt=1 / 200, rendering_dt=8 / 200)
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")

# spawn warehouse scene
prim = define_prim("/World/Ground", "Xform")
asset_path = assets_root_path + args.env_url
prim.GetReferences().AddReference(asset_path)

# spawn robot
for i in range(0, args.num_robots):
    h1 = H1FlatTerrainPolicy(
        prim_path="/World/H1_" + str(i),
        name="H1_" + str(i),
        usd_path=assets_root_path + "/Isaac/Robots/Unitree/H1/h1.usd",
        position=np.array([0, i, 1.05]),
    )

    robots.append(h1)

my_world.reset()
my_world.add_physics_callback("physics_step", callback_fn=on_physics_step)

# robot command
base_command = np.zeros(3)

i = 0
while simulation_app.is_running():
    my_world.step(render=True)
    if my_world.is_stopped():
        reset_needed = True
    if my_world.is_playing():
        if i >= 0 and i < 80:
            # forward
            base_command = np.array([0.5, 0, 0])
        elif i >= 80 and i < 130:
            # rotate
            base_command = np.array([0.5, 0, 0.5])
        elif i >= 130 and i < 200:
            # side ways
            base_command = np.array([0, 0, 0.5])
        elif i == 200:
            i = 0
        i += 1

simulation_app.close()
