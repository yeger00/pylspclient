#include <stdlib.h>
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
void send_notification(){
    return;
} 
class b : public a
{
public:
    b() : a()
    {
    }
    int run()
    {
        return a::run();
    }
};
int main()
{
    send_notification();
    b().run();
}
