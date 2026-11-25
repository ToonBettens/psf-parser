HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mysweep-000_pac2.-2"
"analysis description" "Periodic AC Analysis `mysweep-000_pac2': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "descending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" -2
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
"freq" 1999000
"in" (0.10180000015734798 0.0031444139748813358)
"out" (-0.096774123089953118 0.0026495811121701332)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.002036000003146968 6.2888279497627609e-05)
"P2:p" (-0.0019354824617990637 5.2991622243403784e-05)
"freq" 1996837.7223398315
"in" (0.10179996185508218 0.0031409586401952459)
"out" (-0.096774437292712123 0.002646629603762142)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020359992371016488 6.2819172803904618e-05)
"P2:p" (-0.001935488745854242 5.2932592075242689e-05)
"freq" 1990000
"in" (0.10179984222594718 0.0031300319088293903)
"out" (-0.096775429775181651 0.0026372958952233234)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020359968445189504 6.2600638176588374e-05)
"P2:p" (-0.0019355085955036326 5.2745917904465588e-05)
"freq" 1968377.2233983162
"in" (0.10179947885743632 0.0030954785133461621)
"out" (-0.096778557140970362 0.0026077779204435178)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020359895771487335 6.1909570266925864e-05)
"P2:p" (-0.0019355711428194059 5.215555840886873e-05)
"freq" 1900000
"in" (0.10179847908681425 0.0029862107067211503)
"out" (-0.096788335333090142 0.0025144118438433314)
"loopout" (0 -0)
"fb" (0 -0)
"buf" (0 -0)
"Ip:in" (0 -0)
"P1:p" (0.0020359695817362949 5.9724214134427969e-05)
"P2:p" (-0.0019357667066618026 5.0288236876864468e-05)
END
