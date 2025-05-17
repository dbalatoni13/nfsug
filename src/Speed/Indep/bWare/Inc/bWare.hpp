#pragma once

struct bNode {
  bNode *Next;
  bNode *Prev;
};

template <typename T> struct bTNode : public bNode {};
