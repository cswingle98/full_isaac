# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from isaacsim import SimulationApp

CONFIG = {"renderer": "RaytracedLighting", "headless": True, "width": 1920, "height": 1080}

if __name__ == "__main__":
    app = SimulationApp(launch_config=CONFIG)

    from isaacsim.core.utils.extensions import enable_extension

    app.update()

    enable_extension("omni.kit.scripting")

    import omni.usd
    from omni.kit.scripting import ApplyScriptingAPICommand
    from pxr import OmniScriptingSchema, Sdf

    async def work():

        # Create new prim and attach python scripting api.
        await omni.usd.get_context().new_stage_async("tmp")
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim("/test")
        ApplyScriptingAPICommand(paths=["/test"]).do()

        # Test
        prim = stage.GetPrimAtPath("/test")
        assert prim.HasAPI(OmniScriptingSchema.OmniScriptingAPI)

    asyncio.run(work())
