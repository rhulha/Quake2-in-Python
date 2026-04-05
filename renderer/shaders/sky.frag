#version 330 core

in vec2 tex_uv;

uniform samplerCube sky_cubemap;

out vec4 frag_color;

void main() {
    // Simple skybox color (placeholder for cubemap sampling)
    frag_color = vec4(0.5, 0.7, 1.0, 1.0);
}
