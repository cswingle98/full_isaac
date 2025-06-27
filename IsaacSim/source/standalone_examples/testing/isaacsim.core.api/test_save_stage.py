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

from isaacsim.core.api import SimulationContext
from isaacsim.core.utils.stage import add_reference_to_stage, save_stage
from isaacsim.storage.native import get_assets_root_path

assets_root_path = get_assets_root_path()
asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
simulation_context = SimulationContext()
add_reference_to_stage(asset_path, "/Franka")
# need to initialize physics getting any articulation..etc
simulation_context.initialize_physics()
simulation_context.play()

simulation_context.step(render=True)

assets_root = get_assets_root_path()
if simulation_context._sim_context_initialized == False:
    raise (ValueError(f"simulation context is not initialized"))
save_stage(assets_root + "/Users/test/save_stage.usd", save_and_reload_in_place=False)
if simulation_context._sim_context_initialized == False:
    raise (ValueError(f"simulation context is not initialized"))
simulation_context.step(render=True)
save_stage(assets_root + "/Users/test/save_stage.usd", save_and_reload_in_place=True)
# this should reload the stage and the context should not be initialized anymore
if simulation_context._sim_context_initialized == True:
    raise (ValueError(f"simulation context should not be initialized"))
simulation_context.stop()
simulation_app.close()
