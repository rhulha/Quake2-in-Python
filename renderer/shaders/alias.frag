#version 330 core

in vec2 tex_uv;
in vec4 vert_color;

uniform sampler2D skin_tex;

out vec4 frag_color;

void main() {
    vec4 texel = texture(skin_tex, tex_uv);

    // Apply per-vertex lighting color
    vec4 result = texel * vert_color;

    // Alpha test
    if (result.a < 0.667) discard;

    frag_color = result;
}
