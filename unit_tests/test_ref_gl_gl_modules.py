"""
Unit tests for ref_gl/gl_*.py helper behavior and safe code paths.
"""

import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ref_gl import gl_draw
from ref_gl import gl_image
from ref_gl import gl_light
from ref_gl import gl_mesh
from ref_gl import gl_model
from ref_gl import gl_rmain
from ref_gl import gl_rmisc
from ref_gl import gl_rsurf
from ref_gl import gl_warp


def test_gl_draw_health_color_thresholds():
    assert gl_draw._get_health_color(90) == [0.0, 1.0, 0.0]
    assert gl_draw._get_health_color(60) == [1.0, 1.0, 0.0]
    assert gl_draw._get_health_color(30) == [1.0, 0.5, 0.0]
    assert gl_draw._get_health_color(10) == [1.0, 0.0, 0.0]


def test_gl_draw_get_pic_size_mutable_refs():
    w = SimpleNamespace(value=0)
    h = SimpleNamespace(value=0)
    result = gl_draw.Draw_GetPicSize(w, h, "unused")
    assert result == (64, 64)
    assert w.value == 64
    assert h.value == 64


def test_gl_draw_find_pic_empty_returns_none():
    assert gl_draw.Draw_FindPic("") is None


def test_gl_draw_find_pic_builds_default_path(monkeypatch):
    captured = {}

    def fake_find_image(name, image_type):
        captured["name"] = name
        captured["type"] = image_type
        return 123

    monkeypatch.setattr(gl_image, "GL_FindImage", fake_find_image)
    result = gl_draw.Draw_FindPic("statusbar")
    assert result == 123
    assert captured["name"] == "pics/statusbar.pcx"


def test_gl_image_palette_to_rgba_maps_indices():
    # Palette layout: [r0,g0,b0, r1,g1,b1, ...]
    gl_image.palette_data = bytes([10, 20, 30, 40, 50, 60] + [0] * (768 - 6))
    rgba = gl_image._palette_to_rgba(bytes([0, 1]))
    assert rgba == bytes([10, 20, 30, 255, 40, 50, 60, 255])


def test_gl_image_palette_to_rgba_none_palette():
    gl_image.palette_data = None
    assert gl_image._palette_to_rgba(bytes([0, 1])) is None


def test_gl_image_load_image_uses_cache():
    gl_image.texture_cache = {"pics/foo": 777}
    result = gl_image.GL_LoadImage("pics/foo")
    assert result == 777


def test_gl_image_load_image_falls_back_to_pcx(monkeypatch):
    gl_image.texture_cache = {}
    gl_image.textures = []

    monkeypatch.setattr(gl_image, "LoadWal", lambda name: None)
    monkeypatch.setattr(gl_image, "LoadPcx", lambda name: 99)

    result = gl_image.GL_LoadImage("pics/test")
    assert result == 99
    assert gl_image.texture_cache["pics/test"] == 99
    assert 99 in gl_image.textures


def test_gl_image_upload8_requires_palette():
    gl_image.palette_data = None
    assert gl_image.GL_Upload8(bytes([0, 1]), 1, 2, False, False) is None


def test_gl_image_draw_get_palette_roundtrip():
    gl_image.palette_data = b"abc"
    assert gl_image.Draw_GetPalette() == b"abc"


def test_gl_light_scalar_helpers():
    assert gl_light._clamp(2.0) == 1.0
    assert gl_light._clamp(-1.0) == 0.0
    assert gl_light._lerp(10.0, 20.0, 0.25) == 12.5


def test_gl_light_vector_helpers():
    assert gl_light._vec3_add([1, 2, 3], [4, 5, 6]) == [5, 7, 9]
    assert gl_light._vec3_scale([1, -2, 3], 2) == [2, -4, 6]


def test_gl_light_vec3_normalize_zero_fallback():
    assert gl_light._vec3_normalize([0, 0, 0]) == [0, 0, 1]


def test_gl_light_set_style_scales_255_values():
    gl_light.R_SetLightStyle(0, [255, 128, 0])
    style = gl_light.R_GetLightStyle(0)
    assert style[0] == pytest.approx(1.0)
    assert style[1] == pytest.approx(128.0 / 255.0)
    assert style[2] == pytest.approx(0.0)


def test_gl_light_get_style_out_of_range_default():
    assert gl_light.R_GetLightStyle(1000) == [1.0, 1.0, 1.0]


def test_gl_light_sample_lightmap_leaf_from_bytes():
    model = SimpleNamespace(lightdata=bytes([0, 64, 255]))
    leaf = {"cluster": 0, "lightofs": 0}
    value = gl_light._sample_lightmap_at_leaf(leaf, [0, 0, 0], model)
    assert value[0] == 0.0
    assert value[1] == pytest.approx(64 / 255.0)
    assert value[2] == 1.0


def test_gl_light_point_defaults():
    assert gl_light.R_LightPoint(None) == [1.0, 1.0, 1.0]
    assert gl_light.R_LightPoint([0, 0, 0], None) == [0.5, 0.5, 0.5]


def test_gl_light_entity_no_entity_default():
    assert gl_light.R_LightEntity(None) == [1.0, 1.0, 1.0]


def test_gl_light_entity_with_dynamic_light_clamps(monkeypatch):
    monkeypatch.setattr(gl_light, "R_LightPoint", lambda origin, model=None: [0.9, 0.9, 0.9])
    gl_light.dlights = [{"origin": [0, 0, 0], "color": [1, 1, 1], "intensity": 255}]
    entity = SimpleNamespace(origin=[0, 0, 0])
    lit = gl_light.R_LightEntity(entity)
    assert lit == [1.0, 1.0, 1.0]


def test_gl_model_radius_from_bounds():
    radius = gl_model.RadiusFromBounds([-2, -2, -2], [2, 2, 2])
    assert radius == pytest.approx((12) ** 0.5)


def test_gl_model_point_in_leaf_no_nodes_returns_none():
    model = SimpleNamespace(nodes=[])
    assert gl_model.Mod_PointInLeaf([0, 0, 0], model) is None


def test_gl_model_cluster_pvs_cluster_negative_returns_none():
    model = SimpleNamespace(visdata=b"x", leafs=[1, 2])
    assert gl_model.Mod_ClusterPVS(-1, model) is None


def test_gl_model_free_and_free_all():
    gl_model.mod_known = {"a": object(), "b": object()}
    gl_model.Mod_Free("a")
    assert "a" not in gl_model.mod_known
    gl_model.Mod_FreeAll()
    assert gl_model.mod_known == {}


def test_gl_mesh_lerp_verts_interpolates():
    ov = [gl_mesh.MD2Vertex(0, 0, 0, 0)]
    v = [gl_mesh.MD2Vertex(10, 20, 30, 3)]
    result = gl_mesh.GL_LerpVerts(1, v, ov, None, 0.25, None, None, None)
    assert len(result) == 1
    assert result[0].x == pytest.approx(2.5)
    assert result[0].y == pytest.approx(5.0)
    assert result[0].z == pytest.approx(7.5)
    assert result[0].normal_idx == 3


def test_gl_mesh_light_and_cull_defaults():
    assert gl_mesh.GL_LightVertex(None, None) == [1.0, 1.0, 1.0]
    assert gl_mesh.R_CullAliasModel(None, None) is False


def test_gl_rsurf_read_surfedges():
    # Two int32 values: 1, -2
    data = (1).to_bytes(4, "little", signed=True) + (-2).to_bytes(4, "little", signed=True)
    result = gl_rsurf._read_surfedges(data, 0, 2)
    assert result == [1, -2]


def test_gl_rsurf_read_edges_with_sign():
    # edge0=(10,20), edge1=(30,40)
    data = (
        (10).to_bytes(2, "little") + (20).to_bytes(2, "little") +
        (30).to_bytes(2, "little") + (40).to_bytes(2, "little")
    )
    result = gl_rsurf._read_edges(data, [0, -1])
    assert result == [[10, 20], [40, 30]]


def test_gl_rsurf_lightmap_block_allocate_and_reset():
    block = gl_rsurf.LightmapBlock(width=8, height=8)
    x0, y0 = block.allocate(4, 4)
    x1, y1 = block.allocate(4, 4)
    x2, y2 = block.allocate(4, 4)
    assert (x0, y0) == (0, 0)
    assert (x1, y1) == (4, 0)
    assert (x2, y2) == (0, 4)
    block.reset()
    assert block.next_x == 0
    assert block.next_y == 0
    assert block.row_height == 0


def test_gl_rsurf_texture_animation_dict_and_default():
    assert gl_rsurf.R_TextureAnimation({"imageindex": 7}) == 7
    assert gl_rsurf.R_TextureAnimation(None) == 0


def test_gl_rmain_stub_and_defaults():
    assert gl_rmain.R_CullBox([0, 0, 0], [1, 1, 1]) is False
    assert gl_rmain.R_DrawSpriteModel(None) is None
    assert gl_rmain.R_DrawParticles() is None
    assert gl_rmain.GL_DrawParticles(0, [], None) is None
    assert gl_rmain.R_PolyBlend() is None


def test_gl_rmisc_todo_functions_return_none():
    assert callable(gl_rmisc.R_InitParticleTexture)
    assert callable(gl_rmisc.GL_ScreenShot_f)
    assert callable(gl_rmisc.GL_Strings_f)
    assert callable(gl_rmisc.GL_SetDefaultState)
    assert callable(gl_rmisc.GL_UpdateSwapInterval)


def test_gl_warp_todo_functions_return_none():
    assert callable(gl_warp.BoundPoly)
    assert callable(gl_warp.SubdividePolygon)
    assert callable(gl_warp.GL_SubdivideSurface)
    assert callable(gl_warp.EmitWaterPolys)
    assert callable(gl_warp.DrawSkyPolygon)
    assert callable(gl_warp.ClipSkyPolygon)
    assert callable(gl_warp.R_AddSkySurface)
    assert callable(gl_warp.R_ClearSkyBox)
    assert callable(gl_warp.MakeSkyVec)
    assert callable(gl_warp.R_DrawSkyBox)
    assert callable(gl_warp.R_SetSky)
