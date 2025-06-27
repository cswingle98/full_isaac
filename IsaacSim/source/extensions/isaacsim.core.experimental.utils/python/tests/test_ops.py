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

import isaacsim.core.experimental.utils.ops as ops_utils
import numpy as np
import omni.kit.test
import warp as wp


class TestOps(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()
        # ---------------
        # Do custom setUp
        # ---------------
        self.parametrize_device = ["cpu", "cuda:0", None]
        self.parametrize_dtype = [wp.int8, wp.int16, wp.int32, wp.int64, wp.float16, wp.float32, wp.float64, None]
        self.parametrize_dim = [1, 2, 3, 4]

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        # ------------------
        # Do custom tearDown
        # ------------------
        super().tearDown()

    # --------------------------------------------------------------------

    def check_array(
        self,
        a: wp.array | list[wp.array],
        shape: list[int] | None = None,
        dtype: type | None = None,
        device: str | wp.context.Device | None = None,
    ):
        for i, x in enumerate(a if isinstance(a, (list, tuple)) else [a]):
            assert isinstance(x, wp.array), f"[{i}]: {repr(x)} ({type(x)}) is not a Warp array"
            if shape is not None:
                assert tuple(x.shape) == tuple(shape), f"[{i}]: Unexpected shape: expected {shape}, got {x.shape}"
            if dtype is not None:
                assert x.dtype == dtype, f"[{i}]: Unexpected dtype: expected {dtype}, got {x.dtype}"
            if device is not None:
                assert x.device == wp.get_device(device), f"[{i}]: Unexpected device: expected {device}, got {x.device}"

    def check_equal(
        self,
        a: wp.array | np.ndarray | list[wp.array] | list[np.ndarray],
        b: wp.array | np.ndarray | list[wp.array] | list[np.ndarray],
        *,
        given: list | None = None,
    ):
        msg = ""
        a = a if isinstance(a, (list, tuple)) else [a]
        b = b if isinstance(b, (list, tuple)) else [b]
        assert len(a) == len(b), f"Unexpected (check) length: {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            if isinstance(x, wp.array):
                x = x.numpy()
            if isinstance(y, wp.array):
                y = y.numpy()
            if given is not None:
                msg = f"\nGiven ({type(given[i])})\n{given[i]}"
            assert x.shape == y.shape, f"[{i}]: Unexpected shape: expected {x.shape}, got {y.shape}{msg}"
            assert (x == y).all(), f"[{i}]: Unexpected value:\nExpected\n{x}\nGot\n{y}{msg}"

    # --------------------------------------------------------------------

    async def test_place(self):
        for device in self.parametrize_device:
            for dtype in self.parametrize_dtype:
                for dim in self.parametrize_dim:
                    shape = (*([1] * (dim - 1)),) + (5,)
                    # list
                    x = list(range(5))
                    for _ in range(dim - 1):
                        x = [x]
                    output = ops_utils.place(x, dtype=dtype, device=device)
                    self.check_array(output, shape=shape, dtype=dtype, device=device)
                    # NumPy array
                    x = np.arange(5).reshape(*([1] * (dim - 1)), -1)
                    output = ops_utils.place(x, dtype=dtype, device=device)
                    self.check_array(output, shape=shape, dtype=dtype, device=device)
                    # Warp array
                    x = wp.array(x)
                    output = ops_utils.place(x, dtype=dtype, device=device)
                    self.check_array(output, shape=shape, dtype=dtype, device=device)

    async def test_resolve_indices(self):
        for device in self.parametrize_device:
            for dtype in self.parametrize_dtype:
                for dim in self.parametrize_dim:
                    shape = (5,)
                    # list
                    x = list(range(5))
                    for _ in range(dim - 1):
                        x = [x]
                    output = ops_utils.resolve_indices(x, count=5, dtype=dtype, device=device)
                    self.check_array(output, shape=shape, dtype=dtype, device=device)
                    # NumPy array
                    x = np.arange(5).reshape(*([1] * (dim - 1)), -1)
                    output = ops_utils.resolve_indices(x, count=5, dtype=dtype, device=device)
                    self.check_array(output, shape=shape, dtype=dtype, device=device)
                    # Warp array
                    x = wp.array(x)
                    output = ops_utils.resolve_indices(x, count=5, dtype=dtype, device=device)
                    self.check_array(output, shape=shape, dtype=dtype, device=device)

    async def test_broadcast_to(self):
        for device in self.parametrize_device:
            for dtype in self.parametrize_dtype:
                for shape in [(5,), (11, 5), (22, 11, 5), (33, 22, 11, 5)]:
                    for n in (1, 5):
                        x = np.arange(n).reshape(-1)
                        broadcasted = np.broadcast_to(x, shape=shape)
                        # - NumPy array
                        output = ops_utils.broadcast_to(x, shape=shape, dtype=dtype, device=device)
                        self.check_array(output, shape=shape, dtype=dtype, device=device)
                        self.check_equal(broadcasted, output)
                        # - list
                        output = ops_utils.broadcast_to(x.tolist(), shape=shape, dtype=dtype, device=device)
                        self.check_array(output, shape=shape, dtype=dtype, device=device)
                        self.check_equal(broadcasted, output)
                        # - Warp array
                        output = ops_utils.broadcast_to(wp.array(x), shape=shape, dtype=dtype, device=device)
                        self.check_array(output, shape=shape, dtype=dtype, device=device)
                        self.check_equal(broadcasted, output)
