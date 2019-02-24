# -*- coding: utf-8 -*-

import midiate
import devel

mid = midiate.Midiator()
mid.start_process()
outdev = mid.open_output(name='ZOOM 1 Series')
mid.send(outdev,b'C00A')
mid.send(outdev,b'B04B56')

mid.stop_process()
