#version 330 core

in vec2 tex_uv;
in vec4 vert_color;

uniform sampler2D tex;

out vec4 frag_color;

void main() {
    vec4 texel = texture(tex, tex_uv);
    frag_color = texel * vert_color;
}
