HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mypac.1"
"analysis description" "Periodic AC Analysis `mypac': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "ascending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" 1
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
"freq" 1001000
"in" (-0.004143727377170588 0.29754942652592847)
"out" (-0.0043117505415516087 -0.28326526113053835)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-8.2874547543405587e-05 0.0059509885305185665)
"P2:p" (-8.6235010831031551e-05 -0.0056653052226107708)
"freq" 1003162.2776601684
"in" (-0.0041527159527748689 0.29754949018782068)
"out" (-0.0043215141930523504 -0.28326474891279951)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-8.305431905549247e-05 0.0059509898037564098)
"P2:p" (-8.6430283861045778e-05 -0.0056652949782559966)
"freq" 1010000
"in" (-0.0041811403010888187 0.29754969555445065)
"out" (-0.0043523891749450549 -0.28326312468928144)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-8.3622806021771035e-05 0.0059509939110890166)
"P2:p" (-8.7047783498902132e-05 -0.0056652624937856217)
"freq" 1031622.7766016838
"in" (-0.0042710257485238153 0.29755038548224949)
"out" (-0.0044500204893948092 -0.28325794395645559)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-8.5420514970468671e-05 0.0059510077096449829)
"P2:p" (-8.900040978789655e-05 -0.0056651588791291133)
"freq" 1100000
"in" (-0.0045552661775200868 0.29755297227404426)
"out" (-0.0047587183112340076 -0.28324111619819659)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-9.1105323550391234e-05 0.005951059445480889)
"P2:p" (-9.5174366224681217e-05 -0.0056648223239639224)
END
