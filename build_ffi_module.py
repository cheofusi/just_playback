import os
import platform
from pathlib import Path

from cffi import FFI
ffibuilder = FFI()

ma_defs_path = Path.cwd() / 'just_playback' / 'ma_defs.txt'
with ma_defs_path.open(mode='r') as f:
    ma_defs = f.read()

miniaudio_src = str(Path('just_playback', 'miniaudio', 'miniaudio.c'))
stb_vorbis_src = str(Path('just_playback', 'miniaudio', 'stb_vorbis.c'))
ma_playback_src = str(Path('just_playback', 'ma_playback.c'))
include_dir = str(Path('just_playback'))

libraries = []
compiler_args = []

if os.name == "posix":
    libraries = ["dl", "m", "pthread"]
    compiler_args = ["-g1", "-O3", "-ffast-math"]
    
if platform.system() != "Darwin":
    compiler_args += ["-march=native"]



ffibuilder.cdef( ma_defs + '\n\n'
                """ 
                    typedef struct {  
                        ma_uint32 num_playback_devices;

                        ma_decoder decoder;
                        ma_device_config deviceConfig;
                        ma_device device;

                        ma_uint64 frame_offset;

                        float playback_volume;
                        bool loops_at_end;

                        bool frame_offset_modified;
                        bool audio_stream_ready;
                        bool audio_stream_active;
                        bool audio_stream_ended_naturally;
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
                """)

ffibuilder.set_source("_ma_playback",  
            """ 
                    #include "ma_playback.h"
            """,
            sources=[miniaudio_src, stb_vorbis_src, ma_playback_src], 
            include_dirs=[include_dir],  
            libraries=libraries,
            extra_compile_args=compiler_args,
            define_macros=[
                ("MA_NO_GENERATION", "1")
            ]
            )    

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)