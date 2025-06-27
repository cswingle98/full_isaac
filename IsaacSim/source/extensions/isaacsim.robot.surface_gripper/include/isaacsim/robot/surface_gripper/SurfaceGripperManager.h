// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once
// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "isaacsim/core/includes/PrimManager.h"
#include "isaacsim/robot/surface_gripper/SurfaceGripperComponent.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Log.h>

#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdContext.h>
#include <physicsSchemaTools/UsdTools.h>
#include <pxr/usd/usdPhysics/scene.h>

#include <map>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace isaacsim
{
namespace robot
{
namespace surface_gripper
{

/**
 * @class SurfaceGripperManager
 * @brief Manager class for handling surface grippers in a scene
 * @details
 * This class manages all surface gripper components in a USD scene,
 * providing functionality to control and monitor gripper states.
 * It processes physics steps to update gripper behaviors.
 */
class SurfaceGripperManager : public isaacsim::core::includes::PrimManagerBase<SurfaceGripperComponent>
{
public:
    /**
     * @brief Constructs a new SurfaceGripperManager
     * @param[in] physXInterface Pointer to the PhysX interface used for physics simulation
     */
    SurfaceGripperManager(omni::physx::IPhysx* physXInterface)
    {
        m_physXInterface = physXInterface;
    }

    /**
     * @brief Destructor for SurfaceGripperManager
     */
    ~SurfaceGripperManager()
    {
        m_components.clear();
    }

    /**
     * @brief Returns a vector of supported component types
     * @return Vector of strings representing supported component types
     */
    virtual std::vector<std::string> getComponentIsAVector() const;

    /**
     * @brief Handles the stop event for all managed grippers
     */
    void onStop();

    /**
     * @brief Handles the addition of a new surface gripper component
     * @param[in] prim The USD primitive representing the gripper to be added
     */
    void onComponentAdd(const pxr::UsdPrim& prim);

    /**
     * @brief Handles changes to a gripper component's properties
     * @param[in] prim The USD primitive whose properties have changed
     */
    virtual void onComponentChange(const pxr::UsdPrim& prim);

    /**
     * @brief Called for each physics step to update all grippers
     * @param[in] dt The time step in seconds
     */
    void onPhysicsStep(const double& dt);

    /**
     * @brief Called when the simulation starts
     */
    void onStart();

    /**
     * @brief Tick function called each frame
     * @param[in] dt The time step in seconds
     */
    virtual void tick(double dt);

    /**
     * @brief Sets the status of a specific gripper
     * @param[in] primPath The USD path of the gripper to control
     * @param[in] status The new status to set ("Open" or "Closed")
     * @return True if the status was set successfully, false otherwise
     */
    bool setGripperStatus(const std::string& primPath, const std::string& status);

    /**
     * @brief Gets the status of a specific gripper
     * @param[in] primPath The USD path of the gripper
     * @return The current status of the gripper or empty string if not found
     */
    std::string getGripperStatus(const std::string& primPath);

    /**
     * @brief Gets all grippers currently managed by this manager
     * @return A vector of prim paths representing all grippers
     */
    std::vector<std::string> getAllGrippers() const;

    /**
     * @brief Gets a specific gripper component by its path
     * @param[in] primPath The USD path of the gripper
     * @return Pointer to the gripper component if found, nullptr otherwise
     */
    SurfaceGripperComponent* getGripper(const std::string& primPath);

    /**
     * @brief Gets a specific gripper component by its USD prim
     * @param[in] prim The USD prim of the gripper
     * @return Pointer to the gripper component if found, nullptr otherwise
     */
    SurfaceGripperComponent* getGripper(const pxr::UsdPrim& prim);


    virtual void initialize(const pxr::UsdStageWeakPtr stage);

private:
    omni::physx::IPhysx* m_physXInterface = nullptr; ///< Pointer to the PhysX interface
    pxr::SdfLayerRefPtr m_gripperLayer; ///< The gripper layer for this gripper
};

} // namespace surface_gripper
} // namespace robot
} // namespace isaacsim
