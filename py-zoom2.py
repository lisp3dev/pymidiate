from midiate.zoom.g1on import G1on
g1on = G1on()
g1on.connect()

znr,comp,amp,delay,reverb = g1on.make_patch('ZNR','Comp','MS1959','Delay','Hall')
amp['Gain','Level','OUT'] = 40, 120, 'ComboFront'
comp['Sense'] = 6
delay['Time','Mix'] = 1000,40

input('press any key to turn off the Delay')
delay.off()
input('press any key to quit')

g1on.disconnect()
