HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mysweep-000_pac2.0"
"analysis description" "Periodic AC Analysis `mysweep-000_pac2': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "ascending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" 0
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
"freq" 1000
"in" (1.6125648439935403 -5.3073119206210048e-06)
"out" (0.36901654220601554 -5.9934643318511484e-06)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077487031201292113 -1.0614623841242208e-07)
"P2:p" (0.007380330844120318 -1.1986928663702217e-07)
"freq" 3162.2776601683795
"in" (1.6125648432322848 -1.6783193923814173e-05)
"out" (0.36901654132080619 -1.8952998361504745e-05)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077487031353543241 -3.3566387847628368e-07)
"P2:p" (0.0073803308264161378 -3.7905996723009316e-07)
"freq" 10000.000000000002
"in" (1.6125648356197257 -5.3073119264944042e-05)
"out" (0.36901653246871519 -5.9934643244622971e-05)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077487032876054976 -1.0614623852988787e-06)
"P2:p" (0.0073803306493743131 -1.1986928648924494e-06)
"freq" 31622.7766016838
"in" (1.6125647594940915 -0.00016783194109536105)
"out" (0.36901644394775213 -0.00018952998127841477)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077487048101181899 -3.3566388219072789e-06)
"P2:p" (0.0073803288789550461 -3.7905996255683138e-06)
"freq" 100000
"in" (1.6125639982329589 -0.00053073125136088892)
"out" (0.36901555873304609 -0.00059934635853425822)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (-0.0077487200353408385 -1.0614625027217816e-05)
"P2:p" (0.0073803111746609243 -1.1986927170685114e-05)
END
