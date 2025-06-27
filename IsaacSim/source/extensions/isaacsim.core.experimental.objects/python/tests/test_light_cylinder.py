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

import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.commands
import omni.kit.test
import warp as wp
from isaacsim.core.experimental.objects import CylinderLight as TargetLight
from isaacsim.core.experimental.prims.tests.common import check_allclose, check_array, draw_indices, draw_sample

from .common import parametrize


async def populate_stage(max_num_prims: int, operation: Literal["wrap", "create"]) -> None:
    # create new stage
    await stage_utils.create_new_stage_async()
    # define prims
    if operation == "wrap":
        for i in range(max_num_prims):
            omni.kit.commands.execute(
                "CreatePrimWithDefaultXform",
                prim_type="CylinderLight",
                prim_path=f"/World/A_{i}",
                attributes={"inputs:intensity": 30000},
                select_new_prim=False,
            )


class TestCylinderLight(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_len(self, prim, num_prims, device, backend):
        self.assertEqual(len(prim), num_prims, f"Invalid len ({num_prims} prims)")

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_are_of_type(self, prim, num_prims, device, backend):
        self.assertFalse(TargetLight.are_of_type("/World").numpy().item())
        self.assertTrue(TargetLight.are_of_type("/World/A_0").numpy().item())
        self.assertTrue(TargetLight.are_of_type(["/World/A_0"]).numpy().item())
        self.assertTrue(TargetLight.are_of_type(prim_utils.get_prim_at_path("/World/A_0")).numpy().item())
        self.assertTrue(TargetLight.are_of_type([prim_utils.get_prim_at_path("/World/A_0")]).numpy().item())

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_lengths(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                prim.set_lengths(v0, indices=indices)
                output = prim.get_lengths(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.float32, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_radii(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.float32):
                prim.set_radii(v0, indices=indices)
                output = prim.get_radii(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.float32, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], prim_classes=[TargetLight], populate_stage_func=populate_stage)
    async def test_enabled_treat_as_lines(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            print(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.bool):
                prim.set_enabled_treat_as_lines(v0, indices=indices)
                output = prim.get_enabled_treat_as_lines(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.bool, device=device)
                check_allclose(expected_v0, output, given=(v0,))
