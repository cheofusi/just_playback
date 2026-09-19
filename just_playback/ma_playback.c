#include "ma_playback.h"


static ma_result init_decoder_file(const char* path_to_file, ma_decoder* decoder)
{
    ma_decoder_config decoder_config = ma_decoder_config_init_default();

#ifdef JUST_PLAYBACK_HAS_OPUS
    ma_decoding_backend_vtable* custom_backends[] = {
        ma_decoding_backend_libopus
    };

    decoder_config.ppCustomBackendVTables = custom_backends;
    decoder_config.customBackendCount =
        sizeof(custom_backends) / sizeof(custom_backends[0]);
#endif

    return ma_decoder_init_file(path_to_file, &decoder_config, decoder);
}


static ma_result init_decoder_file_w(const wchar_t* path_to_file, ma_decoder* decoder)
{
    ma_decoder_config decoder_config = ma_decoder_config_init_default();

#ifdef JUST_PLAYBACK_HAS_OPUS
    ma_decoding_backend_vtable* custom_backends[] = {
        ma_decoding_backend_libopus
    };

    decoder_config.ppCustomBackendVTables = custom_backends;
    decoder_config.customBackendCount =
        sizeof(custom_backends) / sizeof(custom_backends[0]);
#endif

    return ma_decoder_init_file_w(path_to_file, &decoder_config, decoder);
}


ma_result check_available_playback_devices(Attrs* attrs) 
{
    // count the # of available playback devices

    if (attrs == NULL)
    {
        return MA_INVALID_ARGS;
    }

    attrs->num_playback_devices = 0;

    ma_context context;
    ma_result ma_res = ma_context_init(NULL, 0, NULL, &context);
    if (ma_res != MA_SUCCESS)
    {
        return ma_res;
    }

    ma_device_info* pPlaybackInfos = NULL;
    ma_uint32 playbackCount = 0;
    ma_device_info* pCaptureInfos = NULL;
    ma_uint32 captureCount = 0;

    ma_res = ma_context_get_devices(&context, &pPlaybackInfos, &playbackCount, &pCaptureInfos, &captureCount);
    if (ma_res == MA_SUCCESS)
    {
        attrs->num_playback_devices = playbackCount;
    }

    // the context was only needed for the device count; release it
    ma_context_uninit(&context);

    return ma_res;
}


void init_attrs(Attrs* attrs) 
{
    if (attrs == NULL)
    {
        return;
    }

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

    if (attrs == NULL || path_to_file == NULL)
    {
        return MA_INVALID_ARGS;
    }

    ma_result ma_res = init_decoder_file(path_to_file, &(attrs->decoder));
    if (ma_res != MA_SUCCESS)
    {
        return ma_res;
    }
    
    attrs->deviceConfig.playback.format   = attrs->decoder.outputFormat;
    attrs->deviceConfig.playback.channels = attrs->decoder.outputChannels;
    attrs->deviceConfig.sampleRate        = attrs->decoder.outputSampleRate;
    
    return MA_SUCCESS;
}

ma_result load_file_w(Attrs* attrs, const wchar_t* path_to_file) 
{
    // Open an audio file and read the necessary config needed for getting audio samples
    // from the file.

    if (attrs == NULL || path_to_file == NULL)
    {
        return MA_INVALID_ARGS;
    }

    ma_result ma_res = init_decoder_file_w(path_to_file, &(attrs->decoder));
    if (ma_res != MA_SUCCESS)
    {
        return ma_res;
    }
    
    attrs->deviceConfig.playback.format   = attrs->decoder.outputFormat;
    attrs->deviceConfig.playback.channels = attrs->decoder.outputChannels;
    attrs->deviceConfig.sampleRate        = attrs->decoder.outputSampleRate;
    
    return MA_SUCCESS;
}


ma_result probe_file(const char* path_to_file)
{
    if (path_to_file == NULL) {
        return MA_INVALID_ARGS;
    }

    ma_decoder decoder;
    ma_result ma_res = init_decoder_file(path_to_file, &decoder);
    unsigned char frame[4096];
    ma_uint64 frames_read = 0;

    if (ma_res != MA_SUCCESS) {
        return ma_res;
    }

    if (ma_get_bytes_per_frame(decoder.outputFormat, decoder.outputChannels) > sizeof(frame)) {
        ma_decoder_uninit(&decoder);
        return MA_INVALID_DATA;
    }

    ma_res = ma_decoder_read_pcm_frames(&decoder, frame, 1, &frames_read);
    if (ma_res == MA_SUCCESS && frames_read != 1) {
        ma_res = MA_INVALID_DATA;
    }
    if (ma_res == MA_SUCCESS) {
        ma_res = ma_decoder_seek_to_pcm_frame(&decoder, 0);
    }

    ma_decoder_uninit(&decoder);
    return ma_res;
}


ma_result probe_file_w(const wchar_t* path_to_file)
{
    if (path_to_file == NULL) {
        return MA_INVALID_ARGS;
    }

    ma_decoder decoder;
    ma_result ma_res = init_decoder_file_w(path_to_file, &decoder);
    unsigned char frame[4096];
    ma_uint64 frames_read = 0;

    if (ma_res != MA_SUCCESS) {
        return ma_res;
    }

    if (ma_get_bytes_per_frame(decoder.outputFormat, decoder.outputChannels) > sizeof(frame)) {
        ma_decoder_uninit(&decoder);
        return MA_INVALID_DATA;
    }

    ma_res = ma_decoder_read_pcm_frames(&decoder, frame, 1, &frames_read);
    if (ma_res == MA_SUCCESS && frames_read != 1) {
        ma_res = MA_INVALID_DATA;
    }
    if (ma_res == MA_SUCCESS) {
        ma_res = ma_decoder_seek_to_pcm_frame(&decoder, 0);
    }

    ma_decoder_uninit(&decoder);
    return ma_res;
}


bool has_opus_support(void)
{
#ifdef JUST_PLAYBACK_HAS_OPUS
    return true;
#else
    return false;
#endif
}


ma_result init_audio_stream(Attrs* attrs)
{
    // Initialize the audio playback device with the config gotten from loading the
    // audio file.

    if (attrs == NULL)
    {
        return MA_INVALID_ARGS;
    }

    ma_result ma_res = ma_device_init(NULL, &(attrs->deviceConfig), &(attrs->device));
    if (ma_res == MA_SUCCESS)
    {
        attrs->audio_stream_ready = true;
    }
    
    return ma_res;
}


ma_result start_audio_stream(Attrs* attrs)
{
    // start sending audio samples to the audio device

    if (attrs == NULL)
    {
        return MA_INVALID_ARGS;
    }

    ma_result ma_res = ma_device_start(&(attrs->device));
    if (ma_res == MA_SUCCESS)
    {
        attrs->audio_stream_active = true;
    }

    return ma_res;
}


ma_result stop_audio_stream(Attrs* attrs)
{
    // stop sending audio samples to the audio device

    if (attrs == NULL)
    {
        return MA_INVALID_ARGS;
    }

    ma_result ma_res = ma_device_stop(&(attrs->device)); 
    if (ma_res == MA_SUCCESS)
    {
        attrs->audio_stream_active = false;
    }
    
    return ma_res;
}


ma_result terminate_audio_stream(Attrs* attrs)
{
    // uninitialize the audio device & audio file decoder

    if (attrs == NULL)
    {
        return MA_INVALID_ARGS;
    }

    ma_device_uninit(&(attrs->device));
    ma_result ma_res = ma_decoder_uninit(&(attrs->decoder));

    attrs->frame_offset = 0;
    attrs->audio_stream_ready = false;
    attrs->audio_stream_active = false;
    attrs->audio_stream_ended_naturally = false;
    
    return ma_res;
}


void audio_stream_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount)
{
    // The audio playback device uses this callback to request audio samples. It continues making
    // requests regardless of whether or not the decoder has reached the end of the audio file. Reason
    // why Attrs::audio_stream_ended_naturally has to be set so the device can be stopped from the main
    // thread (stopping it here isn't thread safe) 

    if (pDevice == NULL || pDevice->pUserData == NULL)
    {
        return;
    }

    Attrs* attrs = (Attrs*)pDevice->pUserData;
    ma_uint64 num_read_frames;
    
    if (attrs->frame_offset_modified) 
    {
        // This is to prevent unecessary calls to ma_decoder_seek_to_pcm_frame except when attr->frame_offset
        // is explicitly set 
        ma_decoder_seek_to_pcm_frame(&(attrs->decoder), attrs->frame_offset);
        attrs->frame_offset_modified = false;
    }

    ma_result ma_res = ma_decoder_read_pcm_frames(&(attrs->decoder), pOutput, frameCount, &num_read_frames);
    attrs->frame_offset += num_read_frames;
    if (ma_res == MA_AT_END) 
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


ma_result set_device_volume(Attrs* attrs) 
{
    if (attrs == NULL)
    {
        return MA_INVALID_ARGS;
    }

    ma_result ma_res = ma_device_set_master_volume(&(attrs->device), attrs->playback_volume);
    
    return ma_res;
}


ma_result get_device_volume(Attrs* attrs)
{
    if (attrs == NULL)
    {
        return MA_INVALID_ARGS;
    }

    float volume;
    ma_result ma_res = ma_device_get_master_volume(&(attrs->device), &volume);
    if (ma_res == MA_SUCCESS)
    {
        attrs->playback_volume = volume;
    }

    return ma_res;
}
