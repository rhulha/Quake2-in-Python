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
uniform vec3 u_offset;  // world-space displacement (moving submodels: doors)

// Outputs to fragment shader
out vec2 v_texcoord;
out vec2 v_lm_coord;

void main() {
    gl_Position = u_proj * u_view * vec4(in_position + u_offset, 1.0);
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

MD2_VERT = """
#version 330 core

in vec3 in_position;
in vec2 in_texcoord;

uniform mat4 u_proj;
uniform mat4 u_view;
uniform mat4 u_model;

out vec2 v_texcoord;

void main() {
    gl_Position = u_proj * u_view * u_model * vec4(in_position, 1.0);
    v_texcoord = in_texcoord;
}
"""

MD2_FRAG = """
#version 330 core

in vec2 v_texcoord;

uniform sampler2D u_texture;

out vec4 frag_color;

void main() {
    frag_color = texture(u_texture, v_texcoord);
}
"""

PARTICLE_VERT = """
#version 330 core

in vec3 in_position;
in vec2 in_texcoord;
in vec4 in_color;

uniform mat4 u_proj;
uniform mat4 u_view;

out vec2 v_texcoord;
out vec4 v_color;

void main() {
    gl_Position = u_proj * u_view * vec4(in_position, 1.0);
    v_texcoord = in_texcoord;
    v_color = in_color;
}
"""

PARTICLE_FRAG = """
#version 330 core

in vec2 v_texcoord;
in vec4 v_color;

uniform sampler2D u_texture;

out vec4 frag_color;

void main() {
    vec4 texel = texture(u_texture, v_texcoord);
    frag_color = texel * v_color;
    if (frag_color.a < 0.01) discard;
}
"""

# 2D HUD/overlay shader. Vertices are in pixel coordinates (origin top-left,
# y down); u_screen maps them to normalized device coordinates.
HUD_VERT = """
#version 330 core

in vec2 in_position;
in vec2 in_texcoord;

uniform vec2 u_screen;

out vec2 v_texcoord;

void main() {
    vec2 ndc = vec2(in_position.x / u_screen.x * 2.0 - 1.0,
                    1.0 - in_position.y / u_screen.y * 2.0);
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_texcoord = in_texcoord;
}
"""

HUD_FRAG = """
#version 330 core

in vec2 v_texcoord;

uniform sampler2D u_texture;
uniform vec4 u_color;     // modulation / solid-fill color
uniform int u_textured;   // 1 = sample texture, 0 = solid fill

out vec4 frag_color;

void main() {
    vec4 c = u_color;
    if (u_textured == 1)
        c *= texture(u_texture, v_texcoord);
    if (c.a < 0.02) discard;
    frag_color = c;
}
"""
