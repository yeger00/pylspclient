#include <stdlib.h>
/**
 * @class a
 * @brief
 *
 */
class a {
public:
  a() {}
  int m_a;
  int run() { return 1; }
};
void send_notification() { return; }
class b : public a {
public:
  b() : a() {}
  int run_2() { return run_1(); }
  int run_1_1() { return a::run(); }
  int run_1() { return a::run(); }
};
int main() {
  send_notification();
  b().run_2();
  b().run_1();
  b().run_1_1();
}
