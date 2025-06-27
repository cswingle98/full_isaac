# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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


import enum
import os
import typing as tp

import cv2
import numpy as np
import PIL.Image
import yaml

from .types import Point2d

ROS_FREESPACE_THRESH_DEFAULT = 0.196
ROS_OCCUPIED_THRESH_DEFAULT = 0.65

OCCUPANCY_MAP_DEFAULT_Z_MIN = 0.1
OCCUPANCY_MAP_DEFAULT_Z_MAX = 0.62
OCCUPANCY_MAP_DEFAULT_CELL_SIZE = 0.05


class OccupancyMapDataValue(enum.IntEnum):
    UNKNOWN = 0
    FREESPACE = 1
    OCCUPIED = 2

    def ros_image_value(self, negate: bool = False) -> int:

        values = [0, 127, 255]

        if negate:
            values = values[::-1]

        if self == OccupancyMapDataValue.OCCUPIED:
            return values[0]
        elif self == OccupancyMapDataValue.UNKNOWN:
            return values[1]
        else:
            return values[2]


class OccupancyMap:

    ROS_IMAGE_FILENAME = "map.png"
    ROS_YAML_FILENAME = "map.yaml"
    ROS_YAML_TEMPLATE = """
image: {image_filename}
resolution: {resolution}
origin: {origin}
negate: {negate}
occupied_thresh: {occupied_thresh}
free_thresh: {free_thresh}
"""

    def __init__(self, data: np.ndarray, resolution: int, origin: tp.Tuple[int, int, int]):
        self.data = data
        self.resolution = resolution  # meters per pixel
        self.origin = origin  # x, y, yaw.  where (x, y) is the bottom-left of image
        self._width_pixels = data.shape[1]
        self._height_pixels = data.shape[0]

    def freespace_mask(self) -> np.ndarray:
        """Get a binary mask representing the freespace of the occupancy map.

        Returns:
            np.ndarray: The binary mask representing freespace of the occupancy map.
        """
        return self.data == OccupancyMapDataValue.FREESPACE

    def unknown_mask(self) -> np.ndarray:
        """Get a binary mask representing the unknown area of the occupancy map.

        Returns:
            np.ndarray: The binary mask representing unknown area of the occupancy map.
        """
        return self.data == OccupancyMapDataValue.UNKNOWN

    def occupied_mask(self) -> np.ndarray:
        """Get a binary mask representing the occupied area of the occupancy map.

        Returns:
            np.ndarray: The binary mask representing occupied area of the occupancy map.
        """
        return self.data == OccupancyMapDataValue.OCCUPIED

    def ros_image(self, negate: bool = False) -> PIL.Image.Image:
        """Get the ROS image for the occupancy map.

        Args:
            negate (bool, optional): See "negate" in ROS occupancy map documentation. Defaults to False.

        Returns:
            PIL.Image.Image: The ROS image for the occupancy map as a PIL image.
        """
        occupied_mask = self.occupied_mask()
        ros_image = np.zeros(self.occupied_mask().shape, dtype=np.uint8)
        ros_image[occupied_mask] = OccupancyMapDataValue.OCCUPIED.ros_image_value(negate)
        ros_image[self.unknown_mask()] = OccupancyMapDataValue.UNKNOWN.ros_image_value(negate)
        ros_image[self.freespace_mask()] = OccupancyMapDataValue.FREESPACE.ros_image_value(negate)
        ros_image = PIL.Image.fromarray(ros_image)
        return ros_image

    def ros_yaml(self, negate: bool = False) -> str:
        """Get the ROS occupancy map YAML file content.

        Args:
            negate (bool, optional): See "negate" in ROS occupancy map documentation. Defaults to False.

        Returns:
            str: The ROS occupancy map YAML file contents.
        """
        return self.ROS_YAML_TEMPLATE.format(
            image_filename=self.ROS_IMAGE_FILENAME,
            resolution=self.resolution,
            origin=self.origin,
            negate=1 if negate else 0,
            occupied_thresh=ROS_OCCUPIED_THRESH_DEFAULT,
            free_thresh=ROS_FREESPACE_THRESH_DEFAULT,
        )

    def save_ros(self, path: str):
        """Save the occupancy map to a folder in ROS format.

        This method saves both the ROS formatted PNG image, as well
        as the corresponding YAML file.

        Args:
            path (str): The output path to save the occupancy map.
        """
        if not os.path.exists(path):
            os.makedirs(path)
        assert os.path.isdir(path)  # safety check
        self.ros_image().save(os.path.join(path, self.ROS_IMAGE_FILENAME))
        with open(os.path.join(path, self.ROS_YAML_FILENAME), "w") as f:
            f.write(self.ros_yaml())

    @staticmethod
    def from_ros_yaml(ros_yaml_path: str) -> "OccupancyMap":
        """Load an occupancy map from a ROS YAML file.

        This method loads an occupancy map from a ROS yaml file.
        This method looks up the occupancy map image from the
        value specified in the YAML file, and requires that
        the image exists at the specified path.

        Args:
            ros_yaml_path (str): The path to the ROS yaml file.

        Returns:
            _type_: OccupancyMap
        """
        with open(ros_yaml_path, "r") as f:
            yaml_data = yaml.safe_load(f)
        yaml_dir = os.path.dirname(ros_yaml_path)
        image_path = os.path.join(yaml_dir, yaml_data["image"])
        image = PIL.Image.open(image_path).convert("L")
        occupancy_map = OccupancyMap.from_ros_image(
            ros_image=image,
            resolution=yaml_data["resolution"],
            origin=yaml_data["origin"],
            negate=yaml_data["negate"],
            occupied_thresh=yaml_data["occupied_thresh"],
            free_thresh=yaml_data["free_thresh"],
        )
        return occupancy_map

    @staticmethod
    def from_ros_image(
        ros_image: PIL.Image.Image,
        resolution: int,
        origin: tp.Tuple[float, float, float],
        negate: bool = False,
        occupied_thresh: float = ROS_OCCUPIED_THRESH_DEFAULT,
        free_thresh: float = ROS_FREESPACE_THRESH_DEFAULT,
    ) -> "OccupancyMap":
        """Create an occupancy map from a ROS formatted image, and other data.

        This method is intended to be used as a utility by other methods,
        but not necessarily useful for end use cases.

        Args:
            ros_image (PIL.Image.Image): The ROS formatted PIL image.
            resolution (int): The resolution (meter/px) of the occupancy map.
            origin (tp.Tuple[float, float, float]): The origin of the occupancy map in world coordinates.
            negate (bool, optional): See "negate" in ROS occupancy map documentation. Defaults to False.
            occupied_thresh (float, optional): The threshold to consider a value occupied.
                Defaults to ROS_OCCUPIED_THRESH_DEFAULT.
            free_thresh (float, optional): The threshold to consider a value free. Defaults to
                ROS_FREESPACE_THRESH_DEFAULT.

        Returns:
            OccupancyMap: The occupancy map.
        """
        ros_image = ros_image.convert("L")

        free_thresh = free_thresh * 255
        occupied_thresh = occupied_thresh * 255

        data = np.asarray(ros_image)

        if not negate:
            data = 255 - data

        freespace_mask = data < free_thresh
        occupied_mask = data > occupied_thresh

        return OccupancyMap.from_masks(
            freespace_mask=freespace_mask, occupied_mask=occupied_mask, resolution=resolution, origin=origin
        )

    @staticmethod
    def from_masks(
        freespace_mask: np.ndarray, occupied_mask: np.ndarray, resolution: int, origin: tp.Tuple[float, float, float]
    ) -> "OccupancyMap":
        """Creates an occupancy map from binary masks and other data

        This method is intended as a utility by other methods, but not necessarily
        useful for end use cases.

        Args:
            freespace_mask (np.ndarray): Binary mask for the freespace region.
            occupied_mask (np.ndarray): Binary mask for the occupied region.
            resolution (int): The resolution of the map (meters/px).
            origin (tp.Tuple[float, float, float]): The origin of the map in world coordinates.

        Returns:
            OccupancyMap: The occupancy map.
        """

        data = np.zeros(freespace_mask.shape, dtype=np.uint8)
        data[...] = OccupancyMapDataValue.UNKNOWN
        data[freespace_mask] = OccupancyMapDataValue.FREESPACE
        data[occupied_mask] = OccupancyMapDataValue.OCCUPIED

        occupancy_map = OccupancyMap(data=data, resolution=resolution, origin=origin)

        return occupancy_map

    def width_pixels(self) -> int:
        """Get the width of the occupancy map in pixels.

        Returns:
            int: The width in pixels.
        """
        return self._width_pixels

    def height_pixels(self) -> int:
        """Get the height of the occupancy map in pixels.

        Returns:
            int: The height in pixels.
        """
        return self._height_pixels

    def width_meters(self):
        """Get the width of the occupancy map in meters.

        Returns:
            _type_: The width in meters.
        """
        return self.resolution * self.width_pixels()

    def height_meters(self):
        """Get the height of the occupancy map in meters.

        Returns:
            _type_: The height in meters.
        """
        return self.resolution * self.height_pixels()

    def bottom_left_pixel_world_coords(self) -> tp.Tuple[float, float]:
        """Get the world coordinates of the bottom left pixel.

        Returns:
            tp.Tuple[float, float]: The (x, y) world coordinates of the
                bottom left pixel in the occupancy map.
        """
        return (self.origin[0], self.origin[1])

    def top_left_pixel_world_coords(self) -> tp.Tuple[float, float]:
        """Get the world coordinates of the top left pixel.

        Returns:
            tp.Tuple[float, float]: The (x, y) world coordinates of the
                top left pixel in the occupancy map.
        """
        return (self.origin[0], self.origin[1] + self.height_meters())

    def bottom_right_pixel_world_coords(self) -> tp.Tuple[float, float]:
        """Get the world coordinates of the bottom right pixel.

        Returns:
            tp.Tuple[float, float]: The (x, y) world coordinates of the
                bottom right pixel in the occupancy map.
        """
        return (self.origin[0] + self.width_meters(), self.origin[1])

    def top_right_pixel_world_coords(self) -> tp.Tuple[float, float]:
        """Get the world coordinates of the top right pixel.

        Returns:
            tp.Tuple[float, float]: The (x, y) world coordinates of the
                top right pixel in the occupancy map.
        """
        return (self.origin[0] + self.width_meters(), self.origin[1] + self.height_meters())

    def buffered(self, buffer_distance_pixels: int) -> "OccupancyMap":
        """Get a buffered occupancy map by dilating the occupied regions.

        This method buffers (aka: pads / dilates) an occupancy map by dilating
        the occupied regions using a circular mask with the a radius
        specified by "buffer_distance_pixels".

        This is useful for modifying an occupancy map for path planning,
        collision checking, or robot spawning with the simple assumption
        that the robot has a circular collision profile.

        Args:
            buffer_distance_pixels (int): The buffer radius / distance in pixels.

        Returns:
            OccupancyMap: The buffered (aka: dilated / padded) occupancy map.
        """

        buffer_distance_pixels = int(buffer_distance_pixels)

        radius = buffer_distance_pixels
        diameter = radius * 2
        kernel = np.zeros((diameter, diameter), np.uint8)
        cv2.circle(kernel, (radius, radius), radius, 255, -1)
        occupied = self.occupied_mask().astype(np.uint8) * 255
        occupied_dilated = cv2.dilate(occupied, kernel, iterations=1)
        occupied_mask = occupied_dilated == 255
        free_mask = self.freespace_mask()
        free_mask[occupied_mask] = False

        return OccupancyMap.from_masks(
            freespace_mask=free_mask, occupied_mask=occupied_mask, resolution=self.resolution, origin=self.origin
        )

    def buffered_meters(self, buffer_distance_meters: float) -> "OccupancyMap":
        """Get a buffered occupancy map by dilating the occupied regions.

        See OccupancyMap.buffer() for more details.

        Args:
            buffer_distance_meters (int): The buffer radius / distance in pixels.

        Returns:
            OccupancyMap: The buffered (aka: dilated / padded) occupancy map.
        """
        buffer_distance_pixels = int(buffer_distance_meters / self.resolution)
        return self.buffered(buffer_distance_pixels)

    def pixel_to_world(self, point: Point2d):
        """Convert a pixel coordinate to world coordinates.

        Args:
            point (Point2d): The pixel coordinate.

        Returns:
            _type_: The world coordinate.
        """
        # currently doesn't handle rotations
        bot_left = self.bottom_left_pixel_world_coords()
        u = point.x / self.width_pixels()
        v = 1.0 - point.y / self.height_pixels()
        x_world = u * self.width_meters() + bot_left[0]
        y_world = v * self.height_meters() + bot_left[1]
        return Point2d(x=x_world, y=y_world)

    def pixel_to_world_numpy(self, points: np.ndarray):
        """Convert an array of pixel coordinates to world coordinates.

        Args:
            points (np.ndarray): The Nx2 numpy array of pixel coordinates.

        Returns:
            _type_: The Nx2 numpy array of world coordinates.
        """
        bot_left = self.bottom_left_pixel_world_coords()
        u = points[:, 0] / self.width_pixels()
        v = 1.0 - points[:, 1] / self.height_pixels()
        x_world = u * self.width_meters() + bot_left[0]
        y_world = v * self.height_meters() + bot_left[1]
        return np.concatenate([x_world[:, None], y_world[:, None]], axis=-1)

    def world_to_pixel_numpy(self, points: np.ndarray):
        """Convert an array of world coordinates to pixel coordinates.

        Args:
            points (np.ndarray): The Nx2 numpy array of world coordinates.

        Returns:
            _type_: The Nx2 numpy array of pixel coordinates.
        """
        bot_left_world = self.bottom_left_pixel_world_coords()
        u = (points[:, 0] - bot_left_world[0]) / self.width_meters()
        v = 1.0 - (points[:, 1] - bot_left_world[1]) / self.height_meters()
        x_px = u * self.width_pixels()
        y_px = v * self.height_pixels()
        return np.concatenate([x_px[:, None], y_px[:, None]], axis=-1)

    def check_world_point_in_bounds(self, point: Point2d) -> bool:
        """Check if a world coordinate is inside the bounds of the occupancy map.

        Args:
            point (Point2d): The world coordinate.

        Returns:
            bool: True if the coordinate is inside the bounds of
                the occupancy map.  False otherwise.
        """

        pixel = self.world_to_pixel_numpy(np.array([[point.x, point.y]]))
        x_px = int(pixel[0, 0])
        y_px = int(pixel[0, 1])

        if x_px < 0:
            return False
        elif x_px >= self.width_pixels():
            return False
        elif y_px < 0:
            return False
        elif y_px >= self.height_pixels():
            return False

        return True

    def check_world_point_in_freespace(self, point: Point2d) -> bool:
        """Check if a world coordinate is inside the freespace region of the occupancy map

        Args:
            point (Point2d): The world coordinate.

        Returns:
            bool: True if the world coordinate is inside the freespace region of the occupancy map.
                False otherwise.
        """
        if not self.check_world_point_in_bounds(point):
            return False
        pixel = self.world_to_pixel_numpy(np.array([[point.x, point.y]]))
        x_px = int(pixel[0, 0])
        y_px = int(pixel[0, 1])
        freespace = self.freespace_mask()
        return bool(freespace[y_px, x_px])
