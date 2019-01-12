# -*- coding: utf-8 -*-

#from midiate import Midiate
import midiate

mid = midiate.Midiator()
mid.start_process()

inputs = mid.enum_input()
outputs = mid.enum_output()

print('MIDI入力:')
for name in inputs: print(name)
print('\n')
print('MIDI出力:')
for name in outputs: print(name)

mid.stop_process()
