#pragma once

#include "./WCollision.h"
#include "Speed/Indep/bWare/Inc/bVector.hpp"


struct WCollisionTri {
  // total size: 0x30
  bVector::bVector3 fPt0;               // offset 0x0, size 0xC
  const struct SimSurface *fSurfaceRef; // offset 0xC, size 0x4
  bVector::bVector3 fPt1;               // offset 0x10, size 0xC
  unsigned int fFlags;                  // offset 0x1C, size 0x4
  bVector::bVector3 fPt2;               // offset 0x20, size 0xC
  WSurface fSurface;                    // offset 0x2C, size 0x2
  unsigned short PAD;                   // offset 0x2E, size 0x2
};
