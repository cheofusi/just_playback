import os
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
    compiler_args = ["-g1", "-O3", "-ffast-math", "-mtune=native", "-march=native" ]


ffibuilder.cdef( ma_defs + '\n\n'
                """ 
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
                    bool load_file(Attrs* attrs, const char* path_to_file);
                    bool init_audio_stream(Attrs* attrs);
                    bool start_audio_stream(Attrs* attrs);
                    bool stop_audio_stream(Attrs* attrs);
                    bool terminate_audio_stream(Attrs* attrs);
                    bool set_device_volume(Attrs* attrs, float volume);
                    float get_device_volume(Attrs* attrs);
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