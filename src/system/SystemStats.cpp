/*
 *
 *    Copyright (c) 2016-2017 Nest Labs, Inc.
 *    All rights reserved.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */

/**
 * @file
 *  This file implements the Weave API to collect statistics
 *  on the state of Weave, Inet and System resources
 */

// Include module header
#include <SystemLayer/SystemStats.h>

// Include common private header
#include "SystemLayerPrivate.h"

// Include local headers
#include <SystemLayer/SystemTimer.h>

#include <string.h>

namespace nl {
namespace Weave {
namespace System {
namespace Stats {

static const Label sStatsStrings[nl::Weave::System::Stats::kNumEntries] =
{
    "SystemLayer_NumPacketBufs",
    "SystemLayer_NumTimersInUse",
#if INET_CONFIG_NUM_RAW_ENDPOINTS
    "InetLayer_NumRawEpsInUse",
#endif
#if INET_CONFIG_NUM_TCP_ENDPOINTS
    "InetLayer_NumTCPEpsInUse",
#endif
#if INET_CONFIG_NUM_UDP_ENDPOINTS
    "InetLayer_NumUDPEpsInUse",
#endif
#if INET_CONFIG_NUM_TUN_ENDPOINTS
    "InetLayer_NumTunEpsInUse",
#endif
#if INET_CONFIG_NUM_DNS_RESOLVERS
    "InetLayer_NumDNSResolversInUse",
#endif
    "ExchangeMgr_NumContextsInUse",
    "ExchangeMgr_NumUMHandlersInUse",
    "ExchangeMgr_NumBindings",
    "MessageLayer_NumConnectionsInUse",
#if WEAVE_CONFIG_ENABLE_SERVICE_DIRECTORY
    "ServiceMgr_NumRequestsInUse",
#endif
    "WDMLegacy_NumViewInUse",
#if WEAVE_CONFIG_WDM_ALLOW_CLIENT_SUBSCRIPTION
    "WDMLegacy_NumSubscribeInUse",
    "WDMLegacy_NumCancelInUse",
#endif // WEAVE_CONFIG_WDM_ALLOW_CLIENT_SUBSCRIPTION
    "WDMLegacy_NumUpdateInUse",
    "WDMLegacy_NumBindingsInUse",
    "WDMLegacy_NumTransactions",
#if WDM_ENABLE_SUBSCRIPTION_PUBLISHER
    "kWDM_NumTraits",
#endif
#if WDM_ENABLE_SUBSCRIPTION_CLIENT
    "kWDM_NumSubscriptionClients",
#endif
#if WDM_ENABLE_SUBSCRIPTION_PUBLISHER
    "kWDM_NumSubscriptionHandlers",
#endif
#if WDM_PUBLISHER_ENABLE_CUSTOM_COMMANDS
    "kWDM_NumCommands",
#endif
};

count_t sResourcesInUse[kNumEntries];
count_t sHighWatermarks[kNumEntries];

const Label *GetStrings(void)
{
    return sStatsStrings;
}

count_t *GetResourcesInUse(void)
{
    return sResourcesInUse;
}

count_t *GetHighWatermarks(void)
{
    return sHighWatermarks;
}

void UpdateSnapshot(Snapshot &aSnapshot)
{
    memcpy(&aSnapshot.mResourcesInUse, &sResourcesInUse, sizeof(aSnapshot.mResourcesInUse));
    memcpy(&aSnapshot.mHighWatermarks, &sHighWatermarks, sizeof(aSnapshot.mHighWatermarks));

    nl::Weave::System::Timer::GetStatistics(aSnapshot.mResourcesInUse[kSystemLayer_NumTimers]);

#if WEAVE_SYSTEM_CONFIG_PROVIDE_STATISTICS
    /*
     * This code has to be compiled out if the feature is not enabled because
     * by default a product won't have LwIP stats enabled either.
     */
#if WEAVE_SYSTEM_CONFIG_USE_LWIP
    aSnapshot.mResourcesInUse[kSystemLayer_NumPacketBufs] = MEMP_STATS_GET(used, MEMP_PBUF_POOL);
    aSnapshot.mHighWatermarks[kSystemLayer_NumPacketBufs] = MEMP_STATS_GET(max, MEMP_PBUF_POOL);
#endif
#endif
}

bool Difference(Snapshot &result, Snapshot &after, Snapshot &before)
{
    int i;
    bool leak = false;

    for (i = 0; i < kNumEntries; i++)
    {
        result.mResourcesInUse[i] = after.mResourcesInUse[i] - before.mResourcesInUse[i];
        result.mHighWatermarks[i] = after.mHighWatermarks[i] - before.mHighWatermarks[i];

        if (result.mResourcesInUse[i] > 0)
        {
            leak = true;
        }
    }

    return leak;
}


} // namespace Stats
} // namespace System
} // namespace Weave
} // namespace nl
