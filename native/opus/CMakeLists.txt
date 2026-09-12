cmake_minimum_required(VERSION 3.16)
project(just_playback_opus_dependencies LANGUAGES C)

if(NOT DEFINED JUST_PLAYBACK_OPUS_SOURCE_DIR)
    message(FATAL_ERROR "JUST_PLAYBACK_OPUS_SOURCE_DIR is required")
endif()
file(TO_CMAKE_PATH "${JUST_PLAYBACK_OPUS_SOURCE_DIR}" JUST_PLAYBACK_OPUS_SOURCE_DIR)

set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# libogg
set(INSTALL_DOCS OFF CACHE BOOL "" FORCE)
add_subdirectory("${JUST_PLAYBACK_OPUS_SOURCE_DIR}/ogg" ogg)

# libopus. Only the library is needed; programs, tests and training support are not.
set(OPUS_BUILD_PROGRAMS OFF CACHE BOOL "" FORCE)
set(OPUS_BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(OPUS_BUILD_SHARED_LIBRARY OFF CACHE BOOL "" FORCE)
set(OPUS_BUILD_DNN OFF CACHE BOOL "" FORCE)
add_subdirectory("${JUST_PLAYBACK_OPUS_SOURCE_DIR}/opus" opus)

# opusfile 0.12 predates its upstream CMake build. Build only the local-file
# decoder sources; opusurl and its TLS/network dependencies are intentionally
# excluded.
set(OPUSFILE_SOURCE_DIR "${JUST_PLAYBACK_OPUS_SOURCE_DIR}/opusfile")
add_library(opusfile STATIC
    "${OPUSFILE_SOURCE_DIR}/src/info.c"
    "${OPUSFILE_SOURCE_DIR}/src/internal.c"
    "${OPUSFILE_SOURCE_DIR}/src/opusfile.c"
    "${OPUSFILE_SOURCE_DIR}/src/stream.c"
)
target_include_directories(opusfile
    PUBLIC
        "$<BUILD_INTERFACE:${OPUSFILE_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include/opus>"
)
target_link_libraries(opusfile PUBLIC Ogg::ogg Opus::opus)
if(NOT MSVC)
    target_link_libraries(opusfile PUBLIC m)
endif()
install(TARGETS opusfile ARCHIVE DESTINATION lib)
install(FILES "${OPUSFILE_SOURCE_DIR}/include/opusfile.h" DESTINATION include/opus)
