#version 330 core

in vec2 tex_uv;
in vec2 lm_uv_out;

uniform sampler2D diffuse_tex;
uniform sampler2D lightmap_tex;

out vec4 frag_color;

void main() {
    vec4 diffuse = texture(diffuse_tex, tex_uv);

    // Discard pixels with low alpha (alpha test: alpha > 0.667)
    if (diffuse.a < 0.667) discard;

    vec4 lightmap = texture(lightmap_tex, lm_uv_out);

    // Modulate diffuse by lightmap (diffuse * lightmap)
    frag_color = diffuse * lightmap;
}
