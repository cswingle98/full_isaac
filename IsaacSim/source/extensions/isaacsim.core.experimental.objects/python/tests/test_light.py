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

from typing import Literal

import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.commands
import omni.kit.test
import warp as wp
from isaacsim.core.experimental.objects import (
    CylinderLight,
    DiskLight,
    DistantLight,
    DomeLight,
    Light,
    RectLight,
    SphereLight,
)
from isaacsim.core.experimental.prims.tests.common import check_allclose, check_array, draw_indices, draw_sample

from .common import parametrize

TargetLight = SphereLight


async def populate_stage(max_num_prims: int, operation: Literal["wrap", "create"]) -> None:
    # create new stage
    await stage_utils.create_new_stage_async()
    # define prims
    if operation == "wrap":
        for i in range(max_num_prims):
            omni.kit.commands.execute(
                "CreatePrimWithDefaultXform",
                prim_type="SphereLight",
                prim_path=f"/World/A_{i}",
                attributes={"inputs:intensity": 30000},
                select_new_prim=False,
            )


class TestLight(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    async def test_fetch_instances(self):
        await stage_utils.create_new_stage_async()
        # create lights
        CylinderLight("/World/light_01")
        DiskLight("/World/light_02")
        DistantLight("/World/light_03")
        DomeLight("/World/light_04")
        RectLight("/World/light_05")
        SphereLight("/World/light_06")
        # fetch instances
        instances = Light.fetch_instances(
            [
                "/World",
                "/World/light_01",
                "/World/light_02",
                "/World/light_03",
                "/World/light_04",
                "/World/light_05",
                "/World/light_06",
            ]
        )
        # check
        self.assertEqual(len(instances), 7)
        self.assertIsNone(instances[0])
        self.assertIsInstance(instances[1], CylinderLight)
        self.assertIsInstance(instances[2], DiskLight)
        self.assertIsInstance(instances[3], DistantLight)
        self.assertIsInstance(instances[4], DomeLight)
        self.assertIsInstance(instances[5], RectLight)
        self.assertIsInstance(instances[6], SphereLight)

    # --------------------------------------------------------------------

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_intensities(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                prim.set_intensities(v0, indices=indices)
                output = prim.get_intensities(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.float32, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_exposures(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                prim.set_exposures(v0, indices=indices)
                output = prim.get_exposures(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.float32, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_multipliers(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (v0, expected_v0), (v1, expected_v1) in zip(
                draw_sample(shape=(expected_count, 1), dtype=wp.float32),
                draw_sample(shape=(expected_count, 1), dtype=wp.float32),
            ):
                prim.set_multipliers(v0, v1, indices=indices)
                output = prim.get_multipliers(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.float32, device=device)
                check_allclose((expected_v0, expected_v1), output, given=(v0, v1))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_enabled_normalizations(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.bool):
                prim.set_enabled_normalizations(v0, indices=indices)
                output = prim.get_enabled_normalizations(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.bool, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_enabled_color_temperatures(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.bool):
                prim.set_enabled_color_temperatures(v0, indices=indices)
                output = prim.get_enabled_color_temperatures(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.bool, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_color_temperatures(self, prim, num_prims, device, backend):
        prim.set_enabled_color_temperatures([True])  # enable use of color temperatures
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                prim.set_color_temperatures(v0, indices=indices)
                output = prim.get_color_temperatures(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.float32, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_colors(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 3), dtype=wp.float32):
                prim.set_colors(v0, indices=indices)
                output = prim.get_colors(indices=indices)
                check_array(output, shape=(expected_count, 3), dtype=wp.float32, device=device)
                check_allclose(expected_v0, output, given=(v0,))
