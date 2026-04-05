#version 330 core

in vec2 tex_uv;

uniform sampler2D water_tex;

out vec4 frag_color;

void main() {
    vec4 texel = texture(water_tex, tex_uv);

    // Add slight transparency for water
    texel.a *= 0.7;

    if (texel.a < 0.1) discard;

    frag_color = texel;
}
