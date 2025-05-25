#pragma once

#include "Speed/Indep/Src/Camera/Camera.hpp"
#include "Speed/Indep/Src/Camera/CameraMover.hpp"
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
  bVector::bMatrix4 WorldViewMatrix;   // offset 0x0, size 0x40
  bVector::bMatrix4 ViewScreenMatrix;  // offset 0x40, size 0x40
  bVector::bMatrix4 WorldClipMatrix;   // offset 0x80, size 0x40
  bVector::bMatrix4 WorldScreenMatrix; // offset 0xC0, size 0x40
  Mtx44 *LightPerspectiveProjection;   // offset 0x100, size 0x4
  eView *ReflectionView;               // offset 0x104, size 0x4
  eView *SpecularView;                 // offset 0x108, size 0x4
  float aspect;                        // offset 0x10C, size 0x4
  float fovscl;                        // offset 0x110, size 0x4
  bVector::bVector4 ClippingPlanes[6]; // offset 0x114, size 0x60

  inline eViewPlatInfo();
  inline bVector::bMatrix4 *GetWorldViewMatrix();
  inline bVector::bMatrix4 *GetViewScreenMatrix();
  inline bVector::bMatrix4 *GetWorldClipMatrix();
  inline bVector::bMatrix4 *GetWorldScreenMatrix();

  void SetWorldViewMatrix(bVector::bMatrix4 *view);
  void SetViewScreenMatrix(bVector::bMatrix4 *proj);

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

eView *eGetView(int view_id);

inline eView *eGetView(int view_id, bool doAssert) {
  if (doAssert) {
    // ?
  }
  return eGetView(view_id);
}

struct eView : public eViewPlatInterface {
  // total size: 0x54
  enum EVIEW_ID ID; // offset 0x4, size 0x4
  char Active;      // offset 0x8, size 0x1
  char LetterBox;   // offset 0x9, size 0x1
  char pad0;        // offset 0xA, size 0x1
  char pad1;        // offset 0xB, size 0x1
  float H;          // offset 0xC, size 0x4
  float NearZ;      // offset 0x10, size 0x4
  float FarZ;       // offset 0x14, size 0x4
  float FovBias;    // offset 0x18, size 0x4
  float FovDegrees; // offset 0x1C, size 0x4
  // int BlackAndWhiteMode;               // offset 0x20, size 0x4
  int PixelMinSize;                    // offset 0x24, size 0x4
  bVector::bVector3 ViewDirection;     // offset 0x28, size 0x10
  Camera *pCamera;                     // offset 0x34, size 0x4
  bTList<CameraMover> CameraMoverList; // offset 0x38, size 0x8
  unsigned int NumCopsInView;          // offset 0x40, size 0x4
  // unsigned int NumCopsTotal;           // offset 0x44, size 0x4
  // unsigned int NumCopsCherry;                     // offset 0x48, size 0x4
  struct TextureInfo *pBlendMask;                 // offset 0x4C, size 0x4
  struct eDynamicLightContext *WorldLightContext; // offset 0x50, size 0x4
  struct eRenderTarget *RenderTargetTable[1];     // offset 0x54, size 0x4
  struct ScreenEffectDB *ScreenEffects;           // offset 0x58, size 0x4
  struct Rain *Precipitation;                     // offset 0x5C, size 0x4
  struct FacePixelation *facePixelation;          // offset 0x60, size 0x4

  void SetRenderTarget(eRenderTarget *target, int index) { RenderTargetTable[index] = target; }

  void SetRenderTarget0(eRenderTarget *target) { SetRenderTarget(target, 0); }

  void SetCamera(Camera *camera) { this->pCamera = camera; }

  void SetActive(int state) {
    int prev_state = Active;
    Active = state;
  }

  CameraMover *GetCameraMover() {
    if (CameraMoverList.IsEmpty()) {
      return static_cast<CameraMover *>(nullptr);
    }
    return CameraMoverList.GetHead();
  }
};
