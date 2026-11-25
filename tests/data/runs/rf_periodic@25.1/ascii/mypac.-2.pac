HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mypac.-2"
"analysis description" "Periodic AC Analysis `mypac': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "descending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" -2
"sweeptype" "absolute"
"freqaxis" "absout"
"operating point producer" "mypss"
"P2:r" 50
"P2:num" 1
"P2:units" "Ohm"
"P1:r" 50
"P1:num" 2
"P1:units" "Ohm"
TYPE
"sweep" FLOAT DOUBLE PROP(
"key" "sweep"
)
"V" COMPLEX DOUBLE PROP(
"units" "V"
"key" "node"
"tolerance" 9.9999999999999995e-07
)
"I" COMPLEX DOUBLE PROP(
"units" "A"
"key" "branch"
"tolerance" 9.9999999999999998e-13
)
"MMF" COMPLEX DOUBLE PROP(
"units" "A*turn"
"key" "node"
"tolerance" 9.9999999999999998e-13
)
"Wb" COMPLEX DOUBLE PROP(
"units" "Wb"
"key" "node"
"tolerance" 1.0000000000000001e-09
)
"Temp" COMPLEX DOUBLE PROP(
"units" "C"
"key" "node"
"tolerance" 0.0001
)
"Pwr" COMPLEX DOUBLE PROP(
"units" "W"
"key" "node"
"tolerance" 1.0000000000000001e-09
)
"U" COMPLEX DOUBLE PROP(
"units" ""
"key" "node"
"tolerance" 9.9999999999999995e-07
)
"V/Sec" COMPLEX DOUBLE PROP(
"units" "V/s"
"key" "node"
"tolerance" 9.9999999999999991e-05
)
"I/Sec" COMPLEX DOUBLE PROP(
"units" "A/s"
"key" "node"
"tolerance" 9.9999999999999995e-07
)
"1/Sec" COMPLEX DOUBLE PROP(
"units" "1/s"
"key" "node"
"tolerance" 9.9999999999999991e-05
)
"HOD" COMPLEX DOUBLE PROP(
"units" ""
"key" "node"
"tolerance" 0.01
)
"Q" COMPLEX DOUBLE PROP(
"units" "Coul"
"key" "node"
"tolerance" 1.0000000000000001e-15
)
"Efield" COMPLEX DOUBLE PROP(
"units" "V/m"
"key" "node"
"tolerance" 9.9999999999999995e-07
"sigtype" "optical"
)
SWEEP
"freq" "sweep" PROP(
"sweep_direction" 0
"units" "Hz"
"plot" 0
"grid" 3
)
TRACE
"in" "V"
"out" "V"
"loopout" "V"
"fb" "V"
"buf" "V"
"Ip:in" "I"
"P1:p" "I"
"P2:p" "I"
VALUE
"freq" 1999000
"in" (0.10180000015705054 0.0031444139750785591)
"out" (-0.096774123090033096 0.0026495811122264792)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020360000031410196 6.2888279501568142e-05)
"P2:p" (-0.001935482461800661 5.2991622244529185e-05)
"freq" 1996837.7223398315
"in" (0.10179996185478471 0.0031409586403923491)
"out" (-0.096774437292791934 0.0026466296038184464)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020359992370957026 6.2819172807845137e-05)
"P2:p" (-0.001935488745855841 5.2932592076368355e-05)
"freq" 1990000
"in" (0.10179984222564983 0.0031300319090266661)
"out" (-0.096775429775261421 0.0026372958952797696)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020359968445130025 6.2600638180529937e-05)
"P2:p" (-0.0019355085955052281 5.2745917905595463e-05)
"freq" 1968377.2233983162
"in" (0.10179947885713891 0.0030954785135435558)
"out" (-0.096778557141049784 0.0026077779205003746)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020359895771427865 6.1909570270870436e-05)
"P2:p" (-0.0019355711428209956 5.2155558410008796e-05)
"freq" 1900000
"in" (0.10179847908651739 0.0029862107069192089)
"out" (-0.096788335333168343 0.0025144118439015201)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020359695817303565 5.9724214138382983e-05)
"P2:p" (-0.0019357667066633678 5.0288236878030317e-05)
END
