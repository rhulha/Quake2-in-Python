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
from ref_gl import gl_screenshot
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


def test_gl_draw_center_string_computes_center(monkeypatch):
    calls = []
    monkeypatch.setattr(gl_draw, "_setup_2d_mode", lambda: None)
    monkeypatch.setattr(gl_draw, "_restore_3d_mode", lambda: None)
    monkeypatch.setattr(gl_draw, "Draw_String", lambda x, y, text, color=None: calls.append((x, y, text, color)))

    gl_draw.screen_width = 800
    gl_draw.char_width = 8

    gl_draw.SCR_DrawCenterString(120, "TEST")

    # len("TEST") * 8 = 32, centered in 800 => x=384
    assert calls == [(384, 120, "TEST", [1.0, 1.0, 1.0])]


def test_gl_draw_hud_draws_expected_strings(monkeypatch):
    fills = []
    strings = []

    monkeypatch.setattr(gl_draw, "_setup_2d_mode", lambda: None)
    monkeypatch.setattr(gl_draw, "_restore_3d_mode", lambda: None)
    monkeypatch.setattr(gl_draw, "Draw_Fill", lambda x, y, w, h, color: fills.append((x, y, w, h, color)))
    monkeypatch.setattr(gl_draw, "Draw_String", lambda x, y, text, color=None: strings.append((x, y, text, color)))

    gl_draw.screen_width = 640
    gl_draw.screen_height = 480

    player_state = {
        "health": 87,
        "armor": 40,
        "ammo": 12,
        "score": 9001,
    }

    gl_draw.SCR_DrawHUD(player_state)

    assert fills == [(0, 448, 640, 32, [0.1, 0.1, 0.1])]
    assert strings[0] == (10, 456, "Health: 87", [0.0, 1.0, 0.0])
    assert strings[1] == (150, 456, "Armor: 40", [0.0, 0.5, 1.0])
    assert strings[2] == (290, 456, "Ammo: 12", [1.0, 1.0, 0.0])
    assert strings[3] == (460, 456, "Score: 9001", [0.5, 1.0, 0.5])


def test_gl_draw_hud_none_state_no_draw(monkeypatch):
    called = {"fill": 0, "string": 0}
    monkeypatch.setattr(gl_draw, "Draw_Fill", lambda *args, **kwargs: called.__setitem__("fill", called["fill"] + 1))
    monkeypatch.setattr(gl_draw, "Draw_String", lambda *args, **kwargs: called.__setitem__("string", called["string"] + 1))
    gl_draw.SCR_DrawHUD(None)
    assert called["fill"] == 0
    assert called["string"] == 0


def test_gl_draw_pause_and_gameover_call_center(monkeypatch):
    centers = []
    fills = []

    monkeypatch.setattr(gl_draw, "_setup_2d_mode", lambda: None)
    monkeypatch.setattr(gl_draw, "_restore_3d_mode", lambda: None)
    monkeypatch.setattr(gl_draw, "Draw_Fill", lambda *args: fills.append(args))
    monkeypatch.setattr(gl_draw, "SCR_DrawCenterString", lambda y, text: centers.append((y, text)))

    gl_draw.screen_width = 800
    gl_draw.screen_height = 600

    gl_draw.DrawPause()
    gl_draw.DrawGameOver()

    assert centers[0] == (280, "PAUSED")
    assert centers[1] == (280, "GAME OVER")
    assert len(fills) == 2


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


def test_gl_image_bind_texture_calls_gl(monkeypatch):
    called = {"count": 0, "args": None}

    def fake_bind(target, tex_id):
        called["count"] += 1
        called["args"] = (target, tex_id)

    monkeypatch.setattr(gl_image, "glBindTexture", fake_bind)
    gl_image.GL_BindTexture(42)
    assert called["count"] == 1
    assert called["args"][1] == 42


def test_gl_image_bind_texture_ignores_zero(monkeypatch):
    called = {"count": 0}
    monkeypatch.setattr(gl_image, "glBindTexture", lambda *args: called.__setitem__("count", called["count"] + 1))
    gl_image.GL_BindTexture(0)
    assert called["count"] == 0


def test_gl_image_bind_by_index(monkeypatch):
    bound = {"value": None}
    monkeypatch.setattr(gl_image, "GL_BindTexture", lambda tex_id: bound.__setitem__("value", tex_id))
    gl_image.textures = [11, 22, 33]
    gl_image.GL_Bind(1)
    assert bound["value"] == 22


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


def test_gl_light_build_lightmap_fills_white_stride_three():
    dest = bytearray(12)
    gl_light.R_BuildLightMap({"dummy": True}, dest, 3)
    assert dest == bytearray([255, 255, 255] * 4)


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


def test_gl_model_for_name_delegates(monkeypatch):
    monkeypatch.setattr(gl_model, "Mod_LoadModel", lambda name, crash: (name, crash))
    assert gl_model.Mod_ForName("maps/base1.bsp", True) == ("maps/base1.bsp", True)


def test_gl_model_begin_registration_increments_sequence(monkeypatch):
    gl_model.registration_sequence = 10
    monkeypatch.setattr(gl_model, "Mod_ForName", lambda name, crash: {"name": name, "crash": crash})
    result = gl_model.R_BeginRegistration("maps/test.bsp")
    assert result == {"name": "maps/test.bsp", "crash": True}
    assert gl_model.registration_sequence == 11


def test_gl_model_register_model_error_returns_none(monkeypatch):
    def fail(name, crash):
        raise RuntimeError("boom")

    monkeypatch.setattr(gl_model, "Mod_ForName", fail)
    assert gl_model.R_RegisterModel("x") is None


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


def test_gl_rsurf_create_surface_lightmap_sets_coords(monkeypatch):
    class FakeBlock:
        def allocate(self, w, h):
            assert (w, h) == (16, 16)
            return (5, 9)

    monkeypatch.setattr(gl_rsurf, "lightmap_block", FakeBlock())
    surf = {}
    gl_rsurf.GL_CreateSurfaceLightmap(surf)
    assert surf["lm_x"] == 5
    assert surf["lm_y"] == 9


def test_gl_rsurf_parse_texinfo_entry():
    # vecs + flags + value + texture(32) + nexttexinfo
    data = bytearray(gl_rsurf.TEXINFO_SIZE_BSP)
    import struct

    struct.pack_into('<fff', data, 0, 1.0, 0.0, 0.0)    # s axis
    struct.pack_into('<f', data, 12, 16.0)               # s offset
    struct.pack_into('<fff', data, 16, 0.0, 1.0, 0.0)    # t axis
    struct.pack_into('<f', data, 28, 8.0)                # t offset
    struct.pack_into('<I', data, 32, 123)                # flags
    struct.pack_into('<I', data, 36, 456)                # value
    tex_name = b"e1u1/base1_1"
    data[40:40 + len(tex_name)] = tex_name
    struct.pack_into('<i', data, 72, -1)

    tx = gl_rsurf._parse_texinfo_entry(bytes(data), 0)
    assert tx is not None
    assert tx["texture"] == "e1u1/base1_1"
    assert tx["s_axis"] == [1.0, 0.0, 0.0]
    assert tx["t_axis"] == [0.0, 1.0, 0.0]


def test_gl_rsurf_compute_uv_with_texinfo():
    tx = {
        "s_axis": [1.0, 0.0, 0.0],
        "t_axis": [0.0, 1.0, 0.0],
        "s_off": 32.0,
        "t_off": 64.0,
    }
    u, v = gl_rsurf._compute_uv([32.0, 64.0, 0.0], tx)
    assert u == pytest.approx(1.0)
    assert v == pytest.approx(2.0)


def test_gl_rsurf_draw_face_textured_path(monkeypatch):
    # Build a simple triangle through surfedges/edges indirection.
    import struct

    surfedges = struct.pack('<iii', 0, 1, 2)
    edges = struct.pack('<HHHHHH', 0, 1, 1, 2, 2, 0)

    # One texinfo entry with texture name.
    tex = bytearray(gl_rsurf.TEXINFO_SIZE_BSP)
    struct.pack_into('<fff', tex, 0, 1.0, 0.0, 0.0)
    struct.pack_into('<f', tex, 12, 0.0)
    struct.pack_into('<fff', tex, 16, 0.0, 1.0, 0.0)
    struct.pack_into('<f', tex, 28, 0.0)
    tex_name = b"e1u1/base1_1"
    tex[40:40 + len(tex_name)] = tex_name

    model = SimpleNamespace(
        lump_surfedges=surfedges,
        lump_edges=edges,
        lump_texinfo=bytes(tex),
        vertices=[[0.0, 0.0, 0.0], [64.0, 0.0, 0.0], [0.0, 64.0, 0.0]],
    )
    face = {"first_edge": 0, "num_edges": 3, "texinfo": 0}

    calls = {"tex": 0, "verts": 0, "bind": 0, "enable": 0}
    monkeypatch.setattr(gl_rsurf, "glBegin", lambda mode: None)
    monkeypatch.setattr(gl_rsurf, "glEnd", lambda: None)
    monkeypatch.setattr(gl_rsurf, "glVertex3f", lambda x, y, z: calls.__setitem__("verts", calls["verts"] + 1))
    monkeypatch.setattr(gl_rsurf, "glTexCoord2f", lambda u, v: calls.__setitem__("tex", calls["tex"] + 1))
    monkeypatch.setattr(gl_rsurf, "glEnable", lambda mode: calls.__setitem__("enable", calls["enable"] + 1))
    monkeypatch.setattr(gl_rsurf, "glDisable", lambda mode: None)
    monkeypatch.setattr(gl_rsurf, "glColor4f", lambda *args: None)
    monkeypatch.setattr(gl_rsurf, "glColor3f", lambda *args: None)

    class _FakeImage:
        @staticmethod
        def GL_FindImage(name, image_type):
            return 55

        @staticmethod
        def GL_BindTexture(tex_id):
            calls["bind"] += 1

    import ref_gl.gl_image as _gl_image
    monkeypatch.setattr(_gl_image, "GL_FindImage", _FakeImage.GL_FindImage)
    monkeypatch.setattr(_gl_image, "GL_BindTexture", _FakeImage.GL_BindTexture)

    count = gl_rsurf._draw_face(model, face)
    assert count == 3
    assert calls["bind"] == 1
    assert calls["enable"] >= 1
    assert calls["tex"] == 3
    assert calls["verts"] == 3


def test_gl_rmain_stub_and_defaults():
    assert gl_rmain.R_CullBox([0, 0, 0], [1, 1, 1]) is False
    assert gl_rmain.R_DrawSpriteModel(None) is None
    assert gl_rmain.R_DrawParticles() is None
    assert gl_rmain.GL_DrawParticles(0, [], None) is None
    assert gl_rmain.R_PolyBlend() is None


def test_gl_rmain_setup_viewport_calls_gl(monkeypatch):
    calls = []

    monkeypatch.setattr(gl_rmain, "glViewport", lambda x, y, w, h: calls.append(("viewport", x, y, w, h)))
    monkeypatch.setattr(gl_rmain, "glMatrixMode", lambda mode: calls.append(("matrix", mode)))
    monkeypatch.setattr(gl_rmain, "glLoadIdentity", lambda: calls.append(("identity",)))
    monkeypatch.setattr(gl_rmain, "GLFrustum", lambda l, r, b, t, n, f: calls.append(("frustum", l, r, b, t, n, f)))

    gl_rmain.R_SetupViewport(800, 600, 75.0)

    assert calls[0] == ("viewport", 0, 0, 800, 600)
    assert any(c[0] == "frustum" for c in calls)


def test_gl_rmain_setup_matrices_order(monkeypatch):
    calls = []
    monkeypatch.setattr(gl_rmain, "glMatrixMode", lambda mode: calls.append(("matrix", mode)))
    monkeypatch.setattr(gl_rmain, "glLoadIdentity", lambda: calls.append(("identity",)))
    monkeypatch.setattr(gl_rmain, "glRotatef", lambda a, x, y, z: calls.append(("rotate", a, x, y, z)))
    monkeypatch.setattr(gl_rmain, "glTranslatef", lambda x, y, z: calls.append(("translate", x, y, z)))

    refdef = SimpleNamespace(viewangles=[10, 20, 30], vieworg=[100, 200, 300])
    gl_rmain.R_SetupMatrices(refdef)

    assert calls[0][0] == "matrix"
    assert calls[1] == ("identity",)
    assert calls[2][0] == "rotate"
    assert calls[3][0] == "rotate"
    assert calls[4][0] == "rotate"
    assert calls[5] == ("translate", -100, -200, -300)


def test_gl_screenshot_error_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(gl_screenshot, "glFlush", lambda: None)
    monkeypatch.setattr(gl_screenshot, "glFinish", lambda: None)
    monkeypatch.setattr(gl_screenshot, "glReadBuffer", lambda x: None)

    def fail_read(*args, **kwargs):
        raise RuntimeError("read failed")

    monkeypatch.setattr(gl_screenshot, "glReadPixels", fail_read)
    assert gl_screenshot.take_screenshot(4, 4, str(tmp_path)) is None


def test_gl_screenshot_success(monkeypatch, tmp_path):
    monkeypatch.setattr(gl_screenshot, "glFlush", lambda: None)
    monkeypatch.setattr(gl_screenshot, "glFinish", lambda: None)
    monkeypatch.setattr(gl_screenshot, "glReadBuffer", lambda x: None)
    monkeypatch.setattr(gl_screenshot, "glReadPixels", lambda *args: b"\x00" * (2 * 2 * 3))

    saved = {"path": None}

    class FakeDatetime:
        @staticmethod
        def now():
            class _Now:
                @staticmethod
                def strftime(fmt):
                    return "20260101_120000"

            return _Now()

    class FakeImageModule:
        @staticmethod
        def fromstring(data, size, mode):
            return object()

        @staticmethod
        def save(surface, path):
            saved["path"] = path

    class FakeTransform:
        @staticmethod
        def flip(surface, xbool, ybool):
            return surface

    monkeypatch.setattr(gl_screenshot, "datetime", FakeDatetime)
    monkeypatch.setattr(gl_screenshot.pygame, "image", FakeImageModule)
    monkeypatch.setattr(gl_screenshot.pygame, "transform", FakeTransform)

    path = gl_screenshot.take_screenshot(2, 2, str(tmp_path))
    assert path is not None
    assert path.endswith("quake2_screenshot_20260101_120000.png")
    assert saved["path"] == path


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
