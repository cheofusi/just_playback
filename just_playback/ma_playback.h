#ifndef _MINIAUDIO_PLAYBACK_H
#define _MINIAUDIO_PLAYBACK_H

#include <stdio.h>
#include <stdbool.h>

#include "miniaudio/miniaudio.h"
#include "ma_atomic_bridge.h"

#ifdef JUST_PLAYBACK_HAS_OPUS
#include "miniaudio/extras/decoders/libopus/miniaudio_libopus.h"
#endif

#define JP_NO_PENDING_FRAME_OFFSET ((ma_uint64)-1)


typedef struct 
{
    ma_uint32 num_playback_devices;

    ma_decoder decoder;
    ma_device_config deviceConfig;
    ma_device device;

    float playback_volume; // persists across multiple file loads

    bool decoder_initialized;
    bool device_initialized;

    ma_atomic_uint64 frame_offset;
    ma_atomic_uint64 pending_frame_offset; // JP_NO_PENDING_FRAME_OFFSET when no seek is queued
    ma_atomic_bool32 loops_at_end; // persists across multiple file loads
    ma_atomic_bool32 audio_stream_active; // true if audio samples are being sent to the audio device
    ma_atomic_bool32 audio_stream_ended_naturally; // set when the audio file plays to completion
}
Attrs;

#include "ma_playback_api.h"

#endif
