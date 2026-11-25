HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mypac.-1"
"analysis description" "Periodic AC Analysis `mypac': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "descending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" -1
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
"freq" 999000
"in" (-0.0041354133856660053 0.29754936818967631)
"out" (-0.0043027195928730519 -0.2832657343048367)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-8.2708267713314226e-05 0.0059509873637935244)
"P2:p" (-8.6054391857461532e-05 -0.0056653146860967309)
"freq" 996837.72233983164
"in" (-0.0041264248031704729 0.29754930571239102)
"out" (-0.0042929558257953247 -0.2832662452213085)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-8.2528496063405678e-05 0.0059509861142478214)
"P2:p" (-8.5859116515906765e-05 -0.0056653249044261609)
"freq" 990000
"in" (-0.0040980003859459584 0.29754911219183028)
"out" (-0.0042620796881332476 -0.28326785643215435)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-8.1960007718915562e-05 0.0059509822438366007)
"P2:p" (-8.5241593762665086e-05 -0.005665357128643092)
"freq" 968377.22339831619
"in" (-0.0040081142493995966 0.29754854072479703)
"out" (-0.0041644368159840508 -0.28327290703818225)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-8.0162284987985734e-05 0.0059509708144959402)
"P2:p" (-8.3288736319680446e-05 -0.0056654581407636498)
"freq" 900000
"in" (-0.0037238669287230934 0.29754713854802711)
"out" (-0.0038556234165556097 -0.28328843352065419)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (-7.4477338574455268e-05 0.0059509427709605409)
"P2:p" (-7.7112468331113111e-05 -0.0056657686704130791)
END
