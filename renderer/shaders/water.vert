#version 330 core

layout(location = 0) in vec3 pos;
layout(location = 1) in vec2 uv;

uniform mat4 projection;
uniform mat4 view;
uniform float time;
uniform float warpsin[256];

out vec2 tex_uv;

void main() {
    // Apply water warp distortion to UV coordinates
    vec2 warped_uv = uv;

    int s_idx = int((uv.y * 0.125 + time) * 40.74) & 255;
    int t_idx = int((uv.x * 0.125 + time) * 40.74) & 255;

    warped_uv.x += warpsin[s_idx] * (1.0/64.0);
    warped_uv.y += warpsin[t_idx] * (1.0/64.0);

    gl_Position = projection * view * vec4(pos, 1.0);
    tex_uv = warped_uv;
}
