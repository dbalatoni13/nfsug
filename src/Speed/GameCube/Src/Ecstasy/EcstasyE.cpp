#include "./eViewPlat.hpp"
#include "Speed/Indep/Src/Ecstasy/Texture.hpp"
#include "Speed/Indep/Src/World/Car.hpp"
#include "Speed/Indep/Src/World/Scenery.hpp"
#include "Speed/Indep/bWare/Inc/bMath.hpp"
#include "Speed/Indep/bWare/Inc/bSlotPool.hpp"

enum VIDEO_MODE {
  NUM_VIDEO_MODES = 3,
  MODE_NTSC = 2,
  MODE_PAL60 = 1,
  MODE_PAL = 0,
};

enum EVIEWMODE {
  EVIEWMODE_TWOV = 4,
  EVIEWMODE_TWOH = 3,
  EVIEWMODE_ONE_RVM = 2,
  EVIEWMODE_ONE = 1,
  EVIEWMODE_NONE = 0,
};

EVIEWMODE CurrentViewMode = EVIEWMODE_NONE;

unsigned int bGetTicker();
int bGetFixTickerDifference(unsigned int start_ticks, unsigned int end_ticks);
int eSetDisplaySystem(int video_mode);
void eInitGX();
void eInitTexture();
void eExStartup();
void eDrawStartup();
void InitSlotPools();
int eInitEnvMap();
void SetScreenBuffers();
void eWaitUntilRenderingDone();

// idk where these go
Camera FlailerCamera;
Camera Player1Camera;
Camera Player2Camera;
Camera Player1RVMCamera;
Camera Player1HeadlightCamera;
Camera Player2HeadlightCamera;
Mtx44 Player1HeadlightProjection;
Mtx44 Player2HeadlightProjection;
Mtx44 Player1ReflectionProjection;
Mtx44 Player2ReflectionProjection;

unsigned int LastVBlankTime;
volatile int FrameCounter;
enum VIDEO_MODE eCurrentVideoMode;
int ScreenWidth;
int ScreenHeight;
SlotPool *ActiveTextureSlotPool;

void cb_PreRetrace(uint32_t param) { LastVBlankTime = bGetTicker(); }

void cb_PostRetrace(uint32_t param) {
  LastVBlankTime = bGetFixTickerDifference(LastVBlankTime, bGetTicker());
  FrameCounter++;
}

int eInitEnginePlat() {
  eSetDisplaySystem(1);
  eInitGX();
  eInitTexture();
  eExStartup();
  eDrawStartup();
  InitSlotPools();
  eInitEnvMap();
  SetScreenBuffers();
  return 1;
}

int eSetDisplaySystem(int video_mode) {
  if (eCurrentVideoMode != video_mode) {
    eCurrentVideoMode = static_cast<VIDEO_MODE>(video_mode);
    eWaitUntilRenderingDone();
    ScreenWidth = 640;
    ScreenHeight = 480;
    VISetPreRetraceCallback(cb_PreRetrace);
    VISetPostRetraceCallback(cb_PostRetrace);
  }
  return 1;
}

void InitSlotPools(void) {
  ActiveTextureSlotPool = bNewSlotPool(0xc, 600, "ActiveTextureSlotPool", 0);
  ActiveTextureSlotPool->ClearFlag(SLOTPOOL_FLAG_ZERO_ALLOCATED_MEMORY);
  return;
}

void epInitViews(void) {
  eView *view = eGetView(0, false);
  view->SetRenderTarget0(eGetRenderTarget(0));
  view->SetCamera(&FlailerCamera);
  view->SetActive(1);

  view = eGetView(1, false);
  view->SetRenderTarget0(eGetRenderTarget(1));
  view->SetCamera(&Player1Camera);
  view->SetActive(1);

  view = eGetView(2, false);
  view->SetRenderTarget0(eGetRenderTarget(2));
  view->SetCamera(&Player2Camera);
  view->SetActive(0);

  view = eGetView(8, false);
  view->SetCamera(&Player1HeadlightCamera);
  view->SetRenderTarget0(eGetRenderTarget(3));
  view->SetActive(1);
  view->GetPlatInfo()->SetLightPerspectiveProjection(&Player1HeadlightProjection);

  view = eGetView(9, false);
  view->SetCamera(&Player2HeadlightCamera);
  view->SetRenderTarget0(eGetRenderTarget(4));
  view->SetActive(0);
  view->GetPlatInfo()->SetLightPerspectiveProjection(&Player2HeadlightProjection);

  view = eGetView(3, false);
  view->SetRenderTarget0(eGetRenderTarget(5));
  view->SetActive(0);
  view->SetCamera(&Player1RVMCamera);

  view = eGetView(4, false);
  view->SetRenderTarget0(eGetRenderTarget(6));
  view->SetCamera(&Player1Camera);
  view->SetActive(1);
  view->GetPlatInfo()->SetLightPerspectiveProjection(&Player1ReflectionProjection);

  view = eGetView(5, false);
  view->SetRenderTarget0(eGetRenderTarget(7));
  view->SetCamera(&Player2Camera);
  view->SetActive(0);
  view->GetPlatInfo()->SetLightPerspectiveProjection(&Player2ReflectionProjection);
}

EVIEWMODE eGetCurrentViewMode() { return CurrentViewMode; }

// void eUpdateViewMode(void) {
//   int iVar1;
//   int iVar2;
//   int iVar3;
//   int iVar4;

//   eView::eView *eview_player1 = eView::eGetView(1);
//   eView::eView *eview_player2 = eView::eGetView(2);
//   eView::eView *eview_player1_rvm = eView::eGetView(3);

//   if (eview_player1->GetCameraMover() != nullptr) {
//     if (eview_player2->GetCameraMover() != nullptr) {
//       CurrentViewMode = EVIEWMODE_TWOH;
//     }
//   } else if (eview_player1->GetCameraMover() != nullptr) {
//     if (eview_player1_rvm->GetCameraMover() != nullptr) {
//       CurrentViewMode = EVIEWMODE_ONE_RVM;
//     }
//   } else {
//     CurrentViewMode = EVIEWMODE_NONE;
//     // if (eview_player1->GetCameraMover() != nullptr)
//     CurrentViewMode = EVIEWMODE_ONE;
//   }
// }

void eUpdateViewMode(void) {
  bNode *node1;
  bNode *node2;
  bNode *node3;

  eView *eview_player1 = eGetView(1, false);
  eView *eview_player2 = eGetView(2, false);
  eView *eview_player1_rvm = eGetView(3, false);

  node1 = (eview_player1->CameraMoverList).HeadNode.GetNext();
  node3 = (bNode *)0x0;
  if (node1 != (bNode *)&eview_player1->CameraMoverList) {
    node3 = node1;
  }
  if (node3 != (bNode *)0x0) {
    node1 = (eview_player2->CameraMoverList).HeadNode.GetNext();
    node3 = (bNode *)0x0;
    if (node1 != (bNode *)&eview_player2->CameraMoverList) {
      node3 = node1;
    }
    if (node3 != (bNode *)0x0) {
      CurrentViewMode = EVIEWMODE_TWOH;
      return;
    }
  }
  node1 = (eview_player1->CameraMoverList).HeadNode.GetNext();
  node3 = (bNode *)0x0;
  if (node1 != (bNode *)&eview_player1->CameraMoverList) {
    node3 = (eview_player1->CameraMoverList).HeadNode.GetNext();
  }
  if (node3 != nullptr) {
    node2 = (eview_player1_rvm->CameraMoverList).HeadNode.GetNext();
    node3 = (bNode *)0x0;
    if (node2 != (bNode *)&eview_player1_rvm->CameraMoverList) {
      node3 = node2;
    }
    if (node3 != nullptr) {
      CurrentViewMode = EVIEWMODE_ONE_RVM;
      return;
    }
  }
  CurrentViewMode = EVIEWMODE_NONE;
  if (node1 != (bNode *)&eview_player1->CameraMoverList) {
    CurrentViewMode = EVIEWMODE_TWOH; // (EVIEWMODE)node1;
  }
  if (CurrentViewMode != EVIEWMODE_NONE) {
    CurrentViewMode = EVIEWMODE_ONE;
  }
}

struct RaceCoordinator {
  int unk_00;
  uint8_t unk04[0x4C];
  int *unk_50;
};

RaceCoordinator *pRaceCoordinator;

eView *GetPlayerView(int nPlayerNumber) {
  int viewId;

  if (((pRaceCoordinator != nullptr) && (pRaceCoordinator->unk_00 == 5)) && (pRaceCoordinator->unk_50 != nullptr)) {
    if (nPlayerNumber != pRaceCoordinator->unk_50[5]) {
      return nullptr;
    }
    return eGetView(1, false);
  } else {
    return eGetView(nPlayerNumber + 1, false);
  }
}

TextureInfo *pTextureInfoRadialBlur;

void RadialBlurOn(eView *view) {
  if ((pRaceCoordinator == nullptr) || (pRaceCoordinator->unk_00 != 8)) {
    view->pBlendMask = pTextureInfoRadialBlur;
  }
}

void RadialBlurOn(int nPlayerNumber) {
  eView *view = GetPlayerView(nPlayerNumber);
  if (view != nullptr) {
    RadialBlurOn(view);
  }
}

void RadialBlurOff(eView *view) { view->pBlendMask = nullptr; }

void RadialBlurOff(int nPlayerNumber) {
  eView *view = GetPlayerView(nPlayerNumber);
  if (view != (eView *)0x0) {
    RadialBlurOff(view);
  }
}

int RadialBlurOnOff(bool on, int nPlayerNumber) {
  if (on) {
    RadialBlurOn(nPlayerNumber);
  } else {
    RadialBlurOff(nPlayerNumber);
  }
  return nPlayerNumber;
}

void RadialBlurAlpha(int param_1, float param_2, float param_3) {}

bool bStraddlesNearZ(Camera *camera, Car *car) { return false; }

void eForceBackgroundColour(unsigned char, unsigned char, unsigned char, float, const char *) {}

int eClampTopLeft(bool bOnOff, int nUnused) { return false; }

void eTagHeadlightCallback(SceneryDrawInfo *info) { info->SceneryInst->Rotation[1] = 512; }

int DisplayCullingStats(int screen_x, int screen_y) { return 0; }

int eGetScreenWidth() { return ScreenWidth; }

int eGetScreenHeight() { return ScreenWidth; }

void eSetScreenDisplayOffsets(int offset_x, int offset_y) {}

void eSetScreenDisplayOffsets(int &offset_x, int &offset_y) {}

eRenderTarget RenderTargets[15];
TextureInfo RenderTargetTextureInfos[15];
eRenderTarget *CurrentRenderTarget;

TextureInfo *eRenderTarget::GetTextureInfo() { return &RenderTargetTextureInfos[static_cast<int>(this->ID)]; }

TextureInfo *eGetRenderTargetTextureInfo(int name_hash) {
  for (int i = FIRST_RENDER_TARGET; i < NUM_RENDER_TARGETS; i++) {
    eRenderTarget *render_target = eGetRenderTarget(i);
    TextureInfo *info = render_target->GetTextureInfo();
    if (name_hash == info->NameHash) {
      return info;
    }
  }
  return nullptr;
}

eRenderTarget *eGetCurrentRenderTarget() { return CurrentRenderTarget; }

eRenderTarget *eGetRenderTarget(int render_target) { return &RenderTargets[render_target]; }

void eWaitUntilRenderingDone() {}

float CalculateH(unsigned short alpha) {
  unsigned short beta = alpha >> 1;
  float tan = bTan(beta);
  if (tan == 0.0f) {
    return 256.0f / tan;
  }
  return 10.0f;
}

// int epSetAllStripsVisibleState(eSolid *param1, int param2) {
//   param1->GetNext();
//   return 0;
// }
