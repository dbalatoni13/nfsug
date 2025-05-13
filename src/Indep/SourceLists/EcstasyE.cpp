unsigned int bGetTicker();

unsigned int LastVBlankTime;

void cb_PreRetrace(unsigned long param) { LastVBlankTime = bGetTicker(); }
