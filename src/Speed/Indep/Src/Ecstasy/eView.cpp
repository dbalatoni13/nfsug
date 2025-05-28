#include "./Ecstasy.hpp"

eView eViews[22];

eView *eGetView(int view_id) { return &eViews[view_id]; }
