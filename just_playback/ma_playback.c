#include "ma_playback.h"


ma_result check_available_playback_devices(Attrs* attrs) 
{
    // count the # of available playback devices

    ma_context context;
    ma_result ma_res = ma_context_init(NULL, 0, NULL, &context);
    if (ma_res != MA_SUCCESS)
    {
        return ma_res;
    }

    else 
    {
        ma_device_info* pPlaybackInfos;
        ma_uint32 playbackCount;
        ma_device_info* pCaptureInfos;
        ma_uint32 captureCount;
        
        ma_res = ma_context_get_devices(&context, &pPlaybackInfos, &playbackCount, &pCaptureInfos, &captureCount);
        attrs->num_playback_devices = playbackCount;

        return ma_res;
    }
}


void init_attrs(Attrs* attrs) 
{
    attrs->deviceConfig                  = ma_device_config_init(ma_device_type_playback);
    attrs->deviceConfig.dataCallback     = audio_stream_callback;
    attrs->deviceConfig.pUserData        = attrs;

    attrs->frame_offset                  = 0;

    attrs->playback_volume               = 1.0;
    attrs->loops_at_end                  = false;

    attrs->frame_offset_modified         = false;
    attrs->audio_stream_ready            = false;
    attrs->audio_stream_active           = false;
    attrs->audio_stream_ended_naturally  = false;
}


ma_result load_file(Attrs* attrs, const char* path_to_file) 
{
    // Open an audio file and read the necessary config needed for getting audio samples
    // from the file.

    ma_result ma_res = ma_decoder_init_file(path_to_file, NULL, &(attrs->decoder));
    
    attrs->deviceConfig.playback.format   = attrs->decoder.outputFormat;
    attrs->deviceConfig.playback.channels = attrs->decoder.outputChannels;
    attrs->deviceConfig.sampleRate        = attrs->decoder.outputSampleRate;
    
    return ma_res;
}


ma_result init_audio_stream(Attrs* attrs)
{
    // Initialize the audio playback device with the config gotten from loading the
    // audio file.

    ma_result ma_res = ma_device_init(NULL, &(attrs->deviceConfig), &(attrs->device));
    attrs->audio_stream_ready = true;
    
    return ma_res;
}


ma_result start_audio_stream(Attrs* attrs)
{
    // start sending audio samples to the audio device

    ma_result ma_res = ma_device_start(&(attrs->device));
    attrs->audio_stream_active = true;

    return ma_res;
}


ma_result stop_audio_stream(Attrs* attrs)
{
    // stop sending audio samples to the audio device

    ma_result ma_res = ma_device_stop(&(attrs->device)); 
    attrs->audio_stream_active = false;
    
    return ma_res;
}


ma_result terminate_audio_stream(Attrs* attrs)
{
    // uninitialize the audio device & audio file decoder

    ma_device_uninit(&(attrs->device));
    ma_result ma_res = ma_decoder_uninit(&(attrs->decoder));

    attrs->frame_offset = 0;
    attrs->audio_stream_ready = false;
    attrs->audio_stream_active = false;
    
    return ma_res;
}


void audio_stream_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount)
{
    // The audio playback device uses this callback for requesting audio samples. It continues making
    // requests regardless of whether or not the decoder has reached the end of the audio file. Reason
    // why Attrs::audio_stream_ended_naturally has to be set so the device can be stopped from the main
    // thread (stopping it here isn't thread safe) 

    Attrs* attrs = (Attrs*)pDevice->pUserData;
    
    if (attrs->frame_offset_modified) 
    {
        // This is to prevent unecessary calls to ma_decoder_seek_to_pcm_frame except when attr->frame_offset
        // is explicitly set 
        ma_decoder_seek_to_pcm_frame(&(attrs->decoder), attrs->frame_offset);
        attrs->frame_offset_modified = false;
    }

    if (&(attrs->decoder) != NULL)
    {
        ma_uint32 num_read_frames = ma_decoder_read_pcm_frames(&(attrs->decoder), pOutput, frameCount);
        attrs->frame_offset += num_read_frames;
        if (num_read_frames < frameCount) 
        {
            // decoder has reached the end of the audio file

            if (attrs->loops_at_end)
            {
                ma_decoder_seek_to_pcm_frame(&(attrs->decoder), 0);
                attrs->frame_offset = 0;
            }

            else
            {
                attrs->audio_stream_active = false;
                attrs->audio_stream_ended_naturally = true;
            }
        }

        (void)pInput;
    }

}


ma_result set_device_volume(Attrs* attrs) 
{
    ma_result ma_res = ma_device_set_master_volume(&(attrs->device), attrs->playback_volume);
    
    return ma_res;
}


ma_result get_device_volume(Attrs* attrs)
{
    float volume;
    ma_result ma_res = ma_device_get_master_volume(&(attrs->device), &volume);
    attrs->playback_volume = volume;

    return volume;
}