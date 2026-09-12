/* Regenerates tests/data/tiny-opus.ogg using the prepared native libraries. */
#include <ogg/ogg.h>
#include <opus/opus.h>

#include <stdint.h>
#include <stdio.h>
#include <string.h>


static void write_u16le(unsigned char* output, uint16_t value)
{
    output[0] = (unsigned char)value;
    output[1] = (unsigned char)(value >> 8);
}


static void write_u32le(unsigned char* output, uint32_t value)
{
    output[0] = (unsigned char)value;
    output[1] = (unsigned char)(value >> 8);
    output[2] = (unsigned char)(value >> 16);
    output[3] = (unsigned char)(value >> 24);
}


static int write_pages(FILE* output, ogg_stream_state* stream, int flush)
{
    ogg_page page;
    int available;

    do {
        available = flush ? ogg_stream_flush(stream, &page) : ogg_stream_pageout(stream, &page);
        if (available) {
            if (
                fwrite(page.header, 1, (size_t)page.header_len, output) != (size_t)page.header_len
                || fwrite(page.body, 1, (size_t)page.body_len, output) != (size_t)page.body_len
            ) {
                return 0;
            }
        }
    } while (available);

    return 1;
}


int main(int argc, char** argv)
{
    const int sample_rate = 48000;
    const int frame_size = 960;
    const char vendor[] = "just_playback test fixture";
    OpusEncoder* encoder;
    ogg_stream_state stream;
    ogg_packet ogg_packet_data;
    opus_int16 pcm[960] = {0};
    unsigned char encoded[4000];
    unsigned char opus_head[19] = {0};
    unsigned char opus_tags[8 + 4 + sizeof(vendor) - 1 + 4];
    int error;
    int lookahead;
    int encoded_size;
    FILE* output;

    if (argc != 2) {
        fprintf(stderr, "usage: %s OUTPUT.opus\n", argv[0]);
        return 2;
    }

    encoder = opus_encoder_create(sample_rate, 1, OPUS_APPLICATION_AUDIO, &error);
    if (encoder == NULL || error != OPUS_OK) {
        fprintf(stderr, "opus_encoder_create failed: %s\n", opus_strerror(error));
        return 1;
    }
    if (opus_encoder_ctl(encoder, OPUS_GET_LOOKAHEAD(&lookahead)) != OPUS_OK) {
        opus_encoder_destroy(encoder);
        return 1;
    }
    encoded_size = opus_encode(encoder, pcm, frame_size, encoded, sizeof(encoded));
    if (encoded_size < 0) {
        fprintf(stderr, "opus_encode failed: %s\n", opus_strerror(encoded_size));
        opus_encoder_destroy(encoder);
        return 1;
    }

    output = fopen(argv[1], "wb");
    if (output == NULL || ogg_stream_init(&stream, 1) != 0) {
        opus_encoder_destroy(encoder);
        return 1;
    }

    memcpy(opus_head, "OpusHead", 8);
    opus_head[8] = 1;
    opus_head[9] = 1;
    write_u16le(opus_head + 10, (uint16_t)lookahead);
    write_u32le(opus_head + 12, (uint32_t)sample_rate);

    memset(&ogg_packet_data, 0, sizeof(ogg_packet_data));
    ogg_packet_data.packet = opus_head;
    ogg_packet_data.bytes = sizeof(opus_head);
    ogg_packet_data.b_o_s = 1;
    ogg_stream_packetin(&stream, &ogg_packet_data);
    if (!write_pages(output, &stream, 1)) {
        return 1;
    }

    memcpy(opus_tags, "OpusTags", 8);
    write_u32le(opus_tags + 8, (uint32_t)(sizeof(vendor) - 1));
    memcpy(opus_tags + 12, vendor, sizeof(vendor) - 1);
    write_u32le(opus_tags + 12 + sizeof(vendor) - 1, 0);
    ogg_packet_data.packet = opus_tags;
    ogg_packet_data.bytes = sizeof(opus_tags);
    ogg_packet_data.b_o_s = 0;
    ogg_packet_data.packetno = 1;
    ogg_stream_packetin(&stream, &ogg_packet_data);
    if (!write_pages(output, &stream, 1)) {
        return 1;
    }

    ogg_packet_data.packet = encoded;
    ogg_packet_data.bytes = encoded_size;
    ogg_packet_data.e_o_s = 1;
    ogg_packet_data.granulepos = lookahead + frame_size;
    ogg_packet_data.packetno = 2;
    ogg_stream_packetin(&stream, &ogg_packet_data);
    if (!write_pages(output, &stream, 1)) {
        return 1;
    }

    ogg_stream_clear(&stream);
    fclose(output);
    opus_encoder_destroy(encoder);
    return 0;
}
