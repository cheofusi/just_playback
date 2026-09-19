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

ma_result check_available_playback_devices(Attrs* attrs);
void init_attrs(Attrs* attrs);
ma_result load_file(Attrs* attrs, const char* path_to_file);
ma_result load_file_w(Attrs* attrs, const wchar_t* path_to_file);
ma_result probe_file(const char* path_to_file);
ma_result probe_file_w(const wchar_t* path_to_file);
bool has_opus_support(void);
const char* get_opus_version_string(void);
ma_result init_audio_stream(Attrs* attrs);
ma_result start_audio_stream(Attrs* attrs);
ma_result stop_audio_stream(Attrs* attrs);
ma_result terminate_audio_stream(Attrs* attrs);
bool is_audio_stream_ready(Attrs* attrs);
ma_result request_audio_stream_seek(Attrs* attrs, ma_uint64 frame_offset);
ma_uint64 get_audio_stream_frame_offset(Attrs* attrs);
ma_result set_audio_stream_looping(Attrs* attrs, bool enabled);
bool is_audio_stream_looping(Attrs* attrs);
bool is_audio_stream_active(Attrs* attrs);
bool did_audio_stream_end_naturally(Attrs* attrs);
void clear_audio_stream_ended_naturally(Attrs* attrs);
void audio_stream_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount);
ma_result set_device_volume(Attrs* attrs);
ma_result get_device_volume(Attrs* attrs);

#endif
