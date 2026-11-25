HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mysweep-000_pac2.-1"
"analysis description" "Periodic AC Analysis `mysweep-000_pac2': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "descending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" -1
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
"freq" 999000
"in" (-0.0041354133853274281 0.29754936818956329)
"out" (-0.0043027195928163646 -0.28326573430487162)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-8.2708267706539304e-05 0.0059509873637912719)
"P2:p" (-8.6054391856326982e-05 -0.0056653146860974222)
"freq" 996837.72233983164
"in" (-0.0041264248028322183 0.29754930571227783)
"out" (-0.004292955825738692 -0.28326624522134314)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-8.2528496056631434e-05 0.0059509861142455637)
"P2:p" (-8.5859116514774397e-05 -0.0056653249044268626)
"freq" 990000
"in" (-0.0040980003856075512 0.29754911219171704)
"out" (-0.0042620796880766462 -0.28326785643218938)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-8.1960007712140694e-05 0.005950982243834349)
"P2:p" (-8.5241593761533003e-05 -0.0056653571286437937)
"freq" 968377.22339831619
"in" (-0.0040081142490612093 0.2975485407246839)
"out" (-0.0041644368159276064 -0.28327290703821795)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-8.0162284981212737e-05 0.0059509708144936798)
"P2:p" (-8.3288736318552875e-05 -0.0056654581407643593)
"freq" 900000
"in" (-0.0037238669283847971 0.29754713854791309)
"out" (-0.0038556234164998393 -0.28328843352069177)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-7.4477338567687651e-05 0.005950942770958271)
"P2:p" (-7.7112468329996599e-05 -0.0056657686704138285)
END
