unsigned int bGetTicker();
int bGetFixTickerDifference(unsigned int start_ticks, unsigned int end_ticks);

unsigned int LastVBlankTime;
volatile int FrameCounter;

void cb_PreRetrace(unsigned long param) { LastVBlankTime = bGetTicker(); }

void cb_PostRetrace(unsigned long param) {
  unsigned long var_r30;

  var_r30 = LastVBlankTime;
  LastVBlankTime = bGetFixTickerDifference(var_r30, bGetTicker());
  FrameCounter += 1;
}
