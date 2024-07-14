#include <stdlib.h>
#include "d.h"
/**
 * @class a
 * @brief
 *
 */
class a
{
public:
  a() {}
  int m_a;
  int run() { return 1; }
};
void send_notification() { return; }
void send_notification_define() { return; }
void send_notification_declare();
class b : public a
{
public:
  b() : a() {}
  int run_2_declare(int a, int b);
  int run_1_1() { return a::run(); }
  int run_1_break() 
  { return a::run(); }
  int run_1(int a1, int b1) { return a::run(); }
  int call_3(){
    class_c c;
    c.call_2();
    return 0;
  }

};
int b::run_2_declare(int a, int b) { return run_1(a, b); }
int main()
{
  send_notification();
  b().run_2_declare(1,1);
  b().run_1(1,1);
  b().run_1_1();
  class_c bb;
  bb.run_class_c();
  b().call_3();
}
