#include "ma_playback.h"
#include <stdlib.h>
#include <string.h>


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
    attrs->playback_speed                = 1.0;
    attrs->loops_at_end                  = false;

    attrs->frame_offset_modified         = false;
    attrs->audio_stream_ready            = false;
    attrs->audio_stream_active           = false;
    attrs->audio_stream_ended_naturally  = false;

    attrs->resampler_initialized         = false; 
    attrs->temp_buffer                   = NULL; 
    attrs->temp_buffer_size              = 0;
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

ma_result load_file_w(Attrs* attrs, const wchar_t* path_to_file) 
{
    // Open an audio file and read the necessary config needed for getting audio samples
    // from the file.

    ma_result ma_res = ma_decoder_init_file_w(path_to_file, NULL, &(attrs->decoder));
    
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
    if (ma_res != MA_SUCCESS) { 
        return ma_res;
    }

    // Initialize resampler if speed is not 1.0 
    if (attrs->playback_speed != 1.0) {
        ma_res = init_resampler(attrs); 
        if (ma_res != MA_SUCCESS) {
            // Clean up device since resampler failed
            ma_device_uninit(&(attrs->device));
            return ma_res;
        }
    }
    
    attrs->audio_stream_ready = true;
    return ma_res;
}

ma_result init_resampler(Attrs *attrs) 
{
    // Initialize the resampler for the audio clip, which controls the speed of 
    // the audio. 

    if (attrs->resampler_initialized) {
        ma_resampler_uninit(&(attrs->resampler), NULL);
        attrs->resampler_initialized = false;
     } 

    // Calculate effective sample rate for speed control 
    ma_uint32 effective_sample_rate = (ma_uint32)(attrs->decoder.outputSampleRate * attrs->playback_speed);

    ma_resampler_config resamplerConfig = ma_resampler_config_init(
        attrs->decoder.outputFormat,
        attrs->decoder.outputChannels,
        effective_sample_rate,           // Input sample rate (modified for speed)
        attrs->deviceConfig.sampleRate,  // Output sample rate (device rate)
        ma_resample_algorithm_linear
    );

    ma_result ma_res = ma_resampler_init(&resamplerConfig, NULL, &(attrs->resampler));
    if (ma_res == MA_SUCCESS) { 
        attrs->resampler_initialized = true;

        // Allocate temporary buffer for resampling 
        attrs->temp_buffer_size = 4096 * attrs->decoder.outputChannels * ma_get_bytes_per_sample(attrs->decoder.outputFormat);
        attrs->temp_buffer = malloc(attrs->temp_buffer_size); 
        if (attrs->temp_buffer == NULL) {
            ma_resampler_uninit(&(attrs->resampler), NULL);
            attrs->resampler_initialized = false; 
            return MA_OUT_OF_MEMORY;
        }
    }

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

    // Clean up resampler 
    if (attrs->resampler_initialized) {
        ma_resampler_uninit(&(attrs->resampler), NULL);
        attrs->resampler_initialized = false;
    }

    // Clean up temporary buffer 
    if (attrs->temp_buffer != NULL) {
        free(attrs->temp_buffer);
        attrs->temp_buffer = NULL; 
        attrs->temp_buffer_size = 0;
    }

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

    Attrs* attrs = (Attrs*)pDevice->pUserData;
    ma_uint64 num_read_frames;
    
    if (attrs->frame_offset_modified) 
    {
        // This is to prevent unecessary calls to ma_decoder_seek_to_pcm_frame except when attr->frame_offset
        // is explicitly set 
        ma_decoder_seek_to_pcm_frame(&(attrs->decoder), attrs->frame_offset);
        attrs->frame_offset_modified = false;
    }

    // Handle speed control 
    if (attrs->playback_speed == 1.0 || !attrs->resampler_initialized) {
        // Normal speed or resampler not available - direct playback 
        ma_result ma_res = ma_decoder_read_pcm_frames(&(attrs->decoder), pOutput, frameCount, &num_read_frames);
        attrs->frame_offset += num_read_frames; 

        if (ma_res == MA_AT_END) {
            handle_end_of_stream(attrs);
        }
    } else {
        handle_speed_controlled_playback(attrs, pOutput, frameCount);
    }

    (void)pInput;
}

void handle_speed_controlled_playback(Attrs* attrs, void *pOutput, ma_uint32 frameCount) 
{
    // Uses the attrs speed value to adjust the resampler to match the new speed. 
    
    // Calculate how many frames we need to read from the decoder 
    // When speed > 1.0, we need more input frames; when speed < 1.0, we need fewer 
    ma_uint32 frames_to_read = (ma_uint32)(frameCount * attrs->playback_speed) + 1; 

    // Ensure we don't exceed our temp buffer size 
    ma_uint32 max_frames = attrs->temp_buffer_size / (attrs->decoder.outputChannels * ma_get_bytes_per_sample(attrs->decoder.outputFormat));
    if (frames_to_read > max_frames) {
        frames_to_read = max_frames;
    }

    ma_uint64 num_read_frames; 
    ma_result ma_res = ma_decoder_read_pcm_frames(&(attrs->decoder), attrs->temp_buffer, frames_to_read, &num_read_frames);

    if (num_read_frames > 0) {
        // Resample the audio
        ma_uint64 output_frames = frameCount; 
        ma_uint64 input_frames_consumed;
        ma_uint64 output_frames_written; 

        ma_result resample_result = ma_resampler_process_pcm_frames(
            &(attrs->resampler),
            attrs->temp_buffer, &num_read_frames,
            pOutput, &output_frames
        );

        attrs->frame_offset += num_read_frames; 

        // If we didn't get enough output frames, fill the rest with silence 
        if (output_frames < frameCount) {
            ma_uint32 remaining_frames = frameCount - (ma_uint32)output_frames; 
            ma_uint32 bytes_per_frame = attrs->decoder.outputChannels * ma_get_bytes_per_sample(attrs->decoder.outputFormat);
            memset((char*)pOutput + (output_frames * bytes_per_frame), 0, remaining_frames * bytes_per_frame);
        }
    } else {
        // No more frames available, fill with silence 
        ma_uint32 bytes_per_frame = attrs->decoder.outputChannels * ma_get_bytes_per_sample(attrs->decoder.outputFormat);
        memset(pOutput, 0, frameCount * bytes_per_frame); 
    }

    if (ma_res == MA_AT_END) {
        handle_end_of_stream(attrs);
    }
}

void handle_end_of_stream(Attrs *attrs)
{
    // handle the end of stream behavior and state
    
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

ma_result set_playback_speed(Attrs *attrs, float speed) 
{
    // Adjust the sampler based on the passed in speed.
    if (speed <= 0.0f) {
        return MA_INVALID_ARGS;
    }

    attrs->playback_speed = speed;

    // If audio stream is ready, reinitialize resampler with new speed 
    if (attrs->audio_stream_ready) {
        if (speed == 1.0f) {
            // Normal speed - uninitialize resampler if it exists 
            if (attrs->resampler_initialized) {
                ma_resampler_uninit(&(attrs->resampler), NULL);
                attrs->resampler_initialized = false; 

                if (attrs->temp_buffer != NULL) {
                    free(attrs->temp_buffer);
                    attrs->temp_buffer = NULL; 
                    attrs->temp_buffer_size = 0;
                }
            }
        } else { 
            // Non-normal speed - initialize or reinitialize resampler 
            return init_resampler(attrs);
        }
    }

    return MA_SUCCESS;
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

    return ma_res;
}
