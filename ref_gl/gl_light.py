"""
gl_light.py - Lighting system for BSP surfaces and entities
Handles lightpoint sampling, dynamic lights, and surface lighting
"""

import struct
import math
from OpenGL.GL import *
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf"])

# ===== Light State =====

dlights = []  # Dynamic lights
light_styles = [[1.0, 1.0, 1.0] for _ in range(64)]  # Light style RGB values


# ===== Entity Lighting =====

def R_LightPoint(position, model=None):
    """
    Sample ambient light at a position in the BSP.
    Returns [r, g, b] color values (0.0-1.0).
    """
    try:
        if not position:
            return [1.0, 1.0, 1.0]  # Default to white if no model

        if not model:
            return [0.5, 0.5, 0.5]  # Default to 50% gray

        # Get the leaf containing this point
        leaf = _find_leaf_at_point(position, model)
        if not leaf:
            return [0.5, 0.5, 0.5]

        # Get light value from leaf
        return _sample_lightmap_at_leaf(leaf, position, model)

    except Exception as e:
        print(f"R_LightPoint error: {e}")
        return [0.5, 0.5, 0.5]


def _find_leaf_at_point(point, model):
    """Find leaf containing a point by traversing BSP tree"""
    try:
        if not model or not hasattr(model, 'nodes') or not model.nodes:
            return None

        node_idx = 0

        # Traverse BSP tree
        while node_idx >= 0 and node_idx < len(model.nodes):
            node = model.nodes[node_idx]

            if not node or 'plane_num' not in node:
                break

            plane_idx = node['plane_num']
            if plane_idx >= len(model.planes):
                break

            plane = model.planes[plane_idx]
            if not plane:
                break

            # Calculate distance from point to plane
            normal = plane.get('normal', [0, 0, 0]) if isinstance(plane, dict) else plane.normal
            dist_val = plane.get('dist', 0) if isinstance(plane, dict) else plane.dist

            distance = (point[0] * normal[0] +
                       point[1] * normal[1] +
                       point[2] * normal[2] - dist_val)

            # Choose child based on point position relative to plane
            children = node.get('children', [0, 0]) if isinstance(node, dict) else node.children
            node_idx = children[0] if distance >= 0 else children[1]

        # Convert negative node index to leaf index
        if node_idx < 0:
            leaf_idx = (-node_idx - 1)
            if hasattr(model, 'leafs') and 0 <= leaf_idx < len(model.leafs):
                return model.leafs[leaf_idx]

        return None

    except Exception as e:
        print(f"_find_leaf_at_point error: {e}")
        return None


def _sample_lightmap_at_leaf(leaf, point, model):
    """Sample lightmap at a point within a leaf"""
    try:
        if not leaf:
            return [0.5, 0.5, 0.5]

        # Get leaf properties
        if isinstance(leaf, dict):
            cluster = leaf.get('cluster', -1)
            lightofs = leaf.get('lightofs', -1)
        else:
            cluster = leaf.cluster if hasattr(leaf, 'cluster') else -1
            lightofs = leaf.lightofs if hasattr(leaf, 'lightofs') else -1

        # Default light if no data
        if cluster < 0 or lightofs < 0:
            return [0.5, 0.5, 0.5]

        # Get lightmap data
        if not hasattr(model, 'lightdata') or not model.lightdata:
            return [0.5, 0.5, 0.5]

        # Read RGB triplet from lightmap
        lightdata = model.lightdata
        if isinstance(lightdata, bytes):
            if lightofs + 3 <= len(lightdata):
                r = lightdata[lightofs] / 255.0
                g = lightdata[lightofs + 1] / 255.0
                b = lightdata[lightofs + 2] / 255.0
                return [r, g, b]

        return [0.5, 0.5, 0.5]

    except Exception as e:
        print(f"_sample_lightmap_at_leaf error: {e}")
        return [0.5, 0.5, 0.5]


def RecursiveLightPoint(node, start, end, model=None):
    """
    Recursively traverse BSP to find light value along a ray.
    Used for more accurate lighting with movement.
    """
    try:
        if not node or not model:
            return [0.5, 0.5, 0.5]

        # Find leaf at end point
        leaf = _find_leaf_at_point(end, model)
        if leaf:
            return _sample_lightmap_at_leaf(leaf, end, model)

        return [0.5, 0.5, 0.5]

    except Exception as e:
        print(f"RecursiveLightPoint error: {e}")
        return [0.5, 0.5, 0.5]


# ===== Dynamic Lights =====

def R_MarkLights(light, bit, node, model=None):
    """Mark surfaces touched by a dynamic light for recalculation"""
    try:
        if not light or not node:
            return

        # TODO: Recursively mark surfaces in BSP that are affected by light
        # This is used for efficient lightmap updating

    except Exception as e:
        print(f"R_MarkLights error: {e}")


def R_RenderDlights():
    """Render visible dynamic lights (halos, coronas)"""
    try:
        if not dlights:
            return

        glColor4f(1.0, 1.0, 1.0, 0.5)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_BLEND)

        for light in dlights:
            if not light:
                continue

            try:
                origin = light.get('origin', [0, 0, 0]) if isinstance(light, dict) else light.origin
                color = light.get('color', [1, 1, 1]) if isinstance(light, dict) else light.color
                intensity = light.get('intensity', 100) if isinstance(light, dict) else light.intensity

                # Draw light halo
                glPushMatrix()
                glTranslatef(origin[0], origin[1], origin[2])

                # Simple sphere of light
                radius = intensity / 100.0
                glColor4f(color[0], color[1], color[2], 0.3)

                # Draw as point sprite
                glBegin(GL_POINTS)
                glVertex3f(0, 0, 0)
                glEnd()

                glPopMatrix()

            except:
                pass

        glDisable(GL_BLEND)

    except Exception as e:
        print(f"R_RenderDlights error: {e}")


def R_RenderDlight(light):
    """Render a single dynamic light"""
    try:
        if not light:
            return

        origin = light.get('origin', [0, 0, 0]) if isinstance(light, dict) else light.origin
        color = light.get('color', [1, 1, 1]) if isinstance(light, dict) else light.color
        intensity = light.get('intensity', 100) if isinstance(light, dict) else light.intensity

        glColor4f(color[0], color[1], color[2], 0.5)
        glBegin(GL_POINTS)
        glVertex3f(origin[0], origin[1], origin[2])
        glEnd()

    except Exception as e:
        print(f"R_RenderDlight error: {e}")


def R_PushDlights():
    """Update dynamic light positions and effects"""
    try:
        # Mark lightmaps that need updating
        for light in dlights:
            if light:
                # TODO: Mark affected surfaces for lightmap updates
                pass

    except Exception as e:
        print(f"R_PushDlights error: {e}")


def R_AddDynamicLights(surf):
    """Add dynamic light effects to a surface"""
    try:
        if not surf or not dlights:
            return 0  # Return lighting flags

        # TODO: Calculate dynamic light contribution to surface

        return 0

    except Exception as e:
        print(f"R_AddDynamicLights error: {e}")
        return 0


def R_SetCacheState(surf):
    """Update cache state for lightmap"""
    try:
        # Mark surface as needing lightmap rebuild
        if isinstance(surf, dict):
            surf['cache_dirty'] = True

    except:
        pass


def R_BuildLightMap(surf, dest, stride):
    """Build lightmap for surface from raw light data"""
    try:
        if not surf:
            return

        # TODO: Build actual lightmap texture
        # For now, just fill with white

        if dest:
            for i in range(0, len(dest), stride):
                if i + 2 < len(dest):
                    dest[i] = 255  # R
                    dest[i + 1] = 255  # G
                    dest[i + 2] = 255  # B

    except Exception as e:
        print(f"R_BuildLightMap error: {e}")


# ===== Light Style Management =====

def R_SetLightStyle(style_idx, rgb):
    """Update light style color"""
    try:
        if 0 <= style_idx < len(light_styles):
            light_styles[style_idx] = [
                float(rgb[0]) / 255.0 if rgb[0] > 1 else float(rgb[0]),
                float(rgb[1]) / 255.0 if rgb[1] > 1 else float(rgb[1]),
                float(rgb[2]) / 255.0 if rgb[2] > 1 else float(rgb[2]),
            ]

    except Exception as e:
        print(f"R_SetLightStyle error: {e}")


def R_GetLightStyle(style_idx):
    """Get current light style color"""
    try:
        if 0 <= style_idx < len(light_styles):
            return light_styles[style_idx]
        return [1.0, 1.0, 1.0]

    except:
        return [1.0, 1.0, 1.0]


# ===== Lighting Utilities =====

def _clamp(value, min_val=0.0, max_val=1.0):
    """Clamp value to range"""
    return max(min_val, min(max_val, value))


def _lerp(a, b, t):
    """Linear interpolation"""
    return a + (b - a) * t


def _vec3_add(a, b):
    """Add two 3D vectors"""
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def _vec3_scale(v, s):
    """Scale 3D vector"""
    return [v[0] * s, v[1] * s, v[2] * s]


def _vec3_normalize(v):
    """Normalize 3D vector"""
    try:
        len_sq = v[0]*v[0] + v[1]*v[1] + v[2]*v[2]
        if len_sq > 0.0001:
            length = math.sqrt(len_sq)
            return [v[0]/length, v[1]/length, v[2]/length]
        return [0, 0, 1]
    except:
        return [0, 0, 1]


# ===== Ambient Light Calculation for Entities =====

def R_LightEntity(entity, model=None):
    """
    Calculate lighting for an entity based on position.
    Returns [r, g, b] color to apply to entity.
    """
    try:
        if not entity:
            return [1.0, 1.0, 1.0]

        # Get entity origin
        origin = entity.origin if hasattr(entity, 'origin') else [0, 0, 0]

        # Sample light at entity position
        light_color = R_LightPoint(origin, model)

        if not light_color:
            light_color = [0.5, 0.5, 0.5]

        # Add dynamic lights contribution
        total_light = [light_color[0], light_color[1], light_color[2]]

        for dlight in dlights:
            if not dlight:
                continue

            try:
                d_origin = dlight.get('origin', [0, 0, 0]) if isinstance(dlight, dict) else dlight.origin
                d_color = dlight.get('color', [1, 1, 1]) if isinstance(dlight, dict) else dlight.color
                d_intensity = dlight.get('intensity', 100) if isinstance(dlight, dict) else dlight.intensity

                # Calculate distance from entity to light
                dx = origin[0] - d_origin[0]
                dy = origin[1] - d_origin[1]
                dz = origin[2] - d_origin[2]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)

                # Calculate light contribution (inverse square law)
                if dist < d_intensity:
                    attenuation = 1.0 - (dist / d_intensity)
                    contribution = (d_intensity / 255.0) * attenuation

                    total_light[0] += d_color[0] * contribution
                    total_light[1] += d_color[1] * contribution
                    total_light[2] += d_color[2] * contribution

            except:
                pass

        # Clamp to [0, 1]
        return [
            _clamp(total_light[0], 0.0, 1.0),
            _clamp(total_light[1], 0.0, 1.0),
            _clamp(total_light[2], 0.0, 1.0),
        ]

    except Exception as e:
        print(f"R_LightEntity error: {e}")
        return [0.5, 0.5, 0.5]


def SetupEntityLighting(entity, model=None):
    """
    Setup OpenGL lighting for entity.
    Called before rendering each entity.
    """
    try:
        light_color = R_LightEntity(entity, model)

        # Apply as vertex color
        glColor3f(light_color[0], light_color[1], light_color[2])

    except Exception as e:
        print(f"SetupEntityLighting error: {e}")
        glColor3f(1.0, 1.0, 1.0)  # Default to white
