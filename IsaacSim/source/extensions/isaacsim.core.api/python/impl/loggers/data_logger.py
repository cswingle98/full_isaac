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
import json
from typing import Callable, Dict, List

from isaacsim.core.api.scenes.scene import Scene
from isaacsim.core.api.tasks.base_task import BaseTask
from isaacsim.core.utils.types import DataFrame


class DataLogger:
    """This class takes care of collecting data as well as reading already saved data in order to replay it for instance."""

    def __init__(self) -> None:
        self._pause = True
        self._data_frames = []
        self._data_frame_logging_func = None

    def add_data(self, data: dict, current_time_step: float, current_time: float) -> None:
        """Adds data to the log

        Args:
            data (dict): Dictionary representing the data to be logged at this time index.
            current_time_step (float): time step corresponding to the data collected.
            current_time (float): time in seconds corresponding to the data collected.
        """
        self._data_frames.append(DataFrame(current_time_step=current_time_step, current_time=current_time, data=data))
        return

    def get_num_of_data_frames(self) -> int:
        """

        Returns:
            int: the number of data frames collected/ retrieved in the data logger.
        """
        return len(self._data_frames)

    def pause(self) -> None:
        """Pauses data collection."""
        self._pause = True
        return

    def start(self) -> None:
        """Resumes/ starts data collection."""
        self._pause = False
        return

    def is_started(self) -> bool:
        """
        Returns:
            bool: True if data collection is started/ resumed. False otherwise.
        """
        return not self._pause

    def reset(self) -> None:
        """Clears the data in the logger."""
        self._pause = True
        self._data_frames = []
        return

    def get_data_frame(self, data_frame_index: int) -> DataFrame:
        """

        Args:
            data_frame_index (int): index of the data frame to retrieve.

        Returns:
            DataFrame: Data Frame collected/ retrieved at the specified data frame index.
        """
        return self._data_frames[data_frame_index]

    def add_data_frame_logging_func(self, func: Callable[[List[BaseTask], Scene], Dict]) -> None:
        """

        Args:
            func (Callable[[list[BaseTask], Scene], None]): function to be called at every step when the logger is started.
                                                            should follow:

                                                            def dummy_data_collection_fn(tasks, scene):
                                                                return {"data 1": [data]}
        """
        self._data_frame_logging_func = func
        return

    def save(self, log_path: str) -> None:
        """
        Saves the current data in the logger to a json file

        Args:
            log_path (str): path of the json file to be used to save the data.
        """
        data = {}
        data["Isaac Sim Data"] = [data_frame.get_dict() for data_frame in self._data_frames]
        with open(log_path, "w") as outfile:
            json.dump(data, outfile)
        return

    def load(self, log_path: str) -> None:
        """Loads data from a json file to read back a previous saved data or to resume recording data from another time step.

        Args:
            log_path (str): path of the json file to be used to load the data.
        """
        self._pause = True
        self._data_frames = []
        self._data_frame_logging_func = None
        with open(log_path) as json_file:
            json_data = json.load(json_file)
            data_frames = json_data["Isaac Sim Data"]
            data_frames = [DataFrame.init_from_dict(dict_representation=data_frame) for data_frame in data_frames]
            self._data_frames = data_frames
        return
