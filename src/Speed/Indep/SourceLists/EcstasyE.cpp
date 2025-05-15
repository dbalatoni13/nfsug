#include "Speed/Indep/bSlotPool.hpp"
#include <dolphin.h>

enum VIDEO_MODE {
  NUM_VIDEO_MODES = 3,
  MODE_NTSC = 2,
  MODE_PAL60 = 1,
  MODE_PAL = 0,
};

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
  // eView *var_r30;
  // bMatrix4 *var_r29;
  // bMatrix4 *var_r28;
  // s32 var_r27;
  // s32 var_r26;

  // var_r27 = 1;
  // var_r26 = 0;
  // var_r30 = eGetView__Fi(0);
  // var_r30->unk_4C = eGetRenderTarget__Fi(0);
  // var_r30->unk_08 = 1;
  // var_r30->unk_34 = &FlailerCamera;
  // var_r30 = eGetView__Fi(1);
  // var_r29 = &Player1Camera;
  // var_r30->unk_4C = eGetRenderTarget__Fi(1);
  // var_r29 = &Player1Camera;
  // var_r30->unk_08 = 1;
  // var_r30->unk_34 = &Player1Camera;
  // var_r30 = eGetView__Fi(2);
  // var_r28 = &Player2Camera;
  // var_r30->unk_4C = eGetRenderTarget__Fi(2);
  // var_r28 = &Player2Camera;
  // var_r30->unk_08 = 0;
  // var_r30->unk_34 = &Player2Camera;
  // var_r30 = eGetView__Fi(8);
  // var_r30->unk_34 = &Player1HeadlightCamera;
  // var_r30->unk_4C = eGetRenderTarget__Fi(3);
  // var_r30->unk_08 = 1;
  // var_r30->unk_00->unk_100 = &Player1HeadlightProjection;
  // var_r30 = eGetView__Fi(9);
  // var_r30->unk_34 = &Player2HeadlightCamera;
  // var_r30->unk_4C = eGetRenderTarget__Fi(4);
  // var_r30->unk_08 = 0;
  // var_r30->unk_00->unk_100 = &Player2HeadlightProjection;
  // var_r30 = eGetView__Fi(3);
  // var_r30->unk_4C = eGetRenderTarget__Fi(5);
  // var_r30->unk_08 = 0;
  // var_r30->unk_34 = &Player1RVMCamera;
  // var_r30 = eGetView__Fi(4);
  // var_r30->unk_4C = eGetRenderTarget__Fi(6);
  // var_r30->unk_34 = &Player1Camera;
  // var_r30->unk_08 = 1;
  // var_r30->unk_00->unk_100 = &Player1ReflectionProjection;
  // var_r30 = eGetView__Fi(5);
  // var_r30->unk_4C = eGetRenderTarget__Fi(7);
  // var_r30->unk_34 = &Player2Camera;
  // var_r30->unk_08 = 0;
  // var_r30->unk_00->unk_100 = &Player2ReflectionProjection;
}
