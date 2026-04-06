"""
shaders.py - GLSL shader source code for ModernGL renderer
Contains vertex and fragment shaders for BSP world rendering.
"""

BSP_VERT = """
#version 330 core

// Per-vertex inputs - match the VBO buffer format
in vec3 in_position;    // location 0 - world position
in vec2 in_texcoord;    // location 1 - diffuse texture coordinates
in vec2 in_lm_coord;    // location 2 - lightmap texture coordinates

// Uniforms
uniform mat4 u_proj;    // projection matrix
uniform mat4 u_view;    // view (camera) matrix

// Outputs to fragment shader
out vec2 v_texcoord;
out vec2 v_lm_coord;

void main() {
    gl_Position = u_proj * u_view * vec4(in_position, 1.0);
    v_texcoord = in_texcoord;
    v_lm_coord = in_lm_coord;
}
"""

BSP_FRAG = """
#version 330 core

// Inputs from vertex shader
in vec2 v_texcoord;
in vec2 v_lm_coord;

// Uniforms
uniform sampler2D u_texture;      // diffuse texture (unit 0)
uniform sampler2D u_lightmap;     // lightmap atlas (unit 1)
uniform float u_fullbright;       // 1.0 = full bright (no lightmap multiply), 0.0 = use lightmap

// Output
out vec4 frag_color;

void main() {
    vec4 diffuse = texture(u_texture, v_texcoord);
    vec4 light   = texture(u_lightmap, v_lm_coord);

    // Multiply diffuse by lightmap RGB; mix between full bright and lightmapped
    vec3 lit = diffuse.rgb * mix(light.rgb, vec3(1.0), u_fullbright);
    frag_color = vec4(lit, diffuse.a);

    // Discard nearly-transparent pixels (handles WAL alpha=0 for sky/clip faces)
    if (frag_color.a < 0.05) discard;
}
"""
