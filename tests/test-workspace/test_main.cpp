#include <stdlib.h>
#include <stdio.h>
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
        return run();
    }
};
int main()
{
    b().run();
}