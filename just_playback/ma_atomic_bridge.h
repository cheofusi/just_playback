#ifndef JUST_PLAYBACK_MA_ATOMIC_BRIDGE_H
#define JUST_PLAYBACK_MA_ATOMIC_BRIDGE_H

#include "miniaudio/miniaudio.h"


ma_uint64 jp_atomic_uint64_load(ma_atomic_uint64* value);
void jp_atomic_uint64_store(ma_atomic_uint64* value, ma_uint64 desired);
ma_uint64 jp_atomic_uint64_exchange(ma_atomic_uint64* value, ma_uint64 desired);
ma_uint64 jp_atomic_uint64_fetch_add(ma_atomic_uint64* value, ma_uint64 amount);

ma_bool32 jp_atomic_bool32_load(ma_atomic_bool32* value);
void jp_atomic_bool32_store(ma_atomic_bool32* value, ma_bool32 desired);

#endif
