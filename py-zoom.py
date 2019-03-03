
import midiate.zoom.g1on as g1
import time

z = g1.G1on()

z.connect()
z.clear_patch()

c = z.make_patch('TScream','HotBox','MS1959',st2=False)

for i in range(2):
    time.sleep(2)
    c[1].on()
    c[0].off()
    time.sleep(2)
    c[0].on()
    c[1].off()
    time.sleep(2)
    c[0].off()

z.disconnect()


