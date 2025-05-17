#include "./eViewPlat.hpp"
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
SlotPool *bNewSlotPool(int slot_size, int num_slots, const char *debug_name,
                       int memory_pool);
eView::eRenderTarget *eGetRenderTarget(int render_target);

eView::eView *eGetView(int view_id);

// goes in eView.hpp
inline eView::eView *eGetView(int view_id, bool doAssert) {
  if (doAssert) {
    // ?
  }
  return eGetView(view_id);
}
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

void cb_PreRetrace(unsigned long param);
void cb_PostRetrace(unsigned long param);

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
    eCurrentVideoMode = (enum VIDEO_MODE)video_mode;
    eWaitUntilRenderingDone();
    ScreenWidth = 0x280;
    ScreenHeight = 0x1e0;
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
  eView::eView *view = eGetView(0, false);
  view->SetRenderTarget(eGetRenderTarget(0));
  view->SetCamera(&FlailerCamera);
  view->SetActive(1);

  view = eGetView(1, false);
  view->SetRenderTarget(eGetRenderTarget(1));
  view->SetCamera(&Player1Camera);
  view->SetActive(1);

  view = eGetView(2, false);
  view->SetRenderTarget(eGetRenderTarget(2));
  view->SetCamera(&Player2Camera);
  view->SetActive(1);

  view = eGetView(8, false);
  view->SetCamera(&Player1HeadlightCamera);
  view->SetRenderTarget(eGetRenderTarget(3));
  view->SetActive(1);
  view->PlatInfo->LightPerspectiveProjection = &Player1HeadlightProjection;

  view = eGetView(9, false);
  view->SetCamera(&Player2HeadlightCamera);
  view->SetRenderTarget(eGetRenderTarget(4));
  view->SetActive(0);
  view->PlatInfo->LightPerspectiveProjection = &Player2HeadlightProjection;

  view = eGetView(3, false);
  view->SetRenderTarget(eGetRenderTarget(5));
  view->SetActive(0);
  view->SetCamera(&Player1RVMCamera);

  view = eGetView(4, false);
  view->SetRenderTarget(eGetRenderTarget(6));
  view->SetCamera(&Player1Camera);
  view->SetActive(1);
  view->PlatInfo->LightPerspectiveProjection = &Player1ReflectionProjection;

  view = eGetView(5, false);
  view->SetRenderTarget(eGetRenderTarget(7));
  view->SetCamera(&Player2Camera);
  view->SetActive(0);
  view->PlatInfo->LightPerspectiveProjection = &Player2ReflectionProjection;
}

EVIEWMODE eGetCurrentViewMode() { return CurrentViewMode; }
