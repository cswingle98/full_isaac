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

import os
from typing import Callable, Literal

import numpy as np
import omni.kit.test
import warp as wp
from isaacsim.core.simulation_manager import SimulationManager


def cprint(message):
    if os.environ.get("ISAACSIM_TEST_VERBOSE", "0").lower() in ["1", "true", "yes"]:
        print(message)


def parametrize(
    *,
    devices: list[Literal["cpu", "cuda"]] = ["cpu", "cuda"],
    backends: list[Literal["usd", "usdrt", "fabric", "tensor"]] = ["usd", "usdrt", "fabric", "tensor"],
    instances: list[Literal["one", "many"]] = ["one", "many"],
    operations: list[Literal["wrap", "create"]] = ["wrap", "create"],
    prim_class: type,
    prim_class_kwargs: dict = {},
    populate_stage_func: Callable[[int, Literal["wrap", "create"]], None],
    populate_stage_func_kwargs: dict = {},
    max_num_prims: int = 5,
):
    def decorator(func):
        async def wrapper(self):
            for device in devices:
                for backend in backends:
                    for instance in instances:
                        for operation in operations:
                            assert backend in ["usd", "usdrt", "fabric", "tensor"], f"Invalid backend: {backend}"
                            assert instance in ["one", "many"], f"Invalid instance: {instance}"
                            assert operation in ["wrap", "create"], f"Invalid operation: {operation}"
                            cprint(
                                f"  |-- device: {device}, backend: {backend}, instance: {instance}, operation: {operation}"
                            )
                            # populate stage
                            await populate_stage_func(max_num_prims, operation, **populate_stage_func_kwargs)
                            # configure simulation manager
                            SimulationManager.set_physics_sim_device(device)
                            # parametrize test
                            if operation == "wrap":
                                paths = "/World/A_0" if instance == "one" else "/World/A_.*"
                            elif operation == "create":
                                paths = (
                                    "/World/A_0"
                                    if instance == "one"
                                    else [f"/World/A_{i}" for i in range(max_num_prims)]
                                )
                            prim = prim_class(paths, **prim_class_kwargs)
                            num_prims = 1 if instance == "one" else max_num_prims
                            # call test method according to backend
                            if backend == "tensor":
                                omni.timeline.get_timeline_interface().play()
                                await omni.kit.app.get_app().next_update_async()
                                await func(self, prim=prim, num_prims=num_prims, device=device, backend=backend)
                                omni.timeline.get_timeline_interface().stop()
                            elif backend in ["usd", "usdrt", "fabric"]:
                                await func(self, prim=prim, num_prims=num_prims, device=device, backend=backend)

        return wrapper

    return decorator


def check_array(
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


def check_lists(a: list, b: list, *, check_value: bool = True, check_type: bool = True, predicate: callable = None):
    assert len(a) == len(b), f"Unexpected length: expected {len(a)}, got {len(b)}"
    for x, y in zip(a, b):
        if check_value:
            if predicate is not None:
                x = predicate(x)
                y = predicate(y)
            assert x == y, f"Unexpected value: expected {x}, got {y}"
        if check_type:
            assert type(x) == type(y), f"Unexpected type: expected {type(x)}, got {type(y)}"


def check_equal(
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


def check_allclose(
    a: wp.array | np.ndarray | list[wp.array] | list[np.ndarray],
    b: wp.array | np.ndarray | list[wp.array] | list[np.ndarray],
    *,
    rtol: float = 1e-03,
    atol: float = 1e-05,
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
        assert np.allclose(
            x, y, rtol=rtol, atol=atol
        ), f"[{i}]: Unexpected value (within tolerance):\nExpected\n{x}\nGot\n{y}{msg}"


def draw_sample(
    *,
    shape: tuple,
    dtype: type,
    types=[list, np.ndarray, wp.array],
    low: int | float = 0.0,
    high: int | float = 1.0,
    normalized: bool = False,
    transform: callable = None,
):
    samples = []
    for _type in types:
        # sample according to dtype
        if dtype is wp.bool:
            sample = np.random.choice([True, False], size=shape).astype(np.bool_)
        elif dtype is wp.int32:
            sample = np.random.randint(low=low, high=high, size=shape).astype(np.int32)
        elif dtype is wp.uint32:
            sample = np.random.randint(low=low, high=high, size=shape).astype(np.uint32)
        elif dtype is wp.float32:
            sample = np.random.uniform(low=low, high=high, size=shape).astype(np.float32)
            if normalized:
                sample = (sample / np.linalg.norm(sample, axis=-1, keepdims=True)).astype(np.float32)
        else:
            raise ValueError(f"Invalid dtype: {dtype}")
        # apply transform if provided
        if transform:
            sample = transform(sample)
        # create single sample and broadcasted sample
        if sample.ndim == 2:
            single_sample = sample[[0]]
        elif sample.ndim == 3:
            single_sample = sample[[0], [0]]
        else:
            raise ValueError(f"Unsupported dimensionality: {sample.ndim}")
        single_sample_broadcasted = np.broadcast_to(single_sample, shape)
        # create samples
        if _type is list:
            samples.append((single_sample.reshape((shape[-1],)).tolist(), single_sample_broadcasted))
            samples.append((single_sample.reshape((1, shape[-1])).tolist(), single_sample_broadcasted))
            samples.append((sample.tolist(), sample))
        elif _type is np.ndarray:
            samples.append((single_sample.reshape((shape[-1],)).copy(), single_sample_broadcasted))
            samples.append((single_sample.reshape((1, shape[-1])).copy(), single_sample_broadcasted))
            samples.append((sample.copy(), sample))
        elif _type is wp.array:
            samples.append((wp.array(single_sample.reshape((shape[-1],)).copy()), single_sample_broadcasted))
            samples.append((wp.array(single_sample.reshape((1, shape[-1])).copy()), single_sample_broadcasted))
            samples.append((wp.array(sample.copy()), sample))
        else:
            raise ValueError(f"Invalid type: {_type}")
    return samples


def draw_choice(*, shape: tuple, choices: list) -> list:
    sample = np.random.choice(np.array(choices, dtype=object).flatten(), size=shape)
    # create single sample and broadcasted sample
    if sample.ndim == 1:
        single_sample = sample[[0]]
    elif sample.ndim == 2:
        single_sample = sample[[0]]
    else:
        raise ValueError(f"Unsupported dimensionality: {sample.ndim}")
    single_sample_broadcasted = np.broadcast_to(single_sample, shape)
    # create samples
    samples = [
        (single_sample.flatten().tolist(), single_sample_broadcasted.tolist()),
        (single_sample.tolist(), single_sample_broadcasted.tolist()),
        (sample.tolist(), sample.tolist()),
    ]
    return samples


def draw_indices(*, count: int, step: int = 2, types=[list, np.ndarray, wp.array, None]):
    indices = list(range(0, count, step))
    indices_list = []
    for _type in types:
        if _type is list:
            indices_list.append((indices[:], len(indices)))
        elif _type is np.ndarray:
            indices_list.append((np.array(indices), len(indices)))
        elif _type is wp.array:
            indices_list.append((wp.array(indices, dtype=wp.int32, device="cpu"), len(indices)))
        elif _type is None:
            indices_list.append((None, count))
    return indices_list
