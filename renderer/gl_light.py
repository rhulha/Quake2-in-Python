import numpy as np
from typing import Optional, List, Tuple

from .gl_model import Surface, Node, Leaf, Plane, Model
from .gl_rsurf import BLOCK_WIDTH, BLOCK_HEIGHT, LightmapAtlas, LightmapManager

# Maximum dynamic lights per frame (mirrors Quake 2 engine)
MAX_DLIGHTS = 32

# Number of Quake 2 light styles
MAX_LIGHTSTYLES = 256


class DLight:
    """Dynamic point light for a single frame."""

    __slots__ = ('origin', 'color', 'intensity')

    def __init__(self, origin: np.ndarray, color: np.ndarray, intensity: float):
        self.origin    = origin.astype(np.float32)
        self.color     = color.astype(np.float32)
        self.intensity = float(intensity)


class LightSystem:
    """Manages dynamic lights, light-style scales, and lightmap building."""

    def __init__(self, lightmap_manager: LightmapManager):
        self.lm_manager = lightmap_manager

        # Per-frame dynamic lights
        self.dlights: List[DLight] = []

        # Light style scale table (256 entries, float 0..2)
        self.lightstyles: np.ndarray = np.ones(MAX_LIGHTSTYLES, dtype=np.float32)

        # Temp buffer for a single surface lightmap (RGB float)
        self._work_buf: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Light style management
    # ------------------------------------------------------------------

    def update_lightstyles(self, styles: np.ndarray):
        """Update all light style scales from the server.
        styles should be a float32 array of length MAX_LIGHTSTYLES.
        """
        length = min(len(styles), MAX_LIGHTSTYLES)
        self.lightstyles[:length] = styles[:length]

    # ------------------------------------------------------------------
    # Dynamic light registration
    # ------------------------------------------------------------------

    def clear_dlights(self):
        self.dlights.clear()

    def add_dlight(self, origin: np.ndarray, color: np.ndarray, intensity: float):
        if len(self.dlights) < MAX_DLIGHTS:
            self.dlights.append(DLight(origin, color, intensity))

    # ------------------------------------------------------------------
    # BSP dynamic-light marking
    # ------------------------------------------------------------------

    def mark_lights(self, light: DLight, bit: int, node):
        """Recursively mark BSP nodes/leaves whose surfaces are touched by light."""
        if node is None:
            return
        if isinstance(node, Leaf):
            return

        # Distance from light to splitting plane
        plane: Plane = node.plane
        if plane is None:
            return
        dist = float(np.dot(light.origin, plane.normal) - plane.dist)

        if dist > light.intensity:
            self.mark_lights(light, bit, node.children[0])
        elif dist < -light.intensity:
            self.mark_lights(light, bit, node.children[1])
        else:
            self.mark_lights(light, bit, node.children[0])
            self.mark_lights(light, bit, node.children[1])

    def push_dlights(self, world: Model):
        """Mark all world BSP nodes for every active dlight."""
        if not world.nodes:
            return
        root = world.nodes[0]
        for i, dl in enumerate(self.dlights):
            self.mark_lights(dl, 1 << i, root)

    # ------------------------------------------------------------------
    # Entity lighting
    # ------------------------------------------------------------------

    def light_point(self, model: Model, point: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute approximate RGB light at a world-space point.

        Returns (color, direction) where color is a float32 RGB triplet
        and direction is a unit vector pointing toward the dominant source.

        Walks the BSP from the root to find the leaf, then samples the
        nearest surface's raw lightmap.
        """
        color = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        direction = np.array([0.0, 0.0, -1.0], dtype=np.float32)

        if not model.nodes or model.lightdata is None:
            return color, direction

        # Cast a ray straight down from point to world floor
        end = point.copy()
        end[2] -= 2048.0

        rgb = self._recursive_light_point(model, model.nodes[0], point, end)
        if rgb is not None:
            color = rgb

        # Factor in nearby dynamic lights
        for dl in self.dlights:
            diff = dl.origin - point
            dist = np.linalg.norm(diff)
            if dist < dl.intensity:
                scale = (dl.intensity - dist) / dl.intensity
                color = np.clip(color + dl.color * scale, 0.0, 1.0)
                if dist > 0.001:
                    direction = diff / dist

        return color, direction

    def _recursive_light_point(self, model: Model, node, start: np.ndarray,
                                end: np.ndarray) -> Optional[np.ndarray]:
        if isinstance(node, Leaf):
            return None

        plane: Plane = node.plane
        if plane is None:
            return None

        front = np.dot(start, plane.normal) - plane.dist
        back  = np.dot(end,   plane.normal) - plane.dist
        side  = 0 if front >= 0 else 1

        if (front >= 0) == (back >= 0):
            return self._recursive_light_point(model, node.children[side], start, end)

        # Find mid-point where the ray crosses the plane
        frac = front / (front - back)
        mid  = start + frac * (end - start)

        # Try the front side first
        col = self._recursive_light_point(model, node.children[side], start, mid)
        if col is not None:
            return col

        # Check surfaces on this node
        for si in range(node.firstsurface, node.firstsurface + node.numsurfaces):
            if si >= len(model.surfaces):
                break
            surf = model.surfaces[si]
            if surf.texinfo is None:
                continue
            if surf.flags & 0x01:  # SURF_SKY or no lightmap
                continue
            tex = surf.texinfo
            s = int(np.dot(mid, tex.vecs[0][:3]) + tex.vecs[0][3])
            t = int(np.dot(mid, tex.vecs[1][:3]) + tex.vecs[1][3])
            if s < surf.texturemins[0] or t < surf.texturemins[1]:
                continue
            ds = s - surf.texturemins[0]
            dt = t - surf.texturemins[1]
            if ds > surf.extents[0] or dt > surf.extents[1]:
                continue
            if surf.samples is None:
                return np.zeros(3, dtype=np.float32)
            # Sample the raw lightmap
            lm_w = (surf.extents[0] >> 4) + 1
            offset = (dt >> 4) * lm_w + (ds >> 4)
            if surf.samples.ndim == 1:
                base = offset * 3
                if base + 3 <= len(surf.samples):
                    return surf.samples[base:base + 3].astype(np.float32) / 255.0
            elif offset < len(surf.samples):
                return surf.samples[offset].astype(np.float32) / 255.0
            return np.zeros(3, dtype=np.float32)

        return self._recursive_light_point(model, node.children[side ^ 1], mid, end)

    # ------------------------------------------------------------------
    # Lightmap building
    # ------------------------------------------------------------------

    def build_lightmap(self, surf: Surface, atlas: LightmapAtlas,
                       gl_modulate: float = 1.0):
        """Compose the final RGBA lightmap for surf and write it into atlas.

        Steps:
        1. Accumulate base lightmap styles.
        2. Apply dynamic lights.
        3. Scale by gl_modulate, clamp, write to atlas buffer.
        """
        smax = (surf.extents[0] >> 4) + 1
        tmax = (surf.extents[1] >> 4) + 1
        size = smax * tmax

        # Allocate float work buffer (RGB)
        if self._work_buf is None or self._work_buf.shape[0] < size:
            self._work_buf = np.zeros((size, 3), dtype=np.float32)
        else:
            self._work_buf[:size] = 0.0
        work = self._work_buf[:size]

        # Accumulate light styles
        if surf.samples is not None and len(surf.samples) > 0:
            samples = surf.samples
            for style_idx in range(4):
                style = surf.styles[style_idx]
                if style == 255:
                    break
                scale = self.lightstyles[style] * gl_modulate
                base = size * 3 * style_idx
                if style_idx == 0 or base + size * 3 <= len(samples):
                    flat = samples[base:base + size * 3].reshape(size, 3).astype(np.float32)
                    work += flat * scale

        # Add dynamic lights
        self._add_dynamic_lights(surf, work, smax, tmax)

        # Convert to RGBA uint8
        rgba = np.empty((size, 4), dtype=np.uint8)
        clipped = np.clip(work, 0.0, 255.0).astype(np.uint8)
        rgba[:, :3] = clipped
        rgba[:, 3]  = 255

        atlas.write_lightmap(surf.light_s, surf.light_t, smax, tmax,
                             rgba.reshape(tmax, smax, 4))

    def _add_dynamic_lights(self, surf: Surface, work: np.ndarray,
                             smax: int, tmax: int):
        """Add contributions from all enabled dlights to the work buffer."""
        if not surf.texinfo:
            return

        tex = surf.texinfo
        s_axis = tex.vecs[0][:3]
        t_axis = tex.vecs[1][:3]

        for dl in self.dlights:
            # Project light origin onto the surface texture axes
            impact_s = np.dot(dl.origin, s_axis) + tex.vecs[0][3]
            impact_t = np.dot(dl.origin, t_axis) + tex.vecs[1][3]

            local_s = impact_s - surf.texturemins[0]
            local_t = impact_t - surf.texturemins[1]

            intensity2 = dl.intensity * dl.intensity
            scale = dl.intensity * 8.0  # raw intensity -> lightmap units

            for t in range(tmax):
                td = local_t - (t * 16 + 8)
                for s in range(smax):
                    sd = local_s - (s * 16 + 8)
                    dist2 = sd * sd + td * td
                    if dist2 < intensity2:
                        add = scale * (1.0 - dist2 / intensity2)
                        idx = t * smax + s
                        work[idx, 0] += dl.color[0] * add
                        work[idx, 1] += dl.color[1] * add
                        work[idx, 2] += dl.color[2] * add
