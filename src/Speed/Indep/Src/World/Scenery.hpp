#pragma once

#include "Speed/Indep/Src/Ecstasy/Ecstasy.hpp"
#include "Speed/Indep/bWare/Inc/bVector.hpp"

struct SceneryBoundingBox {
  // total size: 0x18
  float BBoxMin[3]; // offset 0x0, size 0xC
  float BBoxMax[3]; // offset 0xC, size 0xC
};

struct SceneryInstance : public SceneryBoundingBox {
  // total size: 0x40
  unsigned int ExcludeFlags;   // offset 0x18, size 0x4
  short PrecullerInfoIndex;    // offset 0x1C, size 0x2
  short LightingContextNumber; // offset 0x1E, size 0x2
  float Position[3];           // offset 0x20, size 0xC
  short Rotation[9];           // offset 0x2C, size 0x12
  short SceneryInfoNumber;     // offset 0x3E, size 0x2
};

struct SceneryDrawInfo {
  // total size: 0xC
  eModel *pModel;    // offset 0x0, size 0x4
  bMatrix4 *pMatrix; // offset 0x4, size 0x4
  char unk08[4];
  SceneryInstance *SceneryInst; // offset 0x8, size 0x4
};
