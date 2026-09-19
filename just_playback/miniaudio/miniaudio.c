#define STB_VORBIS_HEADER_ONLY
#include "stb_vorbis.c" 

#define MINIAUDIO_IMPLEMENTATION
#include "miniaudio.h"

/*
Miniaudio's type-safe atomic operations are private to its implementation
translation unit. Export the small subset used by the playback wrapper.
*/
#include "../ma_atomic_bridge.h"


ma_uint64 jp_atomic_uint64_load(ma_atomic_uint64* value)
{
    return ma_atomic_uint64_get(value);
}


void jp_atomic_uint64_store(ma_atomic_uint64* value, ma_uint64 desired)
{
    ma_atomic_uint64_set(value, desired);
}


ma_uint64 jp_atomic_uint64_exchange(ma_atomic_uint64* value, ma_uint64 desired)
{
    return ma_atomic_uint64_exchange(value, desired);
}


ma_uint64 jp_atomic_uint64_fetch_add(ma_atomic_uint64* value, ma_uint64 amount)
{
    return ma_atomic_uint64_fetch_add(value, amount);
}


ma_bool32 jp_atomic_bool32_load(ma_atomic_bool32* value)
{
    return ma_atomic_bool32_get(value);
}


void jp_atomic_bool32_store(ma_atomic_bool32* value, ma_bool32 desired)
{
    ma_atomic_bool32_set(value, desired);
}
