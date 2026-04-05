#version 330 core

layout(location = 0) in vec3 pos;
layout(location = 1) in vec2 uv;
layout(location = 2) in vec2 lm_uv;

uniform mat4 projection;
uniform mat4 view;

out vec2 tex_uv;
out vec2 lm_uv_out;

void main() {
    gl_Position = projection * view * vec4(pos, 1.0);
    tex_uv = uv;
    lm_uv_out = lm_uv;
}
