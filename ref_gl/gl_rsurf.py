"""
gl_rsurf.py - OpenGL BSP surface rendering
Renders brush models and BSP surfaces
"""

import struct
from OpenGL.GL import *
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf"])

# ===== Surface Rendering =====

def R_DrawWorld(worldmodel):
    """Draw world geometry"""
    try:
        if not worldmodel:
            return

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glDisable(GL_BLEND)

        # Render all faces
        if hasattr(worldmodel, 'faces') and worldmodel.faces:
            face_count = 0
            for face in worldmodel.faces:
                try:
                    _draw_face(worldmodel, face)
                    face_count += 1
                except:
                    pass

    except Exception as e:
        Com_Printf(f"R_DrawWorld error: {e}\n")


def R_DrawBrushModel(model):
    """Draw brush model (inline models like doors, platforms)"""
    try:
        R_DrawWorld(model)
    except Exception as e:
        Com_Printf(f"R_DrawBrushModel error: {e}\n")


def _draw_face(model, face):
    """Draw a single face"""
    try:
        # Get face geometry
        if not hasattr(face, '__getitem__') or 'num_edges' not in face:
            return

        first_edge = face['first_edge']
        num_edges = face['num_edges']

        if num_edges <= 0:
            return

        # Get vertices
        vertices = []

        if hasattr(model, 'lump_surfedges') and hasattr(model, 'lump_edges') and hasattr(model, 'vertices'):
            # Parse surfedges and edges on the fly
            surfedges = _read_surfedges(model.lump_surfedges, first_edge, num_edges)
            edges = _read_edges(model.lump_edges, surfedges)

            for edge in edges:
                if isinstance(edge, (list, tuple)) and len(edge) >= 1:
                    v_idx = edge[0]
                    if isinstance(v_idx, int) and 0 <= v_idx < len(model.vertices):
                        v = model.vertices[v_idx]
                        vertices.append([float(v[0]), float(v[1]), float(v[2])])

        # Render polygon
        if len(vertices) >= 3:
            glBegin(GL_POLYGON)
            for v in vertices:
                glVertex3f(v[0], v[1], v[2])
            glEnd()

    except Exception as e:
        Com_Printf(f"_draw_face error: {e}\n")


def _read_surfedges(lump_data, offset, count):
    """Read surfedge indices"""
    try:
        surfedges = []
        for i in range(count):
            idx = offset + i
            if idx * 4 + 4 <= len(lump_data):
                se = struct.unpack_from('<i', lump_data, idx * 4)[0]
                surfedges.append(se)
        return surfedges
    except:
        return []


def _read_edges(lump_data, surfedge_indices):
    """Read edges from lump"""
    try:
        edges = []
        for se in surfedge_indices:
            edge_idx = abs(se)
            if edge_idx * 4 + 4 <= len(lump_data):
                v0 = struct.unpack_from('<H', lump_data, edge_idx * 4)[0]
                v1 = struct.unpack_from('<H', lump_data, edge_idx * 4 + 2)[0]
                edges.append([v0 if se >= 0 else v1, v1 if se >= 0 else v0])
        return edges
    except:
        return []


# ===== Lightmap Management =====

lightmap_atlas = None
lightmap_block = None


class LightmapBlock:
    """Lightmap atlas block for efficient rendering"""
    def __init__(self, width=1024, height=1024):
        self.width = width
        self.height = height
        self.data = bytearray(width * height * 4)  # RGBA
        self.next_x = 0
        self.next_y = 0
        self.row_height = 0
        self.tex_id = None

    def allocate(self, width, height):
        """Allocate block in lightmap atlas"""
        if self.next_x + width > self.width:
            # Move to next row
            self.next_x = 0
            self.next_y += self.row_height
            self.row_height = 0

        if self.next_y + height > self.height:
            # Lightmap full, upload and reset
            self.upload()
            self.reset()

        x = self.next_x
        y = self.next_y
        self.next_x += width
        self.row_height = max(self.row_height, height)

        return x, y

    def upload(self):
        """Upload lightmap to GPU"""
        try:
            if self.tex_id is None:
                self.tex_id = glGenTextures(1)

            glBindTexture(GL_TEXTURE_2D, self.tex_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                         self.width, self.height, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE,
                         bytes(self.data))
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        except:
            pass

    def reset(self):
        """Reset block for next allocation"""
        self.data = bytearray(self.width * self.height * 4)
        self.next_x = 0
        self.next_y = 0
        self.row_height = 0


def GL_BeginBuildingLightmaps():
    """Start lightmap building"""
    global lightmap_block
    lightmap_block = LightmapBlock()


def GL_EndBuildingLightmaps():
    """Finish lightmap building"""
    global lightmap_block
    if lightmap_block:
        lightmap_block.upload()


def GL_CreateSurfaceLightmap(surf):
    """Allocate lightmap for surface"""
    try:
        if not lightmap_block:
            GL_BeginBuildingLightmaps()

        # For now, just allocate space (minimal lightmap)
        lm_x, lm_y = lightmap_block.allocate(16, 16)

        # Store lightmap coordinates in surface
        if isinstance(surf, dict):
            surf['lm_x'] = lm_x
            surf['lm_y'] = lm_y

    except Exception as e:
        Com_Printf(f"GL_CreateSurfaceLightmap error: {e}\n")


def R_MarkLeaves():
    """Mark visible leaves using PVS"""
    pass


def R_SetFrustum():
    """Extract frustum planes from matrices"""
    pass


def R_RenderBrushModel(model):
    """Render brush model with fullbright"""
    R_DrawWorld(model)


def DrawGLPoly(poly_verts):
    """Draw a polygon"""
    try:
        if len(poly_verts) < 3:
            return

        glBegin(GL_POLYGON)
        for v in poly_verts:
            glVertex3f(v[0], v[1], v[2])
        glEnd()
    except:
        pass


def DrawTextureChains():
    """Render surfaces grouped by texture"""
    pass


def R_DrawAlphaSurfaces():
    """Draw transparent surfaces"""
    pass


def GL_SubdivideSurface(face):
    """Subdivide large surfaces"""
    pass


def R_BuildLightMap(surf):
    """Build lightmap for surface"""
    pass


def R_BlendLightmaps():
    """Blend lightmaps into surfaces"""
    pass


def GL_RenderLightmappedPoly(surf):
    """Render lightmapped polygon"""
    pass


def R_TextureAnimation(texinfo):
    """Get animated texture frame"""
    try:
        if isinstance(texinfo, dict):
            return texinfo.get('imageindex', 0)
        return 0
    except:
        return 0


def R_ClearSkyBox():
    """Clear skybox"""
    glClearColor(0.5, 0.5, 0.5, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)


def DrawSkyBox():
    """Draw skybox"""
    pass


def R_RecursiveWorldNode(node, refdef):
    """Recursively traverse BSP tree for rendering"""
    pass


def RecursiveLightPoint(node, start, end):
    """Find light value at point"""
    pass
