# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from omni.ui import color as cl

# Use same context menu style with content browser
cl.context_menu_background = cl.shade(cl("#343432"))
cl.context_menu_separator = cl.shade(0x449E9E9E)
cl.context_menu_text = cl.shade(cl("#9E9E9E"))

CONTEXT_MENU_STYLE = {
    "Menu": {"background_color": cl.context_menu_background_color, "color": cl.context_menu_text, "border_radius": 2},
    "Menu.Item": {"background_color": 0x0, "margin": 0},
    "Separator": {"background_color": 0x0, "color": cl.context_menu_separator},
}
