#version 330 core

in vec2 tex_uv;

uniform sampler2D sprite_tex;
uniform vec4 blend_color;

out vec4 frag_color;

void main() {
    vec4 texel = texture(sprite_tex, tex_uv);

    if (texel.a < 0.667) discard;

    // Modulate with blend color
    frag_color = texel * blend_color;
}
