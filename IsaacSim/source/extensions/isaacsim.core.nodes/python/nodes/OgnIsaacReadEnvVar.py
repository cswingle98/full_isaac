# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import numpy
import omni


class OgnIsaacReadEnvVar:
    """
    look for environment variable on OS, and return it.
    """

    @staticmethod
    def compute(db) -> bool:

        # Empty input case:
        if len(db.inputs.envVar) == 0:
            db.outputs.value = ""

        else:
            # Get environment variable
            envv = os.getenv(db.inputs.envVar)

            if envv is None:
                db.outputs.value = ""
            else:
                db.outputs.value = envv

        return True
