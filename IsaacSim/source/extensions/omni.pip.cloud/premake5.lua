-- SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
-- http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

local ext = get_current_extension_info()

project_ext(ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "omni", ext.target_dir .. "/omni" },
    { "$root/_build/target-deps/pip_cloud_prebundle", ext.target_dir .. "/pip_prebundle" },
    -- { "$root/_build/target-deps/pip_archive", ext.target_dir.."/pip_archive" },
}
if os.target() == "windows" then
    local currentAbsPath = repo_build.get_abs_path(".")
    repo_build.copy_to_dir(currentAbsPath .. "/pywin32/*.py", ext.target_dir .. "/pip_prebundle/pywin32_system32")
end
