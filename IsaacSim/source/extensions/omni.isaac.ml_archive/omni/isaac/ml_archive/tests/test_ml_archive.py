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

import omni.kit.test


class TestPipArchive(omni.kit.test.AsyncTestCase):
    # import all packages to make sure dependencies were not missed
    async def test_import_all(self):
        import filelock
        import fsspec
        import mpmath
        import networkx
        import sympy
        import torch
        import torchaudio
        import torchvision

        self.assertIsNotNone(torch)
        self.assertIsNotNone(torchvision)
        self.assertIsNotNone(torchaudio)
        self.assertIsNotNone(filelock)
        self.assertIsNotNone(fsspec)
        self.assertIsNotNone(mpmath)
        self.assertIsNotNone(networkx)
        self.assertIsNotNone(sympy)
