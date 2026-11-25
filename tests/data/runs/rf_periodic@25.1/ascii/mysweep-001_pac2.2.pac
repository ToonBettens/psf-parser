HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mysweep-001_pac2.2"
"analysis description" "Periodic AC Analysis `mysweep-001_pac2': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "ascending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" 2
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
"freq" 2001000
"in" (0.10183427632909663 0.0063427705799892695)
"out" (-0.096316946702495007 0.0052868679565156148)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.002036685526581942 0.00012685541159978322)
"P2:p" (-0.0019263389340499005 0.00010573735913031208)
"freq" 2003162.2776601685
"in" (0.10183446238563756 0.006349891416687012)
"out" (-0.09631578312345962 0.0052924109480410675)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.00203668924771276 0.00012699782833373676)
"P2:p" (-0.0019263156624691935 0.00010584821896082052)
"freq" 2010000
"in" (0.10183505704007928 0.0063724091792135519)
"out" (-0.0963121002345005 0.0053099375773169605)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.0020367011408015919 0.00012744818358426831)
"P2:p" (-0.0019262420046900076 0.00010619875154634095)
"freq" 2031622.7766016838
"in" (0.10183700042035998 0.0064436135487811992)
"out" (-0.096300420651156252 0.0053653431651323703)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.0020367400084072042 0.00012887227097562021)
"P2:p" (-0.0019260084130231267 0.00010730686330264713)
"freq" 2100000
"in" (0.10184377503630697 0.00666874963514218)
"out" (-0.096263154653200039 0.0055403665182490328)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.0020368755007261481 0.00013337499270284082)
"P2:p" (-0.0019252630930640014 0.0001108073303649789)
END
