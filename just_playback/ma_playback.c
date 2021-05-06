#include "ma_playback.h"


bool check_devices() {
    ma_context context;
    ma_result result = ma_context_init(NULL, 0, NULL, &context);
    if (result != MA_SUCCESS) {
        return false;
    }

    ma_device_info* pPlaybackInfos;
    ma_uint32 playbackCount;
    ma_device_info* pCaptureInfos;
    ma_uint32 captureCount;
    result = ma_context_get_devices(&context, &pPlaybackInfos, &playbackCount, &pCaptureInfos, &captureCount);
    if (result != MA_SUCCESS || playbackCount < 1) {
        return false;
    }

    return true;
}


void init_attrs(Attrs* attrs) {
    attrs->deviceConfig              = ma_device_config_init(ma_device_type_playback);
    attrs->deviceConfig.dataCallback = audio_stream_callback;
    attrs->deviceConfig.pUserData    = attrs;

    attrs->frame_offset              = 0;
    attrs->audio_stream_ready        = false;
    attrs->playback_active           = false;

    init_file_specific_attrs(attrs);
}


void init_file_specific_attrs(Attrs* attrs) {
    attrs->sample_rate  = 0;
    attrs->duration     = 0;
    attrs->num_channels = 0;
}

bool load_file(Attrs* attrs, const char* path_to_file) {
    ma_result result = ma_decoder_init_file(path_to_file, NULL, &(attrs->decoder));
    if (result != MA_SUCCESS) {
        attrs->op_errcode = result;
        return false;
    }
    
    attrs->deviceConfig.playback.format   = attrs->decoder.outputFormat;
    attrs->deviceConfig.playback.channels = attrs->decoder.outputChannels;
    attrs->deviceConfig.sampleRate        = attrs->decoder.outputSampleRate;

    attrs->sample_rate = attrs->decoder.outputSampleRate;
    attrs->num_channels = attrs->decoder.outputChannels;
    
    return true;
}

bool init_audio_stream(Attrs* attrs) {
    ma_result result = ma_device_init(NULL, &(attrs->deviceConfig), &(attrs->device));
    if(result != MA_SUCCESS) {
        attrs->op_errcode = result;
        return false;
    }

    attrs->audio_stream_ready = true;
    attrs->frame_offset = 0;
    return true;
}

bool start_audio_stream(Attrs* attrs) {
    ma_result result = ma_device_start(&(attrs->device));
    if (result != MA_SUCCESS) {
        attrs->op_errcode = result;
        return false;
    } 

    attrs->playback_active = true;
    return true;
}

bool stop_audio_stream(Attrs* attrs) {
    ma_result result = ma_device_stop(&(attrs->device)); 
    if (result != MA_SUCCESS) {
        attrs->op_errcode = result;
        return false;
    }

    attrs->playback_active = false;
    return true;
}

bool terminate_audio_stream(Attrs* attrs) {
    ma_device_uninit(&(attrs->device));
    ma_result result = ma_decoder_uninit(&(attrs->decoder));
    if(result != MA_SUCCESS) {
        attrs->op_errcode = result;
        return false;
    }

    init_file_specific_attrs(attrs);
    attrs->audio_stream_ready = false;
    attrs->playback_active = false;
    return true;
}

void audio_stream_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount) {
    Attrs* attrs = (Attrs*)pDevice->pUserData;
    
    if (attrs->user_seeked) {
        // This is to prevent unecessary calls to ma_decoder_seek_to_pcm_frame except when attr->frame_offset
        // is set explicitly 
        ma_decoder_seek_to_pcm_frame(&(attrs->decoder), attrs->frame_offset);
        attrs->user_seeked = false;
    }

    if (&(attrs->decoder) == NULL) {
        return;
    }

    ma_uint32 num_read_frames = ma_decoder_read_pcm_frames(&(attrs->decoder), pOutput, frameCount);
    attrs->frame_offset += num_read_frames;
    if (num_read_frames < frameCount) {
        attrs->playback_active = false;
    }

    (void)pInput;
}

bool set_device_volume(Attrs* attrs, float volume) {
    ma_result result = ma_device_set_master_volume(&(attrs->device), volume);
    if(result != MA_SUCCESS) {
        attrs->op_errcode = result;
        return false;
    }

    return true;
}

float get_device_volume(Attrs* attrs) {
    float volume;
    ma_result result = ma_device_get_master_volume(&(attrs->device), &volume);
     if(result != MA_SUCCESS) {
        attrs->op_errcode = result;
        return -1;
    }

    return volume;
}