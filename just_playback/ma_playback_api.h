/*
 * Function declarations shared by the native header and CFFI.
 *
 * This file is intentionally a preprocessor-free declaration fragment so
 * build_ffi_module.py can pass it directly to FFI.cdef().
 */

ma_result check_available_playback_devices(Attrs* attrs);
void init_attrs(Attrs* attrs);
ma_result load_file(Attrs* attrs, const char* path_to_file);
ma_result load_file_w(Attrs* attrs, const wchar_t* path_to_file);
ma_result probe_file(const char* path_to_file);
ma_result probe_file_w(const wchar_t* path_to_file);
const char* ma_version_string(void);
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
void audio_stream_callback(
    ma_device* pDevice,
    void* pOutput,
    const void* pInput,
    ma_uint32 frameCount
);
ma_result set_device_volume(Attrs* attrs);
ma_result get_device_volume(Attrs* attrs);
