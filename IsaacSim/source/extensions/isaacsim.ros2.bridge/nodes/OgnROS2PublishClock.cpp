// SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/extras/Library.h>

#include <isaacsim/ros2/bridge/Ros2Factory.h>
#include <isaacsim/ros2/bridge/Ros2Node.h>

#include <OgnROS2PublishClockDatabase.h>

using namespace isaacsim::ros2::bridge;

class OgnROS2PublishClock : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
    }

    static bool compute(OgnROS2PublishClockDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishClock>();

        // Spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.isInitialized())
        {
            const GraphContextObj& context = db.abi_context();
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!state.initializeNodeHandle(
                    std::string(nodeObj.iNode->getPrimPath(nodeObj)),
                    collectNamespace(db.inputs.nodeNamespace(),
                                     stage->GetPrimAtPath(pxr::SdfPath(nodeObj.iNode->getPrimPath(nodeObj)))),
                    db.inputs.context()))
            {
                db.logError("Unable to create ROS2 node, please check that namespace is valid");
                return false;
            }
        }

        // Publisher was not valid, create a new one
        if (!state.m_publisher)
        {
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.m_namespaceName, topicName);
            if (!state.m_factory->validateTopicName(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.m_message = state.m_factory->createClockMessage();

            Ros2QoSProfile qos;
            const std::string& qosProfile = db.inputs.qosProfile();
            if (qosProfile.empty())
            {
                qos.depth = db.inputs.queueSize();
            }
            else
            {
                if (!jsonToRos2QoSProfile(qos, qosProfile))
                {
                    return false;
                }
            }

            state.m_publisher = state.m_factory->createPublisher(
                state.m_nodeHandle.get(), fullTopicName.c_str(), state.m_message->getTypeSupportHandle(), qos);
            return true;
        }

        return state.publishClock(db);
    }

    bool publishClock(OgnROS2PublishClockDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishClock>();

        // Check if subscription count is 0
        if (!m_publishWithoutVerification && !state.m_publisher.get()->getSubscriptionCount())
        {
            return false;
        }

        state.m_message->writeData(db.inputs.timeStamp());
        state.m_publisher.get()->publish(state.m_message->getPtr());
        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishClockDatabase::sPerInstanceState<OgnROS2PublishClock>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        m_publisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> m_publisher = nullptr;
    std::shared_ptr<Ros2ClockMessage> m_message = nullptr;
};

REGISTER_OGN_NODE()
