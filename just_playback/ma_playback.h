#ifndef _MINIAUDIO_PLAYBACK_H
#define _MINIAUDIO_PLAYBACK_H

#include <stdio.h>
#include <stdbool.h>

#include "miniaudio/miniaudio.h"



typedef struct 
{
    ma_uint32 num_playback_devices;

    ma_decoder decoder;
    ma_device_config deviceConfig;
    ma_device device;

    ma_uint64 frame_offset;
    
    float playback_volume; // persists across multiple file loads
    bool loops_at_end; // persists across multiple file loads
    
    bool frame_offset_modified; // set when some function other than audio_stream_callback modifies frame_offset's value
    bool audio_stream_ready; // true if the audio device has been initialized & is ready to receive audio samples
    bool audio_stream_active; // true if audio samples are being sent to the audio device
    bool audio_stream_ended_naturally; // set when the audio file plays to completion
}
Attrs;


ma_result check_available_playback_devices(Attrs* attrs);
void init_attrs(Attrs* attrs);
ma_result load_file(Attrs* attrs, const char* path_to_file);
ma_result init_audio_stream(Attrs* attrs);
ma_result start_audio_stream(Attrs* attrs);
ma_result stop_audio_stream(Attrs* attrs);
ma_result terminate_audio_stream(Attrs* attrs);
void audio_stream_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount);
ma_result set_device_volume(Attrs* attrs);
ma_result get_device_volume(Attrs* attrs);

#endif