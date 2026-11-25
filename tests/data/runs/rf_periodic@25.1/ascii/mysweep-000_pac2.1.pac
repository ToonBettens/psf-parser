HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mysweep-000_pac2.1"
"analysis description" "Periodic AC Analysis `mysweep-000_pac2': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "ascending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" 1
"sweeptype" "absolute"
"freqaxis" "absout"
"operating point producer" "mysweep-000_pss2"
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
"freq" 1001000
"in" (-0.0041437273768320107 0.29754942652581551)
"out" (-0.0043117505414949128 -0.28326526113057315)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-8.2874547536631289e-05 0.0059509885305163114)
"P2:p" (-8.6235010829898288e-05 -0.0056653052226114638)
"freq" 1003162.2776601684
"in" (-0.0041527159524363923 0.29754949018770788)
"out" (-0.0043215141929956223 -0.28326474891283426)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-8.305431904871748e-05 0.0059509898037541564)
"P2:p" (-8.6430283859912325e-05 -0.005665294978256687)
"freq" 1010000
"in" (-0.0041811403007504114 0.29754969555433775)
"out" (-0.0043523891748882895 -0.28326312468931603)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-8.3622806014995896e-05 0.0059509939110867598)
"P2:p" (-8.704778349776662e-05 -0.0056652624937863112)
"freq" 1031622.7766016838
"in" (-0.0042710257481852615 0.29755038548213658)
"out" (-0.0044500204893379381 -0.28325794395648918)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-8.5420514963692665e-05 0.005951007709642739)
"P2:p" (-8.9000409786757568e-05 -0.0056651588791297889)
"freq" 1100000
"in" (-0.004555266177181069 0.29755297227393246)
"out" (-0.0047587183111765146 -0.28324111619822867)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-9.1105323543610255e-05 0.0059510594454786547)
"P2:p" (-9.5174366223529455e-05 -0.0056648223239645608)
END
