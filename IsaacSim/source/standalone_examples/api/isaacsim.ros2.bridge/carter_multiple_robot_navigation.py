# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument(
    "--environment",
    type=str,
    choices=["hospital", "office"],
    default="hospital",
    help="Choice of navigation environment.",
)
args, _ = parser.parse_known_args()

HOSPITAL_USD_PATH = "/Isaac/Samples/ROS2/Scenario/multiple_robot_carter_hospital_navigation.usd"
OFFICE_USD_PATH = "/Isaac/Samples/ROS2/Scenario/multiple_robot_carter_office_navigation.usd"

if args.environment == "hospital":
    ENV_USD_PATH = HOSPITAL_USD_PATH
elif args.environment == "office":
    ENV_USD_PATH = OFFICE_USD_PATH

import carb
from isaacsim import SimulationApp

CONFIG = {"renderer": "RaytracedLighting", "headless": False}

# Example ROS2 bridge sample demonstrating the manual loading of Multiple Robot Navigation scenario
simulation_app = SimulationApp(CONFIG)
import omni
from isaacsim.core.api import SimulationContext
from isaacsim.core.utils.extensions import enable_extension
from isaacsim.storage.native import get_assets_root_path

# enable ROS2 bridge extension
enable_extension("isaacsim.ros2.bridge")

simulation_app.update()

# Locate assets root folder to load sample
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

usd_path = assets_root_path + ENV_USD_PATH
omni.usd.get_context().open_stage(usd_path, None)

# Wait two frames so that stage starts loading
simulation_app.update()
simulation_app.update()

print("Loading stage...")
from isaacsim.core.utils.stage import is_stage_loading

while is_stage_loading():
    simulation_app.update()
print("Loading Complete")

simulation_context = SimulationContext(stage_units_in_meters=1.0)

simulation_app.update()

simulation_context.play()

simulation_app.update()

while simulation_app.is_running():

    # runs with a realtime clock
    simulation_app.update()

simulation_context.stop()
simulation_app.close()
