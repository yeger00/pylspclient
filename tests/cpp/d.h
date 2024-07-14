#pragma once
#include <stdio.h>
#include <stdlib.h>
class class_c {
public:
  class_c() {}
  void run_class_c();
  void call_1() {}
  void call_2() {call_1();}
};
