#pragma once

#include "Speed/Indep/Src/Ecstasy/Texture.hpp"
#include "Speed/Indep/bWare/Inc/bVector.hpp"
#include <dolphin.h>

enum EVIEW_ID {
  NUM_RVM_VIEWS = 1,
  NUM_PLAYER_VIEWS = 3,
  NUM_RENDER_VIEWS = 21,
  NUM_EVIEWS = 22,
  EVIEW_LAST_ENVMAP = 21,
  EVIEW_FIRST_ENVMAP = 16,
  EVIEW_LAST_RVM = 3,
  EVIEW_FIRST_RVM = 3,
  EVIEW_LAST_PLAYER = 3,
  EVIEW_FIRST_PLAYER = 1,
  EVIEW_LAST_RENDER = 21,
  EVIEW_FIRST_RENDER = 1,
  EVIEW_LAST = 21,
  EVIEW_FIRST = 0,
  EVIEW_ENVMAP0D = 21,
  EVIEW_ENVMAP0U = 20,
  EVIEW_ENVMAP0L = 19,
  EVIEW_ENVMAP0B = 18,
  EVIEW_ENVMAP0R = 17,
  EVIEW_ENVMAP0F = 16,
  EVIEW_SHADOWMATTE = 15,
  EVIEW_SHADOWMAP2 = 14,
  EVIEW_SHADOWMAP1 = 13,
  EVIEW_HDR_SCENE = 12,
  EVIEW_QUADRANT_BOTTOM_RIGHT = 11,
  EVIEW_QUADRANT_BOTTOM_LEFT = 10,
  EVIEW_QUADRANT_TOP_RIGHT = 9,
  EVIEW_QUADRANT_TOP_LEFT = 8,
  EVIEW_PLAYER2_SPECULAR = 7,
  EVIEW_PLAYER1_SPECULAR = 6,
  EVIEW_PLAYER2_GLOW = 5,
  EVIEW_PLAYER1_GLOW = 4,
  EVIEW_PLAYER1_RVM = 3,
  EVIEW_PLAYER2 = 2,
  EVIEW_PLAYER1 = 1,
  EVIEW_FLAILER = 0,
  EVIEW_NONE = -1,
};

struct eView;

struct eViewPlatInfo {
  // total size: 0x174
  bMatrix4 WorldViewMatrix;          // offset 0x0, size 0x40
  bMatrix4 ViewScreenMatrix;         // offset 0x40, size 0x40
  bMatrix4 WorldClipMatrix;          // offset 0x80, size 0x40
  bMatrix4 WorldScreenMatrix;        // offset 0xC0, size 0x40
  Mtx44 *LightPerspectiveProjection; // offset 0x100, size 0x4
  eView *ReflectionView;             // offset 0x104, size 0x4
  eView *SpecularView;               // offset 0x108, size 0x4
  float aspect;                      // offset 0x10C, size 0x4
  float fovscl;                      // offset 0x110, size 0x4
  bVector4 ClippingPlanes[6];        // offset 0x114, size 0x60

  inline eViewPlatInfo();
  inline bMatrix4 *GetWorldViewMatrix();
  inline bMatrix4 *GetViewScreenMatrix();
  inline bMatrix4 *GetWorldClipMatrix();
  inline bMatrix4 *GetWorldScreenMatrix();

  void SetWorldViewMatrix(bMatrix4 *view);
  void SetViewScreenMatrix(bMatrix4 *proj);

  Mtx44 *GetLightPerspectiveProjection() { return LightPerspectiveProjection; };
  void SetLightPerspectiveProjection(Mtx44 *projection) { LightPerspectiveProjection = projection; }
};

class eViewPlatInterface {
  // total size: 0x4
  eViewPlatInfo *PlatInfo; // offset 0x0, size 0x4

public:
  eViewPlatInfo *GetPlatInfo() { return PlatInfo; }
  void SetPlatInfo(eViewPlatInfo *info) { PlatInfo = info; }
};

enum TARGET_ID {
  NUM_RENDER_TARGETS = 15,
  LAST_RENDER_TARGET = 14,
  FIRST_RENDER_TARGET = 0,
  TOTAL_RENDER_TARGETS = 15,
  // TARGET_ENVMAP0_FULL = 16,
  // TARGET_ENVMAP0D = 15,
  TARGET_ENVMAP0U = 14,
  TARGET_ENVMAP0L = 13,
  TARGET_ENVMAP0B = 12,
  TARGET_ENVMAP0R = 11,
  TARGET_ENVMAP0F = 10,
  TARGET_QUADRANT_BOTTOM_RIGHT = 9,
  TARGET_QUADRANT_BOTTOM_LEFT = 8,
  TARGET_QUADRANT_TOP_RIGHT = 7,
  TARGET_QUADRANT_TOP_LEFT = 6,
  TARGET_PLAYER2_SPECULAR = 5,
  TARGET_PLAYER1_SPECULAR = 4,
  TARGET_PLAYER1_RVM = 3,
  TARGET_PLAYER2 = 2,
  TARGET_PLAYER1 = 1,
  TARGET_FLAYER = 0,
};
enum FILTER_ID {
  FILTER_TOTAL = 11,
  FILTER_PIXELATE = 10,
  FILTER_EFB_XFB_AA = 9,
  FILTER_CONTRAST_INTENSITY = 8,
  FILTER_GLOWBLOOM = 7,
  FILTER_MOTIONBLUR = 6,
  FILTER_REFLECTION = 5,
  FILTER_SPHERE_MAP = 4,
  FILTER_CUBE_FACES = 3,
  FILTER_EFB_XFB = 2,
  FILTER_DEFAULT = 1,
  FILTER_OFF = 0,
};

struct eRenderTarget {
  // total size: 0x44
  TARGET_ID ID;             // offset 0x0, size 0x4
  const char *Name;         // offset 0x4, size 0x4
  int Active;               // offset 0x8, size 0x4
  int ScissorX;             // offset 0xC, size 0x4
  int ScissorY;             // offset 0x10, size 0x4
  int ScissorW;             // offset 0x14, size 0x4
  int ScissorH;             // offset 0x18, size 0x4
  int FrameAddress;         // offset 0x1C, size 0x4
  int FrameWidth;           // offset 0x20, size 0x4
  int FrameHeight;          // offset 0x24, size 0x4
  int unk28;                // offset 0x28, size 0x4
  FILTER_ID CopyFilterID;   // offset 0x2C, size 0x4
  GXColor BackgroundColour; // offset 0x30, size 0x4
  int ClearBackground;      // offset 0x34, size 0x4
  bMatrix4 *WorldClip;      // offset 0x38, size 0x4
  bMatrix4 *WorldView;      // offset 0x3C, size 0x4
  bMatrix4 *ViewScreen;     // offset 0x40, size 0x4

  FILTER_ID GetCopyFilter() { return CopyFilterID; }

  TextureInfo *GetTextureInfo();
};
