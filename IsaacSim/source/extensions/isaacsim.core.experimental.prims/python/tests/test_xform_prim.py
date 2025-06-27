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

import carb
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.kit.test
import warp as wp
from isaacsim.core.experimental.prims import XformPrim
from isaacsim.core.experimental.utils.backend import use_backend
from isaacsim.core.simulation_manager import IsaacEvents

from .common import (
    check_allclose,
    check_array,
    check_equal,
    check_lists,
    cprint,
    draw_choice,
    draw_indices,
    draw_sample,
    parametrize,
)


async def populate_stage(max_num_prims: int, operation: Literal["wrap", "create"], **kwargs) -> None:
    assert operation == "wrap", "Other operations except 'wrap' are not supported"
    # create new stage
    await stage_utils.create_new_stage_async()
    # define prims
    stage_utils.define_prim(f"/World", "Xform")
    stage_utils.define_prim(f"/World/PhysicsScene", "PhysicsScene")
    for i in range(max_num_prims):
        stage_utils.define_prim(f"/World/A_{i}", "Xform")
        stage_utils.define_prim(f"/World/A_{i}/B", "Cube")


class TestXformPrim(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    @parametrize(backends=["usd"], operations=["wrap"], prim_class=XformPrim, populate_stage_func=populate_stage)
    async def test_len(self, prim, num_prims, device, backend):
        self.assertEqual(len(prim), num_prims, f"Invalid XformPrim ({num_prims} prims) len")

    @parametrize(backends=["usd"], operations=["wrap"], prim_class=XformPrim, populate_stage_func=populate_stage)
    async def test_visibilities(self, prim, num_prims, device, backend):
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            cprint(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 1), dtype=wp.bool):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_visibilities(v0, indices=indices)
                    output = prim.get_visibilities(indices=indices)
                check_array(output, shape=(expected_count, 1), dtype=wp.bool, device=device)
                check_equal(expected_v0, output, given=(v0,))

    @parametrize(
        backends=["usd", "usdrt", "fabric"],
        operations=["wrap"],
        prim_class=XformPrim,
        populate_stage_func=populate_stage,
    )
    async def test_world_poses(self, prim, num_prims, device, backend):
        # check backend
        if backend in ["usdrt", "fabric"]:
            await omni.kit.app.get_app().next_update_async()
        else:
            prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            cprint(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (v0, expected_v0), (v1, expected_v1) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_world_poses(v0, v1, indices=indices)
                    output = prim.get_world_poses(indices=indices)
                check_array(output[0], shape=(expected_count, 3), dtype=wp.float32, device=device)
                check_array(output[1], shape=(expected_count, 4), dtype=wp.float32, device=device)
                check_allclose((expected_v0, expected_v1), output, given=(v0, v1))

    @parametrize(
        backends=["usd", "usdrt", "fabric"],
        operations=["wrap"],
        prim_class=XformPrim,
        populate_stage_func=populate_stage,
    )
    async def test_local_poses(self, prim, num_prims, device, backend):
        # check backend
        if backend in ["usdrt", "fabric"]:
            await omni.kit.app.get_app().next_update_async()
        else:
            prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            cprint(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (v0, expected_v0), (v1, expected_v1) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_local_poses(v0, v1, indices=indices)
                    output = prim.get_local_poses(indices=indices)
                check_array(output[0], shape=(expected_count, 3), dtype=wp.float32, device=device)
                check_array(output[1], shape=(expected_count, 4), dtype=wp.float32, device=device)
                check_allclose((expected_v0, expected_v1), output, given=(v0, v1))

    @parametrize(
        backends=["usd", "usdrt", "fabric"],
        operations=["wrap"],
        prim_class=XformPrim,
        populate_stage_func=populate_stage,
    )
    async def test_local_scales(self, prim, num_prims, device, backend):
        # check backend
        if backend in ["usdrt", "fabric"]:
            await omni.kit.app.get_app().next_update_async()
        else:
            prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            cprint(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for v0, expected_v0 in draw_sample(shape=(expected_count, 3), dtype=wp.float32):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_local_scales(v0, indices=indices)
                    output = prim.get_local_scales(indices=indices)
                check_array(output, shape=(expected_count, 3), dtype=wp.float32, device=device)
                check_allclose(expected_v0, output, given=(v0,))

    @parametrize(backends=["usd"], operations=["wrap"], prim_class=XformPrim, populate_stage_func=populate_stage)
    async def test_default_state(self, prim, num_prims, device, backend):
        prim.reset_xform_op_properties()
        # test cases
        for indices, expected_count in draw_indices(count=num_prims, step=2):
            cprint(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            for (v0, expected_v0), (v1, expected_v1) in zip(
                draw_sample(shape=(expected_count, 3), dtype=wp.float32),
                draw_sample(shape=(expected_count, 4), dtype=wp.float32, normalized=True),
            ):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.set_default_state(v0, v1, indices=indices)
                    output = prim.get_default_state(indices=indices)
                    prim.reset_to_default_state()
                check_array(output[0], shape=(expected_count, 3), dtype=wp.float32, device=device)
                check_array(output[1], shape=(expected_count, 4), dtype=wp.float32, device=device)
                check_allclose((expected_v0, expected_v1), output, given=(v0, v1))

    @parametrize(backends=["usd"], operations=["wrap"], prim_class=XformPrim, populate_stage_func=populate_stage)
    async def test_visual_materials(self, prim, num_prims, device, backend):
        from isaacsim.core.experimental.materials import OmniGlassMaterial, OmniPbrMaterial, PreviewSurfaceMaterial

        choices = [
            OmniGlassMaterial("/materials/omni_glass"),
            OmniPbrMaterial("/materials/omni_pbr"),
            PreviewSurfaceMaterial("/materials/preview_surface"),
        ]
        # test cases
        # - check the number of applied materials before applying any material
        with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
            output = prim.get_applied_visual_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert number_of_materials == 0, f"No material should have been applied. Applied: {number_of_materials}"
        # - by indices
        for indices, expected_count in draw_indices(count=num_prims, step=2, types=[list, np.ndarray, wp.array]):
            cprint(f"  |    |-- indices: {type(indices).__name__}, expected_count: {expected_count}")
            count = expected_count
            for v0, expected_v0 in draw_choice(shape=(count,), choices=choices):
                with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                    prim.apply_visual_materials(v0, indices=indices)
                    output = prim.get_applied_visual_materials(indices=indices)
                check_lists(expected_v0, output, check_value=False)
        # - check the number of applied materials after applying materials by indices
        with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
            output = prim.get_applied_visual_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert (
            number_of_materials == count
        ), f"{count} materials should have been applied. Applied: {number_of_materials}"
        # - all
        count = num_prims
        for v0, expected_v0 in draw_choice(shape=(count,), choices=choices):
            with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
                prim.apply_visual_materials(v0)
                output = prim.get_applied_visual_materials()
            check_lists(expected_v0, output, check_value=False)
        # - check the number of applied materials after applying materials by all
        with use_backend(backend, raise_on_unsupported=True, raise_on_fallback=True):
            output = prim.get_applied_visual_materials()
        number_of_materials = sum(1 for material in output if material is not None)
        assert (
            number_of_materials == count
        ), f"{count} materials should have been applied. Applied: {number_of_materials}"

    @parametrize(backends=["usd"], operations=["wrap"], prim_class=XformPrim, populate_stage_func=populate_stage)
    async def test_events(self, prim, num_prims, device, backend):
        prim.reset_xform_op_properties()
        # trigger events automatically
        timeline = omni.timeline.get_timeline_interface()
        for _ in range(2):
            timeline.play()
            for _ in range(2):
                await omni.kit.app.get_app().next_update_async()
            timeline.stop()
        # trigger events manually
        event_dispatcher = carb.eventdispatcher.get_eventdispatcher()
        event_dispatcher.dispatch_event(IsaacEvents.PHYSICS_WARMUP.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.SIMULATION_VIEW_CREATED.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.PHYSICS_READY.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.POST_RESET.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.PRIM_DELETION.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.PRE_PHYSICS_STEP.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.POST_PHYSICS_STEP.value, payload={})
        event_dispatcher.dispatch_event(IsaacEvents.TIMELINE_STOP.value, payload={})
