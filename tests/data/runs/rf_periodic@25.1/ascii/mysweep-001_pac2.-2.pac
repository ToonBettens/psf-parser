HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mysweep-001_pac2.-2"
"analysis description" "Periodic AC Analysis `mysweep-001_pac2': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "descending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" -2
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
"freq" 1999000
"in" (0.10183410508712891 0.0063361841174747122)
"out" (-0.096318022505179818 0.0052817407130644443)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020366821017425885 0.00012672368234949283)
"P2:p" (-0.0019263604501035976 0.00010563481426128919)
"freq" 1996837.7223398315
"in" (0.10183392087099533 0.0063290631935538052)
"out" (-0.096319185110184419 0.0052761971805883601)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020366784174199151 0.00012658126387107404)
"P2:p" (-0.0019263837022036865 0.0001055239436117672)
"freq" 1990000
"in" (0.10183334462062693 0.0063065445587948635)
"out" (-0.096322858258833202 0.0052586651418058952)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020366668924125461 0.00012613089117589519)
"P2:p" (-0.0019264571651766615 0.00010517330283611727)
"freq" 1968377.2233983162
"in" (0.10183158528101749 0.0062353314669011378)
"out" (-0.096334440438845023 0.0052032054590050439)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020366317056203561 0.00012470662933802306)
"P2:p" (-0.0019266888087769018 0.00010406410918010019)
"freq" 1900000
"in" (0.10182665106568631 0.0060101081570500432)
"out" (-0.096370732380687191 0.0050276411639982822)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020365330213137339 0.00012020216314099843)
"P2:p" (-0.0019274146476137442 0.00010055282327996575)
END
