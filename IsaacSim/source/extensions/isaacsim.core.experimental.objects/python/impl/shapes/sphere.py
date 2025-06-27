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

from __future__ import annotations

import isaacsim.core.experimental.utils.ops as ops_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import warp as wp
from isaacsim.core.experimental.prims.impl.prim import _MSG_PRIM_NOT_VALID
from pxr import Gf, Usd, UsdGeom

from .shape import Shape


class Sphere(Shape):
    """High level class for creating/wrapping USD Sphere (primitive sphere centered at the origin) prims.

    .. note::

        This class creates or wraps (one of both) USD Sphere prims according to the following rules:

        * If the prim paths exist, a wrapper is placed over the USD Sphere prims.
        * If the prim paths do not exist, USD Sphere prims are created at each path and a wrapper is placed over them.

    Args:
        paths: Single path or list of paths to existing or non-existing (one of both) USD prims.
            Can include regular expressions for matching multiple prims.
        radii: Radii (sphere's radius) (shape ``(N, 1)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        positions: Positions in the world frame (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        translations: Translations in the local frame (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        orientations: Orientations in the world frame (shape ``(N, 4)``, quaternion ``wxyz``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        scales: Scales to be applied to the prims (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        reset_xform_op_properties: Whether to reset the transformation operation attributes of the prims to a standard set.
            See :py:meth:`reset_xform_op_properties` for more details.

    Raises:
        ValueError: If resulting paths are mixed (existing and non-existing prims) or invalid.
        AssertionError: If wrapped prims are not USD Sphere.
        AssertionError: If both positions and translations are specified.

    Example:

    .. code-block:: python

        >>> from isaacsim.core.experimental.objects import Sphere
        >>>
        >>> # given an empty USD stage with the /World Xform prim,
        >>> # create spheres at paths: /World/prim_0, /World/prim_1, and /World/prim_2
        >>> paths = ["/World/prim_0", "/World/prim_1", "/World/prim_2"]
        >>> prims = Sphere(paths)  # doctest: +NO_CHECK
    """

    def __init__(
        self,
        paths: str | list[str],
        *,
        # Sphere
        radii: list | np.ndarray | wp.array | None = None,
        # XformPrim
        positions: list | np.ndarray | wp.array | None = None,
        translations: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        scales: list | np.ndarray | wp.array | None = None,
        reset_xform_op_properties: bool = False,
    ) -> None:
        self._geoms = []
        stage = stage_utils.get_current_stage(backend="usd")
        existent_paths, nonexistent_paths = Shape.resolve_paths(paths)
        # get spheres
        if existent_paths:
            paths = existent_paths
            for path in existent_paths:
                prim = stage.GetPrimAtPath(path)
                assert prim.IsA(UsdGeom.Sphere), f"The wrapped prim at path {path} is not a USD Sphere"
                self._geoms.append(UsdGeom.Sphere(prim))
        # create spheres
        else:
            paths = nonexistent_paths
            for path in nonexistent_paths:
                self._geoms.append(UsdGeom.Sphere.Define(stage, path))
        # initialize base class
        super().__init__(
            paths,
            resolve_paths=False,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            reset_xform_op_properties=reset_xform_op_properties,
        )
        # initialize instance from arguments
        if radii is not None:
            self.set_radii(radii)

    """
    Static methods.
    """

    @staticmethod
    def update_extents(geoms: list[UsdGeom.Sphere]) -> None:
        """Update the gprims' extents.

        Backends: :guilabel:`usd`.

        Args:
            geoms: Geoms to process.
        """
        # USD API
        for geom in geoms:
            value = geom.GetRadiusAttr().Get()
            geom.GetExtentAttr().Set((Gf.Vec3f([-value, -value, -value]), Gf.Vec3f([value, value, value])))

    @staticmethod
    def are_of_type(paths: str | Usd.Prim | list[str | Usd.Prim]) -> wp.array:
        """Check if the prims at the given paths are valid for creating Shape instances of this type.

        Backends: :guilabel:`usd`.

        .. warning::

            Since this method is static, the output is always on the CPU.

        Args:
            paths: Prim paths (or prims) to check for.

        Returns:
            Boolean flags indicating if the prims are valid for creating Shape instances.

        Example:

        .. code-block:: python

            >>> # check if the following prims at paths are valid for creating instances
            >>> result = Sphere.are_of_type(["/World", "/World/prim_0"])
            >>> print(result)
            [False  True]
        """
        stage = stage_utils.get_current_stage(backend="usd")
        return ops_utils.place(
            [
                (stage.GetPrimAtPath(item) if isinstance(item, str) else item).IsA(UsdGeom.Sphere)
                for item in (paths if isinstance(paths, (list, tuple)) else [paths])
            ],
            dtype=wp.bool,
            device="cpu",
        )

    """
    Methods.
    """

    def set_radii(
        self,
        radii: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the radii (sphere's radius) of the prims.

        Backends: :guilabel:`usd`.

        Args:
            radii: Radii (shape ``(N, 1)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set same radii for all prims
            >>> prims.set_radii(radii=[0.1])
            >>>
            >>> # set only the radius for the second prim
            >>> prims.set_radii(radii=[0.2], indices=[1])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = ops_utils.resolve_indices(indices, count=len(self), device="cpu")
        radii = ops_utils.place(radii, device="cpu").numpy().reshape((-1, 1))
        for i, index in enumerate(indices.numpy()):
            geom = self.geoms[index]
            geom.GetRadiusAttr().Set(radii[0 if radii.shape[0] == 1 else i].item())
            self.update_extents([geom])

    def get_radii(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the radii (sphere's radius) of the prims.

        Backends: :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The radii (shape ``(N, 1)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the radii of all prims
            >>> radii = prims.get_radii()
            >>> radii.shape
            (3, 1)
            >>>
            >>> # get the radii of the first and last prims
            >>> radii = prims.get_radii(indices=[0, 2])
            >>> radii.shape
            (2, 1)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = ops_utils.resolve_indices(indices, count=len(self), device="cpu")
        data = np.zeros((indices.shape[0], 1), dtype=np.float32)
        for i, index in enumerate(indices.numpy()):
            data[i][0] = self.geoms[index].GetRadiusAttr().Get()
        return ops_utils.place(data, device=self._device)
