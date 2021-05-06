#ifndef _MINIAUDIO_PLAYBACK_H
#define _MINIAUDIO_PLAYBACK_H

#include <stdio.h>
#include <stdbool.h>

#include "miniaudio/miniaudio.h"



typedef struct {
    ma_decoder decoder;
    ma_device_config deviceConfig;
    ma_device device;

    ma_uint64 frame_offset;
    bool audio_stream_ready;

    int sample_rate;
    double duration;
    int num_channels;
    
    bool user_seeked;
    bool playback_active;

    int op_errcode;
}
Attrs;


bool check_devices();
void init_attrs(Attrs* attrs);
void init_file_specific_attrs(Attrs* attrs);
bool load_file(Attrs* attrs, const char* path_to_file);
bool init_audio_stream(Attrs* attrs);
bool start_audio_stream(Attrs* attrs);
bool stop_audio_stream(Attrs* attrs);
bool terminate_audio_stream(Attrs* attrs);
void audio_stream_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount);
bool set_device_volume(Attrs* attrs, float volume);
float get_device_volume(Attrs* attrs);

#endif