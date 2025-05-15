#pragma once

struct bNode {
  bNode *Next;
  bNode *Prev;
};

template <typename T> class bTNode : public bNode {};
