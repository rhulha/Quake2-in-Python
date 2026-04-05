#version 330 core

layout(location = 0) in vec3 pos;
layout(location = 1) in vec2 uv;

uniform mat4 projection;
uniform mat4 view;

out vec2 tex_uv;

void main() {
    gl_Position = projection * view * vec4(pos, 1.0);
    tex_uv = uv;
}
