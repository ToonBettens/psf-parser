HEADER
"PSFversion" "1.00"
"simulator" "spectre"
"version" "25.1.0.181.isr3"
"date" "6:29:28 PM, Thur Nov 19, 2026"
"design" "// Periodic analyses on a driven diode: pss and the small-signal analyses around it."
"analysis type" "pac"
"analysis name" "mysweep-000_pac2.2"
"analysis description" "Periodic AC Analysis `mysweep-000_pac2': freq = (1 kHz -> 100 kHz)"
"xVecSorted" "ascending"
"tolerance.relative" 0.001
"fundamental frequency" 1000000
"harmonic" 2
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
"freq" 2001000
"in" (0.10180003578705106 0.0031476099882449069)
"out" (-0.096773832317248759 0.0026523110819451313)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.0020360007157410294 6.2952199764902418e-05)
"P2:p" (-0.0019354766463449736 5.3046221638902923e-05)
"freq" 2003162.2776601685
"in" (0.10180007452609803 0.0031510653218574823)
"out" (-0.096773517788685898 0.0026552625262018068)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.0020360014905219681 6.3021306437152053e-05)
"P2:p" (-0.0019354703557737183 5.3105250524037354e-05)
"freq" 2010000
"in" (0.10180019852304406 0.0031619920424866403)
"out" (-0.096772522048178031 0.0026645955932272205)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.0020360039704608876 6.323984084973383e-05)
"P2:p" (-0.0019354504409635604 5.3291911864545137e-05)
"freq" 2031622.7766016838
"in" (0.10180060556969037 0.0031965453305994674)
"out" (-0.096769362101981851 0.0026941071528688992)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.0020360121113938167 6.3930906611994468e-05)
"P2:p" (-0.0019353872420396377 5.3882143057380127e-05)
"freq" 2100000
"in" (0.10180204212402419 0.0033058120632205429)
"out" (-0.096759258103298912 0.0027874090777464523)
"loopout" (0 0)
"fb" (0 0)
"buf" (0 0)
"Ip:in" (0 0)
"P1:p" (0.0020360408424804919 6.6116241264411717e-05)
"P2:p" (-0.0019351851620659809 5.5748181554928564e-05)
END
