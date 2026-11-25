HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mysweep-001_pac2.0"
"analysis description" "Periodic AC Analysis `mysweep-001_pac2': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "ascending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" 0
"sweeptype" "absolute"
"freqaxis" "absout"
"operating point producer" "mysweep-001_pss2"
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
"freq" 1000
"in" (1.6125105120371377 -1.0472782963298915e-05)
"out" (0.3690981354575299 -1.2128105786410215e-05)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077497897592572725 -2.0945565926597697e-07)
"P2:p" (0.007381962709150606 -2.4256211572820308e-07)
"freq" 3162.2776601683795
"in" (1.6125105090630025 -3.311784738612669e-05)
"out" (0.3690981317663859 -3.8352437663216454e-05)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077497898187399673 -6.6235694772253562e-07)
"P2:p" (0.0073819626353277233 -7.6704875326432654e-07)
"freq" 10000.000000000002
"in" (1.612510479321656 -0.00010472782203227488)
"out" (0.36909809485494854 -0.0001212810465482719)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077497904135668981 -2.094556440645469e-06)
"P2:p" (0.0073819618970989822 -2.425620930965424e-06)
"freq" 31622.7766016838
"in" (1.6125101819082748 -0.00033117823350551473)
"out" (0.36909772574082217 -0.00038352401879439355)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077497963618345222 -6.6235646701102866e-06)
"P2:p" (0.0073819545148164486 -7.6704803758878491e-06)
"freq" 100000
"in" (1.6125072077830738 -0.0010472706195851348)
"out" (0.36909403462422363 -0.0012127991497170017)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077498558443385452 -2.0945412391702649e-05)
"P2:p" (0.0073818806924844773 -2.4255982994339926e-05)
END
