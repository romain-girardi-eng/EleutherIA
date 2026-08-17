#!/usr/bin/env python3
"""Canonical-reference payload for the 709 Plotinus passage fragments.

The payload is additive and contains no replacement Greek.  It records only
node identifiers, hashes of the untouched descriptions, half-open byte anchors
in ``TLG2000.TXT``, decoded citation states, and the new reference metadata.

The builder below is retained as executable provenance.  It:

* reads the four citation-level names from ``TLG2000.IDT``;
* decodes the IDT's 190 per-8192-byte index entries;
* checks every IDT Ennead/treatise/chapter state against the redundant block
  snapshot at the corresponding boundary in ``TLG2000.TXT``;
* decodes every inline citation update in the TXT stream;
* aligns base-letter-normalized node descriptions sequentially using unique
  32-letter anchors and local ``difflib`` verification; and
* selects the chapter containing the largest number of exactly aligned letters.

The last rule is needed because the source fragments are fixed-size text
slices rather than citation units: 265 of the 709 slices cross at least one
chapter boundary.  ``citation_span_start``, ``citation_span_end`` and all
chapter votes are retained so the selection remains inspectable.  A tie, a
weak alignment, a missing citation, or a fixed-point contradiction is never
guessed: the builder emits an unresolvable record instead.

Run ``--verify-source`` to reproduce the payload from the live KG and TLG E
disk.  ``--emit-payload`` is a maintainer-only deterministic payload builder.
"""

from __future__ import annotations

import argparse
import base64
import difflib
import hashlib
import json
import os
import re
import statistics
import sys
import unicodedata
import zlib
from bisect import bisect_left, bisect_right
from collections import Counter
from pathlib import Path

STAMP = "plotinus_remap_2026_08_17"
LINGUISTIC_STAMP = "linguistic_repairs_2026_08_17"
BACKUP_SUFFIX = ".bak-plotinus_remap"
RECORD_COUNT = 709
TLG_FILE = "TLG2000.TXT"
IDT_FILE = "TLG2000.IDT"
TLG_BLOCK_SIZE = 8192
TLG_BLOCK_COUNT = 190
TLG_WORK_URN = "urn:cts:greekLit:tlg2000.tlg001"
TEXT_SOURCE = "TLG2000 (TLG E disk; Henry-Schwyzer citation hierarchy)"
REFERENCE_PRECISION = "ennead.treatise.chapter"
ALIGNMENT_METHOD = (
    "unique 32-base-letter anchors + sequential local difflib alignment"
)
CITATION_SELECTION_METHOD = "largest exact-aligned base-letter share"

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NODES = ROOT / "data" / "kg" / "nodes.jsonl"
DEFAULT_TLGE = Path(
    os.environ.get("TLGE_DIR", "~/Desktop/Romain/TLGE")
).expanduser()

ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}
GREEK_TO_BETA = {
    "α": "a",
    "β": "b",
    "γ": "g",
    "δ": "d",
    "ε": "e",
    "ζ": "z",
    "η": "h",
    "θ": "q",
    "ι": "i",
    "κ": "k",
    "λ": "l",
    "μ": "m",
    "ν": "n",
    "ξ": "c",
    "ο": "o",
    "π": "p",
    "ρ": "r",
    "σ": "s",
    "ς": "s",
    "ϲ": "s",
    "τ": "t",
    "υ": "u",
    "φ": "f",
    "χ": "x",
    "ψ": "y",
    "ω": "w",
    "ϝ": "v",
}

_PAYLOAD_SHA256 = "f577ef042fa02063dee9d05251d3386d69af1f4476a38ca6b93ed7a57ac73ccf"
_PAYLOAD_B85 = """
c-oA;+j1mHa&7r9@thBKzwmv&BBiCoZhqJ@WH+U&d1lT~`0ul}xqBdxnTTXp7sBCz0(O|IsqSs2s`g)x^|!yRHvjm?fBx;y$G?34
ugCcNfBx;CkAJZ?f4km${7d-uIR5&NKmYm1pMU?)e~k6V@sIYu{(b%JpMU)IZ*%>>{P4HOzqL1S+x*|(K7MnoAHO;N?l;@={&%~a
UVeA*{^NJ2-~4Wu^ZVbOP5tk`e0%(L@|*wb(f{r5<NyBS{t(rCdvva6`^W$J<KNpq$G@&WuiN8a+kgCX{o{{+{Qckl?eG7ai|5<?
y}AAz|M=^F{PXYs_*1{sJpSeJZ-4#UdVG6WF8^HPpMU-P-}uh)-Svz3&hy>>b$+b>29V(W@#jC=KmPeg|3Cj+kAJB=p+DQduRrd;
{eh@3B7gq%|6BVfx#3JG|GhudAAkO9b20I&oy{TSlFc#l>?ZqaLNg((c*JExa^CrwQVPyn*Vk&U*yf{6F<Wzl1B8D+jz8Bw|CoRM
bNu~p|NQIU{`0T@{Hy-lcLwkufB%1U_5JZ5?ax2k|5|_i$G`nuKl0}v|NF0h)IaRw8wOPLH={p#i0$w_&D6q?dowG{d_+@+&(+Vc
%u)P^&DojUu~wPOAFi3lx9ok4nU_#(_@;k+_-4)i-}5!v`<?6M`}JB}_=~=r7hhp@k8h5Ln2oXX@WquQj1ba@(U{s}H8J~jG~;c`
%UhGpa&yLT)b3VFwXWWMdz>H(FUdG}L#Z`~7{6uai;v$z{)99>k;Yi=Th67we9I;A?;Ftm@eLzzDaTU73O@SmOzaHY$Sy3)MRR@j
kb_@ld9&uosd`gaUOlvVRA)A5(0aYt;BN>u*pfcR*WLF&fsWsbWpvYi`3h!u@S_h5){HW(wY{uqFo|{aRkBMlVtm%EFb+PqYirC5
z#L~kT53Fs<>K);@yQPOIOz$qTCDsDGsG`&=4u$xn$L@`pvK2HJXdMWk2HGhri_)nu{MFuxitn4aSUHdS-dflsnZ_QPk^Q)+sa2<
;ju9Wjc9Scd_c_=GkA_@`2uPv<u81x=fzi0)8iYCFwa?M?JZkAn@@GRbQq>tNY#cBt)~6aVwt_wmFB3S%;u*lt25hter$}v@=~L%
A5asI;$u|Jm!s-5s@KI=Q1w@E-(~q3`|z`LJPvbyx;5=uafMKUSEnx(jCPnf4)0xI{1;Cb@5E<$Y>dpR9B_3{L^nnrN%ZEM|2(Sc
36+_A-%9l_-x42|f4>G@9^VL2Ip)svPR!udiaA#6CAriipJnw?64R`gU|OC7{{{X4iUXL~i#_DMgjS%f_fG^BpKSeyDdhW&PoUGc
=o!}N>v{1N)cW{F=#8u5vV0qPSnE^ly;>V_2gfocGxghSv&`8{H+I-n`-sUg35~<v-FTcBd6vON6F;CvgWFBDgj~OQ_X%nKKzjcd
`J1ztEspRT5AJKwma(x!)iTB?VO3&+Cs2gdCyro*gk99R(l8z4Zavvi7-Yi$&%?!)i*dd7@;LEUUOWbJgQ%s}XnwNb{24dyKyxhD
bY6T3R<Vp=MqtuVX1pj^oU4WiA;@K<I$Fb?4U>@n5fF^4k(p@-Aqshc;P==lgUlh|drvTh=@x6^#ns{%M)wJ8d18(3zLN@;%kR)5
dxM&&W(jL4G4Fgl4#Qu;1BYyTBKAgbj)bK$FP&YfrGbYVrV{4NOm;F$`KfIgz|~(%&Ri3$KF2m0tMC!hjqZB?`}Hl{;=UEKys)N2
d1KF(z{c!&960y6#%et5;-kyWDe6u)Rtlr$<Ywp?w8J*K!SelBB?M<}BO-_X*nq7@o9C5p5ST_G)IKMlf1-QEeYxLI{d+%barah4
TK=tImo<*k^te5+kG2{^Ji_5^pUFpDZwE6Fi?=uvMG85Hw!s38mts?Tf~}tSng1{WAbrA$Q9rR>(~ny)5XP7fnB%+Yhd;H%I{e$f
QJ8861DINdb#yu9h|L^}puuNw{x}K@q9x6|=?+3jkK8v3%fc(z)z@-^z`<GnG5!4WjaS^f=9B@;v)LD4f@R`Zq8%v32ttVbWdhxZ
qX)xi7P~C$hWS%{>yR6udZIQlF_+r;<-?~w1-1r5w2MYGZG*5H;}|rlj6&cKSnU(5yDXerQCu=-d}V&aCM<zZa?9ZpJTuQEA20}P
cScNsVKp`{q9No5rg7whI07pk4S(1$lyHF3$i+qc9-~D-zhVVW0xK4uEFKfjw`UIae*63NEyHl%ia7$C&ks9z1Dii6c~%H*V+1S&
MNsEJHS~1^eHe!sAR0`D)e~Ui^w}N?k`PZgePBehOar`LuwA)gpJ0PKd=Pm5ME41|<8i=&Q_1JWmtYBgJhVqi(Jr7ZmjZ+657;|T
iHGkF8!T2GqM4zr1VhGjS8VoxPw-}Tu%X9^k~k293)lSeKgo=bcdnQ3*K1L%<I8#RrOY7c;r1U$qEy>-M68r~(AYxH5*zK9)pbIK
80V%&&abo_-t0iM8Hu8_odqx>9yub7uA!6A5V4YIsIt}a32S&_wHJHh7D^A;m{##`=AR?{Il^CUM+w%n?n0|$#DXNMskz{dUlo4r
VHCCu&AI4!Ygu0wer+5UXD%KnyiA*j>MS3yG31Z2zD+oM#?6N{iXO(F7hi&vmLuw6jRgkmj+EeVxVX`5wzJrJ%)T`2t%gXb=y5nm
G@r&Kd2G}1&4+tzlv&Oqr+apZ8e`p9r$QpL&VRxhpIB{u-U>z}u0rDK8$)&kJtsN0qHjP;J;Q-hX&&BI0)u;anEtAfcMXp#HVB^!
7?JlKp>O)(TeFW7ug19K+XUjzhHRhkUV%puy}#(odGRG$qMlRKgKApBhDYElK2$<qT@m{$P&Hc)Td`>$GWsY;{25qT#_5@i6!jZz
Vdn9IU&tSW>|FT>(YNFM32e^NAGw?tUxFppIju+?sS}DPTBF%G8j%jR4gqqxWVGeB?g^K`V)+Ddl~G5r2Lu!qV#MA+$;0P|jr18}
k?0YyWyqO_kd~)G#OvJ~so!!>cf6<%4*grU@2r@=h5~!w2Jofb;&!J4TR4o#aJ4uLA<ZAeyCcFb+#p<=ibOHE3^;0v#kMIe3fPSq
8FgcTJB9M0nm5(d{U>I<@QME-4u4*J36xpw6y#<)s`U-xj%#yFQ9{~u4VGSfi+w@VRuA1}7#-3R&ePp$MBGZ4n3`^TJ?fjxVo#nE
DAsH~bG4s<M!DQ5jrZ2~64rPKkK}vr$I&g(7;o8mpuVJ;3AxxnK%nxyBuEUS!0w|Ny(2I(PTSSIfr1b>n?eZZ$SJBJx#H*P75A!%
zJ5Pna`B?S<-GV3C?O3m{=g?z<IrgauFiysxkO7~=ndy<qNZLL_}Mk#$>RvCIHrvq3p40xYfli$&=L|dT~K~>1U~)>Y1DjDWQp%4
mgjE}*dI8kX&pMwmVQ+DS#BmQ$7MF7PFM^Qh=^4VX}SX*)G$%k2pVP{S-dR8V1zWe623wjeu-2pmoMkVmq_t6o(R?wRtF7m6LwV&
sWw~_;5?6XK+K4$6W<U^f*sT`OPGhpm<Q0|#g7x>=BvrnACMwak{-T$0qSp{{0G+!R5n4E|C)c_K*rJtI}h~tj1eQnO*LaD^E+V=
YY@OpfHh2UO6g}*J*s0^2(MNtm|M>5g){!NR1id}#tVa3n5&-&y6(R~_CVH332b3sd<j(RkVGz2WXyP@V@70I$F~w2@>+*s%#IX!
t1q~?JJ1G%wceP6&7^hIY@^>}Tk^I7=4Ac=N~r!E3Vs5bvnEy!=f#&m@rD@DqjWsGoi$`XLTd$8Y07K{v0!3DV3xI-K?+wM=MiQa
0nxzZBP29t++!p3`m^@riW=1_vGHLG!C&{!uiwuX0?1$Fk<W`Sf$}GqmygUtLWa%a;vlSgQP%8wZ*Z*IZEsqY#xsqzh_rkZ=90m)
RnL#`xgHy#qHA^`=Nl+duD(pG`b(fe!YtPF;!B`JDKBA`1ETzx1o{=RxyBGDB9e1MVWD8N!A9fr4A`g~KU~2u3B5tE8xcbg7OUsy
V|<P%j`qd*{}L#EgZVFU6W)YVt#lIQ9*L*k;Y*>d+~#2&nwPP4Gq;fsbflM3Ec}zvWGESD`W#^eco<?~1BI0t8Cy&z(7m$DC;xc#
?z(?|{eHf{ax|jhy!a9*QHsg<@O3n%J243<PN<3=3LQ%+gIVK^@mdUDE+fS7yaa~>8ao{^;7Gn6B343JrBX}y0J_Om@?HcagcqFY
#tA>WZn(Prl;z)dLrb{Ah8{hZZjF~}%~AwJQ9;HMGvXYj-YdGCK`VTshWmH59!*<MM~KJRh+|Q>LR1%fVE}RZc~+%Y$mt$h|9)r#
(F&#WfH`+Ul|KseX*A4qj_5ijfVA<)3RqI<Ot1iRNiNMp3zW%KsF;I2JWhmJ#1jR711(z9{Z@^Y1oQC)XTEV_&eshsLCdYZRWgAw
36foDhOP5bDb>OO3e&!Nw0SXmIk!uR$FPu-EtgRWPAnhOu9~5|iU2~&IOXc<4S|u>s?iS|Fux)Or#7OJyDq*2il@QoA8@@RWT+=@
sJE<zr3tr#Zx4b1&)gPAC=Hdz?M5oTG`wns7+?v0Y@i_2Vyp?aUQm9LF7B5|<@xz?UVMp^SQVtQJoGLRtf%CEW`1jr4^h&37vm?E
YC~-$IP}t9AoIo&R!8(5CWy)B?bLX&DcP@(re7h=3Z{HHFTO;oZ8L(^^0mPe!m*A6$=wnjtG1bYpAZ&{Cx`oY?W*<YXW|oBJV9KL
eYDM91QkRfmCX48DNe*H_P-8kxq$|I-*CxkaO-;_5C~hinn#DJ@Vp&*G$lBBmb>?+yH>^`d_`gx=DbpX>}ih&hm4=i5tCs4hzNj{
5S6u~QZ5X?RIqyE1v9EOTOqaQ#g|BlTRa>@3+!neJks7hbDOb*n6|L+T9asY%<cjamI2HNE{mmfF~@39vkbqGilp-reZEJlV#Gww
nu_yJf-Ris)-2%M>x;VKHelRCdIy-uLxg!$19vG2D}Z1#yFBa!Ko)RNS#cT@x+RiX+eUTFH?+8Q69N(Z%F+ZSAQuF<Y-<n%T!Aa@
bD&LIWnGB%61B%0`LXzRvzPc4h+jA?$a92B;oY0jR(bSR`VcikWc6+x7McR?FbEdb!D>6B7-q3Rer$x>1|Wy&2{hK1JwKm*1vGoD
a{6*!d<m2}92B<dF&8L?_Ig*3DdCe^<wGW>JIENojwdJ<p8;!GsQrq=z(@3P9NPr46{9P~=M&0a<iwhYrOD!wf_=g1Zk(bK=MBHZ
fmTZ0o9PvKdQs^qxXQ6|LS#3FxR_K9EP@edpt8}19x5y;+PY;S+HUrWSq~xuUPBy4P?_O{;S5j2JRSKY$LG5dyZzOlh~W);mq9md
-rHv8y^@VQ#z+8L@gS~Ze+|typs2)Yj1r2#EQ4UdVU__Tas~zgea!QK${5IDV-{(-Q&9KjeYW|+APG}{*rZNd89X6-C0zhi>c_sZ
+DHI{7d;Tw&ac^ts<v82txo*W0Z%Xuo`sA?nN(btTcKH{hlDab?_{f`SFO~8&|wVKLI|Ef@t;4$ub+S-@F83Fy7&?(@e7`VD9o@c
{xSmxFU8nIvyoqT{f>Qh1{Q{+#X>Y7D!jKAI;tia)Qr|_gs^&T+}9kQK#hj#)6&3CK$CcO!h5E7ggY`Z;JOb!dDWJqbAA%X_}kSv
rW-M}Fn+D!HqBhbiedWU2uE64RvHLSEguSBLWp7VFfOa~d;dItJbG_`2~<z~+~<Gy=#}%K#X$si>J9P)Ln(O#EudinH3aA)B6SuN
7;|K}mg_P(ca%U2P3cl|C};_xQX!(L=>|&t!=1*Em4D#<6KB5tm51(|>xQ@5Ruba+ChaE@yrM+cLSF+{(u%2{A+N(rgCY_qF;(%5
P&Egh1$_o_sKHxj0q;YZ{&7Op(57?$P#756oc2<Nt?m?ud3&yWdM<sFw#Deixs<__d~dbbTO@jU+s(pQ2Qmxh0jtH}TK7qLG{py~
I3dH1%7_p6HtrQ`J|?34;K%m#0%}nrPxAi4AYTjf{zPQ+c3n@%n*Mue<9YEVQ2s<DdM)U*hzgo@Wj}3#enGGu(hI^G-2h(9{lHS{
T!n|MG#jAhf-~D2jY0^K#S4_Qp~z|(|G;p$Oys$S)?II2IBl@kjbtTiQhdLU8wq1dyiAaEXn(SVs1mht?{EMC3)NWjS)ka8_y@xu
%S4y)8SoS<E!<bw4gsh#hAM7)A?Eqymz1S=-G71XwKsh!@OOJiiRhJ-?@<~NW|(GN4WqS^D)E&kj*DnuQMwfrW`uS?3;6*9qZ#Hf
YZXG+9@<LOktiirJ%K{|L4Z=msrmGRGu$}6jn@raxI6;^?cEZ5B6<<m9}p4{9|$Ov%wd`9aQ~?-&Z$+n;VU#NH$Fx1NMBq>TSe(M
Ln(sVA{SJmJ5svTbYXzXK)Qak+VBdQe{DJ)!oK(tDA6lv$Lq+e7Ub7NhGPw;LIn=Hy!fme6>8uHk-HmZga*twu7h`MI<$~z9w$Pr
OKNBO23oYk%(U<Uud^2lZ=CVQ>1(`hIPGp=f%u4b#(?ulgt1x&8imM&MSA=VaaXw=F-^D&4k+>DEs`eLBexc3km;a)!?KmT?XjUc
4Xuyq2F0VnZGQ-cblrb}9Pz~j1&<Ti7heJ;jPZLPZTLCxSeDRVW+Psquq!spZ@}pn>^H@>GE_^8b4sxt6CzRj!a2|WI1$QEMwinQ
s1_DKh(Y)j(4y><f>oEd>41bWe8t1#U$MyJXwa*p^ME6wVA|LYI~sypd!eub<{6JQ@B_p%69Q8|jIK>cbZym!wn6egfr>D?Z@3PR
v$<^b#F=iKc%bVB9PV0;O>YQzQU)Votd*V_8-#VkO(_$pLk1!W7S7m+5q;IxmNJH;Ht4L<SBoP8TZ5XYj}xk_7Q!Dc3`{SG`;XHr
y+Tg6SPbvQV!}D5oxq5^?k1)_lTpgwfPQ7O5DaysiQtJxFo&-WnrjU|hP;I3CL|lATnU9jC>wya+Z!nI+}Y2Y96tdiBHw8;?;I9?
A`!jJ^jhLJ<*0e$1B}5VOeG?X+3}eUx7x+WrfBx)M5Ts$bfv^Jdft8jghBfgxyI*+hOBvwLbA{3b>hr7&S>m)W3L$GB*br`SK{gM
<Q@}dJr{NZ;|g{js}hnb54tTV46bXA8CE)Af;a+V?=e${Q@3DyW(qw{sD;>iCH4pd@fLRUnI-1auilUWt#m0u;(7693agZ}v=@Q^
;a}leE+cLGT13#av|#}y_u&}5Xn~mM;P>WHhUVCg^v1nug-Zx|-g@Zq<bBHj%gQ`TMa1k(5WjJj8z+3@x)HS^kIieQzCkPrt&~M*
;E^Uls@ewhV=Y8!*JeddbIt`i2fZRtDcK9pIwDj&YM~ZCn;s`rFKu#9ud=Dk%Xa5AwB;4D642sh1M!U?*gL93FLabf!Jr5Wj84{;
V1zZ{Snb3ZFai^%g4%MvmKI0L0bU+E!lKI$2%&5sxM-h1(X}7b>mm$40F5DP57C|%Ujh|lR$AhUu{K684E$-Z#dlX*fl|eliSzR?
hdT;v95(1t<{4Kuv{2jex_v!Pg#2NcWPSow5?=YdwDA+rl*;9>(mP|-q69%J<OQuVzH9qZ0Hszt)c+XEScr`CeAlKQjmN1K*tD$z
@e4VUFxm*kSeYCjk3Q89fAp+BJ$ezBl+KGUfodx)DzDEWRgG1q%T&$)c3Kj&+bE^dXxD%Ng@XIML=I7`d@jbW2jCV(SGyA$2x~E>
=ZKn8UOcP&<%nv>U{C*dTL)RWA8Fetlb)xW8JEde*=e+OaC8aqd@PwnXrBMC0f#b&btTr2mMsX6J()mAtg<B~{{$NI%lg2tM|7v-
oVk1N9{t{-`u4DBWrv_f4JbP&ND4B;ZJKDMQda8DTBuAHtAew|w7hoZ8T=NGWBVx(s<5NxoS%>0aq~BmDTz-dCGfo?R#{?Bu?qf-
|CvTxF!(1d&N`ewP-4?RaM=JWFh=<qCGu(D0Tu~4(6n{W`l^iL;vl{8g7V{9vHPWe@>;v%%X#r7QZ4oqqbhV{La4`~RO)h=Bu9>l
QZ`|dnCSz40`r34HNsNy7{@Awo2wN~dqKoM;ZCdjm`&0A){$x?^RCi(Go)n)?r)Fi+JQQ5W8}I@lVVYUNQc4VO?yRxV{r-KmEhHf
57w-bVE`TT-lSRx`NIxP`Qb=y3GTPkey8)=^WsaOiq}@#+W=we)XuOqEd)2%Uxn)r?ZmIFr662E3=E%~gEzzQ-{1hyEr$q|5Ju%(
=9dwL;@IDeDBMB&TGz#wK%M>s6cypY0|$%uE<*j#&Dnb9!rmU9$3ZNIj+)Mp7b3t~Zldu~3`sjRj}u{14H`oA2^2M$KJRDzJfc=3
>f(9vB~bBpg{DvmjCRzB4qQD}qWv(cP4P*N6qzzxR_Z`qcKT%^bQ(8SP+gws^VkTpY&4l`de^;E7~SVw5#2w(em`H5Lg%?G_$G!H
LKBhX;o+fHA(LUTe%b{!Z7ZZ;wI2^xQFVg1#s;4<OqzMdZQ^OJQ@gW|6CsY&L8<){XjYt(fK*yWe8FkW4K!MJ-*MW>ILnvbIDkDY
+SU@WUqNe>xKSc$9V?=paHj{F8!3y45*e0NF$IqR*<y>b{)274kH-mCR-hG{8w8-;%Nk4Y_ZzRUdCe*T+GREGYJrMk43P?*c|@Xo
W8#=tZHLjhwIZL?Yq6c_FQ&XO2gnk#E)s+xen;lPtT`ViO3kgBFZa2@Ci7A|@io|3?mU+_(W(%wh}sXHB{La^@6k5~#V;PL4FRj_
2!w3PSg>8#z|qmxCVA*Wst(@QoZYS!ln@mUhk6}Z#F&<)oN`J&W3^ALNXq*b1ou`g?~GWUM|)f*A^2xtS{Y<@L#h%9Ceb!w*Lj94
+GXsj+FCjsF^nmQBuA}=simxqH!FqT)F%jFYjK<Br3%n{1@?OTUV{be6_&Z>jpm*#|6N&4QLwDqnyVeRuZ?4qSIUPQ@&ahV>KSSg
7l!~#s=FarxZE>7tVEn#cE?r(!iybyAFjD)wG10=FgR3SMYZC6f4^Ldg;q;+_P*s!xpL;;72;LGn#!+jEV&#o1C%TmiFv%5>mJg-
h6}jd#18}v9<|Mg=<^Zr@G8YDD-kcel1)6I`oy(UVsKvuTAR)t`+a}ETnlmfwwn8vxAE3rZ;V7+m^{-5swy|-5O*1}gSf-9Tv3W-
&EV{en@4+Pq(t%#4bk?dDeM&?Jojh^<?R&+nz@W2e#5kl5o=X$=N&tCd35=9n|Ao-Za2fzsQG$xm*?g3K1NqUAA|I;5ZB5xRdwai
=sG9$0wRM24|(y}QIC<J?3B?}!)C~4jNX%0CJUNOYY9HpS}zEUx$;pyEqau_%W$DDJO6m6``7nLGL_I*mC@0L3LBwiRhx}UmI_BM
2nk3n9viKwtY4@^)q0rStK@{WQkk$$<&Q;qo){x+a4#WjpeS?ylG#;$1+-`t8I^oqd<m4$r+WUJTZ9{^Zafg=s#X+%nvQB3n9D56
MQeep$$J&r<-2lITT80qer$w}zvh(``UDy@RG(PSPe2Ka=v*bMr#CAHm3W7}JpzHl7lgtt5Nk=>bg0GEO@dae5s>5!&sva<P0xEo
6G9uEq37<Na8<R%C75%6seC)DmZJT<Yg_g%NI7?F^pceeK_ogaz68qTV9q|oACwQ}#?YT0DolcUdrYjR*@HHc+;9yA<hohY80bM)
y7y`gOMPsFRzR(-HxzM+7aMiI1RAx}i5xjEz68oxRH?F~5QBq9CsgUK4vR>(4Lhxai!)<pf;+A@yv+w<(;TZDvmXHkY`26ELVSTr
UegT}8+{?XA^!?!vD??0^WsaOM7CO#akdPCh5_=$9MM7&dc|*<Q4ei=W!U#xzE-O&=zPQhdruR&xu(s2lROZ@BjIn?$Z7uz=dttV
9V6ynarzr4vH!XeqrJ<B-`RkQpQ{qPJzSwp?~bYB14P9tvRtNBn6pP!#Ta=nUk;>{l!S+_C3GjBR)kVe`O_h2%j-hyLw4?S$$r`U
N>9jF!kGm8+sre5hYFsxhS-%^xR8j|BWYp0Q>D+jkGX91z&1ghFf#Et;?)eCq9}<+g`=(R!3`2-MOlI86c4+q^~F;;cilg~e!spc
StYIRy!aZb%AJk2zM|Gpn@E@HB%;b;x@E-Tu(>ba7ZzX-*f8=8J$Z~{DvLgMBv|f}lEO%+45|1V%uktI<yTlS7Fn!2FTTdAB4<OS
QpsN<KsAfM$5PAEz9Ot_rB!+!>xl45m^f-!_2Y-J%7!5T<7~^`M-WKZSl|ixdswULZ(udC#;ca@MjD@^dijj_&1v8MOpAF}vuIS{
Y^2wC=xW6Q{U(TFyB%RG-2gjBk!k%n`bAs{2T~(=YnwyEfra2}ly<qnYMv=hTqvrjg8k8I<16SZ-At*qZ}ZMDML|`iS92=89RYIX
qnfv@gJ*79M*_Rj$1zrm%MHll0Ublc9f9`=1;^-Gjoug;UbR%oPpCD&<nXxsE2vSd77}q@d<|74&BU3<+8(AA^kf?lyVyFjs-e;j
WOy4#*wvs|a~}=CD`H8ci?}c2lPdqz^8lMF(Vlx?W$%9&2-=UF<$m}3`GS<Yoz~k4rh;ap1w{y-88Zf3dl<zjqeyiLY9X<d;X5Jd
zA~$3Z_0^aMjF&cQf*_(iU`7p4vx<F_=Fl&wee}4?kA{0&t0D=yf*+9F`F#;TTzWpjYO0St8`PS-bl#af|5Vb=?jX*G!IER$p=B7
hwsZ2OLtpDJEKz5s4SEXChwia*Np^s-9Nv6KVPmol>9#Z)M|@Oli`tPa+=(z1i2mMZI|V3AD*eD%+1)4+_AvSGq*DzKwJ3`8h>Q3
ZM2OMx5b08{sQw;JyQ84R+WY;kfeA0hOGPzUoh6j^nkdeId>>^gA0fjyaf6`tUTJ(Cf9Jv@W~)|Nv!Kon+atJZ;-M8hW7-cC1vMd
mz2$Q|NQ#>d?93O?c1IgU-!OH;8LrONd(1PDP=ex9ks{!nQ|1!fe0+2tJ|aXzWDznBG{P_WMfQ5{qRb^2cwm6gnw>jSjAjpLB(i(
*HG_4E!UeDQore=ZUmpNz2)%E7n}_{h+v)&06{f9g-nF<@PLGpWin~d31jL&r6P7FR83KJDYaQSwd#7>l38G(TrubE3pQqAp`wD(
uHUJ3H#oj-#<jmG_YH6NhFwsK%{$DBWa`&ZJd+;Xt$c_hPeKIlNGrEf#j+Js4aFTWF|8l=Y;X+*S~imQ#ZQ_TRif}sIlkLZ)nAp<
)$5HH)QSdLN=Wg%_!_Gsn0j=0=OfbOKqIOW8IQkA4Df(um4y;qiw3z{R)@&s1JRoLo`6_HX?rtFAPEb}7#lAzQZw3)b7`;XhZm&&
M(S(5ZuqmP%DrD~vb$4<T6L^CvYK0ESoKlofH^^I-1MsdX_ok{bU)_baN8{Q-h*+*meR`Tdxg#HtdnH@-o>eB3X*@7is8Ed0$M8_
Nm8+%7hgkFC{ue5rus4DHkoKcIY#&>M4xdfbcbC{OISnIj5?R-fwrMnz@E)v8(!{lVq^{_J)I3^r}RV@KYNF>u|Ylg*G>SJqDj`A
7hgkFC{uF|OE6HIp`hF{m3&%z)TM?H8I}MSz+K>f72iBAEGuwC#Mr7a*Q3el3ZpE+hnjAv5KJtYc&&apKE5E0H`1_|)OEw{ZAZ00
c-wktH|9`hjxuc!HSn<S-Lzm$uD#{?o1to^uB^%C@d>64<gB`NIK~!Q++r2K6<8i;+Qn8UiXS%~Z*(u9<Nt8u(e7p(>c-I)a*UW_
$Khwta&xuufNU)urnNv1Wdge#O8yGITS)F`iqN4!(H|RQ_DbT>GQA3?<$S9ahLqPM=VmU9=bIN&wJ<wxgrJGW!%lDI!|utUrW_sW
Jwh#qE!Fe_<4VwTEti^NhO(tR&S6Zi9V$z(wm64@IwOE+m+G;>MoqMo%o8(%?>-eUpZ71&=S$KexpG9)yVY{5h8$KMIT|yEhaKZG
Doam!s<tj=3_068O6hH3BX$M(TL=Z_3;_xOn}~-BHaA9D0<tbVp?b*pw-`X2q|85%x*MsMP|q7)`mw;=%e!JLt8N@3P|BR@s-jW#
KVhySUzphj@iiADJE{(3zz)o6t!N!|9>FRgC*@ZuwM}5PK$Ebga-qPFiSWO4)I0CLfOdD^9`l>NJ#KfPa;g9r3|1X#EUEQzwJcoO
V#PRDSV4^_^sZtsUs5}?uewrSYD%Q4F)ez5F#$CjXX6uU3E95pO#A|BQu=I);k@`7sv?>iaHM4dvGl+t%%dn1ftjQwn3WEERweF^
#_Wp&hCa2|*zDSMcd@6jx2C|T6rXJ4WweS8KEp?tXKD->><dzVBlRg?H-g;PxiR&wzmU3cShe9uWhJ!-FtWWAmGn_@xkg=i4z)~c
)pvq$Ov@rP+hNtRP>tfI(!=*QjF=EF5F7u*Oyn`I-2A-%0-E_Hbq*mtFTRGVh^8hSu!4?BTK>>rw3ubuTs4LHXT8(5NbGqYBcRi8
7~S_H2Dp$?(|8zrc(n)nO|7%)-3>y7p}JRY^U)<DoKTgHxOaETdGR$=MKtx^SP2Mo7VVhzf%6^AaAnc+ShZ~p;aLM~R9}dJJZ~N1
*qa)PR7O_ZMi_}`S+(OAm|qkL{tD~=s7TPNl0)5}9&j*7IHWDWx<hE%CZEcb<FT|pXU^zFd!TZf>I7HA=MJlaw+s>9i%MDP?z~7m
pM5p7SPREhyC|gvUvc1Sx^W|QmtCm+hF0uUYWRMpDWs_rhhrqi*5m3Ha2!182{Gwa<-xE^NI@!NsR4sCYvL!EnMY3QQ5&-IM>klw
Ic)a=w;L8_H7tagrL%3`32wjn{rpBLxaW<qTXM*e#kb?Ekfx>_OedAwXwzdxsKQE#05_)=X3SERX0^E4?vd_1jjpaeeyH4Py5Rjb
->eRRB^U9)3v<o(wS>W6_g_FO=<d!u=Dhg2d7eU=x^i@bBY=w+*QcG$5(jWqZfS2Fp58hPN1Z|<c2dVM40HF*DBG{0gGFw@sO>ow
Go<J6*7CZzlz#;^s%>oqYJAtf)~YLqRa*``!eP`;t|%YCjM|HO|G{F>jd3(LAvRfkO}x^;teMILvWZYtn%NnvU{r>(7EkYoU9(e~
U4oCPl*PUv%}=D4tH`or`P|*r;T>j$H1*|h73CZ3p>Ai3=O4T~U|Ni(DTJ=9Bs--wWo_?;E}XV|tu;<S?;IF`g_<MUQn^s5R_rDE
UQ8mtg3fo|a(bV)Z2j(|NJ#4*IX>hWP~~G<ta7<F{SnkHcBzUK|4Wc4TNVc%g({!?m@&3AHN3?+Er`h%-Xpl{$IEY_*2`$$`Y~-8
SoP+ZUZqSUYU4<KI6})aO|5`9qxHI@bE&L#yezt+*3m+Mk2knin%WH97>Q)cS&7e4Wl#ZQ{nqRD1!=jFh7_(FZg;g+?~8ZIi&mu1
s!hilHWVb`VCwXst@Y8+Ik4O#8{3*gGbrWWVA@BO%gD>vVTwZ#mz}-<Sn)oz@HO|#-k1*gM;=yQLGMB+8SQoPHB^N(HR?bY@O*oK
6=IE!sgw+(7E2G=r-l}2$F9L1Rn2;>SCQMY$F7dst17~%=!*|5rzPwrl?qinv!ZOeSEThu8t(67-T8rH=5H-RkxeZ-vWl!2o~~Nv
bd08C_E6N*W)7u<;NxIDZej@Pel>B%QIEqg?7nT|Rb9F2C(H}vy{Y~Kb*!(L_597<vf~{MQ(>B_=pPmfG~nYmBheR%an8n2D+_NS
zdST-Faetu!nM?(#FjqHGR?q%6&%30OFgOzEw(_|c`V^ILnz;GTrc0R*Q>|1`weSU!w!}DKD@f%tQnc%!&sOCVYM3P4>*?!--mHK
h47G+tgbs-9qynt_-$@}&$a3kZlUhn%O_liAt=2-d*au~-e~O;ZMgpn{vUVlSbSenYPEu>6q833C)Xaw9JpI1&sqfCQS(x>dDq5L
dP{?+HJ|Z&?bwSVXgDU_QeBr2%OubgCEPHy*HakW3V|rv>$&dlms_tvd9uH6`OSFt^m`ZQ)W}1HeGg+*=3rHGquTg-9Lj&4$rYvH
cL=##YEzhJB!n+w@+2UtgSUl=?HqR@hEYP7Z$XR>3OK`}tpN3yzWA7OZM5un;Z}p3t6SB#UH+EKZ)Tvjm#o@)EYz<*%5csrW$ZBC
B83-mnkeB8bnqDS=-pw-`01cd^f2JYkM?BL*lEMXCs%b3y+I)L+^5y_^ZpaGUUrGY*(&Sp04vg|ug5|i&ZVw6a2THa3Uz7uR>@3W
39u28>Mi`NG$-z3$As~yy{&pQYrPDNS|w4d@wCD0+IUT?Sk%e&6c;yAcO!*LUpIo=iF#IPo9{61#=**kJa!$?Ko_aUQ*pEMohd^t
Ac2R(Citl?*&L&{I=dHa{I9R$Ol+#V%DB|zgL`7$v+$FHbKl%6Xm{6g|90Xj(y6nD>&P=`Z+7YkYax~)<`722B*fbJW+6D3e#sD>
=L&tMg?G02mAv-wCbdc`HAm;qZfKZq(B^73Ca6}=J(2p`5cp@)4&8`mSC#npc>z1w-m1q3GYdKHa1o_WlVXJNsLO%H&1IvqP0hXu
yxChn)aJii2$5?jkKILjgH5~;kZ%;bFHt;4KAyf}gX8NSUBAnu<8@<;IUNBJ-&(Okp1OQQb!sz^*3==nF%Eb{cMfoPT^G9gD*7}%
lZ!~=l@_@Oc4BL56s>7(tg;BjjtfN1>ZtHp&iilf6|=hvH?sc?_feY<t3Drxwj-dFGeW|qZ;)Rs0pcE!z7y-TvesCWN>c+2P8=h8
kGwAgAr%@3V^-rN7tdkzXZs9wWOfpY*XX+I%?qjX_fN;2D7G_W-|0?u{II*_hpKdv*3TpKT(XT2J;m9hG6xT(K-cD$Ri}>$@}h0+
L<H0ZXKRlWECNGKuFQqvCtV+Icps?!+4M8p-*o@9>h&Qt{uuCJ2G6SVd}F@r2#4wW9Jqg{k|{n>>lVLvBol`^nIMshS?Xixwa>gk
GNi_<;nZ_{McC9jL>Z6%1!=gErev-gR@*A)ro}tqscs)u?LMl!*FvCqmukbU`K%3AC&y7oP&d<zp)7)({Iv6G&h2--@~oj8j}2A<
*@R%rg+dKVUMsoGOB=uov^wu%wPE)*duP7t_hHrWL#Z|>vQltqOHCShys$T~*7wC>ttKe(N{gvFXv8As7l6|!Iv_)zSQwq4M(sP?
P<507?8xj+3GM}HypgJ#(s^U6jr=>^sm>oN!+Rjp>r^}4Jcv0B?Fp_!#pmi39=j{Pw`EijpVVK`wzv!d(5PDkB;v8L>W~k!Gcqp_
%9Z|9jBwt6!5mf4buXa39bH8>HUFqd=}V=fBbKVX(HW|jiQ2p9IqbuLI+Kb|F_UWiC4LM3t>LQrR30MY9^I)n1R*@3di#<==;E)S
2KD|4+D(4f1jxqS24BgJt}9=V;HE)}R!x1!L69H-qularS%v*mEn<_ixxjI(iT=nsxJb=3Hb!KdQ4^IX)S!6-Nw(@^^*X5OIjFW?
H}>wzPI`Ph%@o+w|HH#EAY7gJfH=~D4XBHx+@+BV!5BiOLtS)O3iPLSH8*O9(a{3|yHrjhSefO>QkQQKT8gse^Gd4!mR>RI1Qjj%
)^J{Y4OIb6jX#j~dFtegPN0wKjZ@?3%%tWF(%4|VxgTklsv_gjC5}&39SXU_j@DyigsJOD6YHN)x2pfaW`BTs2DIObd3FBK9>@a+
3vuzsENKL+l_)kcBn%!4wLOUTxL=hbm~JrR20J$d<u;OvuIA4Aw#o>_Uqox3P|IF8(X+63=sl6<8>zo6S;f;u%V!vTeS3t10-BnC
bd%c{>u_~Cb$&CBSmjYMYx=3GgQ#}AsRw13;f1?;hZFUN8;K95RBwSLE+AtsbIfNojs3g;;m_U)H|Tty02JPz0A$tu!>av9hv72E
rHD1@Azu|rP>u$j#f!OSVqY+etmPEKMJ+=*ezgOxnWkcc)u~Fn1gPW_>aL*NZE(_U2q)5VBRv(WZg}he2c?u&I#F9r4_n4zcg5+!
Q?%-%G}I*={mf(m`jN6SNe{I+I;va*KS*e^Jd&mS;tdvez^|(}il6v`zutI3UH*sd*sT)nt$KhUdGWa_IYb8aFoG*3&85<wUerU@
1PtPk&4!}%NP|TlgU6thDW%YDkX0`=+(W2lCGk^6;V+<K+d8+(oflt2RUlLI4;>l-%N;~8gY<<h+7%7@Yc2wBYzZB#z7?=?P{R?_
(a?;pt^h}K+Z2e^L<g%+@`RfBV4rtaeu7%Go>NrR{&rzUTclR)Ka?&3)RLhB$X2hcaR>L(b})|{;({ZcwjV`FypR@a`*KR4ZdRR2
1huHu2d)ogbT&5L-RxdYfePlje}4UbzMQq6o7}#m2kQS})d0lI!yYp+;~Bd#>~xG-oRxu98_tFSYw{6>wTP}_rGt=b4>xcCZkK&n
nJ~13|0F)45}VbIy=uw#nqVi=a{+2Y4duSG`_`xq^zBYt+UL3`lr3yQS@BtgfhlO+9&^N6v)9sw@(9zhT9Fn)i#3c@ry=C-t?sH;
#b^ap4bZRnuvemtJJ-)FQq0F+qIUQ9XTN*3h%#@dnu418fefu*%%<ZCcMY@h@<#D$avY>5M!_v(0BUW~YQ#0eE(yqd(xmR9j}xs3
AQCiwfY!M#KU#$~pI~pe=JaB3%VVsv8MVFe=q?|Jx`4Dp=XM|`k!kY9ZdUwjHm)(22htLvpgP4ol>lY6){wIbH#bflQx(z&oK4HK
mY^7pn=agM+Yhup-M3U9dN#p-YtRaA>J6gJKBFw@;}}NlJd}n(Ox1Z2JEqY(({gxYrl`(7ko4_vsJ3+InJOAw(D579#S+Vn;s=)&
o`^pI*CLL&PC;;QkNQ!7Q-_e87UQH%*2AZe)R96$s7`}Pm^`{kL*+E4#~```?0gusd#`HSE3XDlT)8&HFGjH8Is&z7>Wc`3|Af{(
(T42qTW%lrqo&C3I(S=UX4|~0v3Hx{fuB$!j@lH=*{!T19dZzA(8M4pdm4oq{RmJqomJ!~_x3nv$#s=wrh3EB&V2aPs_%N^6LP-Y
oJY+0E&J6HomIOK)R$LhuzE0{7I!?(9<K3Fo5rK>Ge)%D(4_25Rs}XcHd0+W?`fB}@e>;7>MxPG;d=kNFHpXKd$pX-?^{k=^$bx5
(1+@(ja5G$IgMksIAIDvi(SQYO$X<oALdlX<n*c>4@ZYD7rw-_orTU_LQ9~HKSo!Dbh?R`Oi#18(E5+Ty;dod%e?cV%x}^))I!9n
hlp1x5KJ6r8?;O^j!}A<h)SbgF+qEWSUZYxdSbbm__s0CLrRN+S!xr&T7U5N%q#F$)n#}IeK&Cb8Mv}b>J9hZQneb1$i+XD?^=LL
fRHB+B_2wDGs?4Hfygq{yCcJcaT5W*vKC{Ut&U)VhwNHHl{accQz;*CLwY%n#+NVP<}Kmkb@4S^#Xa>C3F^Ax4#GmH%97No9z63n
^3h@zJzueO2Sau-Xu?$;(n|n0b&I9P##wO>UdKb6aKhQgQ}H-x8Tw<?ueWcs%0Itud9CaORSmwaTgdxFvwS8TW#z*pQ3{iT9i<TP
(*m3711uxvS4WT##d#Rr8G=hbW~lwxCB0rN7OJrFA299#uBtap-(0%i*e{p3SCwl{_bss^wXBckEpSCa^&4TfxK<tfmv|EFQu~$#
Nt1Y2jqYl`s>|nrO4bpYEwlqxVr?3^6&+I}#FBSD#@qkKJ0bkjUig0F6YwjmIw_&`ZF;qOj#xDvK?P|Mz0Hv#s(m<OiZ?NtdK}OR
bw%SzI5_gLYJ*BAq^a5fFK5-1>~Z3ZT7oDpe!%rw8~H)x{|xu+=dm-Z-;J(1kLXabM^N_8V!EfKGZWN7;AqnhL$vdY2qLUSy?m-{
JZo*G=-^L><d04|UpR{lz+7un_9J*;M~V<P&5ZZ^H(XcJeJhl3<@LNhp-*WTR=r39{tJq!6xvpd5)xs{so7z3OCFwXOz^}*oq#uT
?76{N)qy~|WGW{d$g1h8UYp@J3@xjb^rObJ=`-?lc1hdKKHs%Vvua3U)sZA&5~&(BP7eezow3p<<e7Nrq7r~x?y=$qr;gpg!L4eJ
sbX=Xyhce<FTn6NW<dFXtIBlsN-k%G<}2F#L>p?jZ#j|ARDaX5c4u(zBg+keEv^g)atE9!jAN-puc(1)DMjF|&RbB^QUm#@%)Wsu
iK-cmDx4Ey9jdJZMcfTT9n4=^K6-P%@d-KK7IpfPnUr_)Pi$B9bPp{*Vi1if#QY|>rFE!(Ya7cSYbV=Pt5af<(j?|?xiQq?Q77K4
W0!neHTZ!atCsNzH{=()zUSXhaCaiz$ui!Wg~Fd&l&so`%!g5Dc;!^u+*Oao{8GKX4k^!d*+m%XZFu!-NQcTw)Rz|iFYg9}*3Jg8
amS5tR_Lg)U&Y+>dD!m_Hhi;BtozgH#<qmK&FI~Vn>v+PwJHfy4V*fhLdE(8(P2spL+6oJEzGMgFdBpFkmHeyQdX_bx*Nfbt~&FL
Rwfb8M5+z?JdfiO!wBE(2k7w8V&FIDa9I5fl`cL;$QYka<Ahl*iPg#lfh5g=e_l>mQz)x6)pT{JO<WDIPm{ckAXKe#kO0)7aUq{a
uV`Z~?zS~(g<4LTdLwl=QkU~}Bb=F`@iz;aWuM}yq!e|nw6jcxvN^R>!<yl7sjE4WmSK%{<zb}}<gkm{P@q<&W~zWts1{iC6GXn=
ur$1{?Q8GP@&a1zb$2bCJukk7s%WRqBu1y!tJ>U}l(faHZrnPu1n*^fh;w(|L9R~4;?Sqt&CO8x#A+ho<HV@hhDPyEsLAK_S?T=*
HSZH$cj4wcsA4WUJV|+K=(f2Vk5q9saeLEk*LiU@b_9_Q!b;{m(p9Irs^=0s$u&5;n42(4IIE@gm7uCt=W+(S^!wb|IFZKNX3=%Q
UpM?doMmgLcWhIgNUU0s5Nx%Sne3tGK4+E4AmHK+bS7$<u^kRVp+c@X6S`V`>$NI_?Mx*BY_N=IG}S*b6LDgC?QS1mQf|Lr$zYma
XU~*(6HUuc>cH@D`v?Fxl|nVtVB+A4*%tPuTvOUOTups|{p{N6p8de6_hQlV+CAME3CAjmjCV=P&qs*-0_)jiF_rgC7Oip(tvZjW
OJ*|4HAxveoX~jHG=_cN3Gr^&(%`*16RE2jqagO-KdI|v;+$j(0txAf-n;r7R;7r2UdQ|iD*yS_7dF2=BUj-}y+>lmV;*MU#n3`{
Dx=hfKAJ&*dZ(5}Q%!(E!^<Igf=VEbTT^F9HMOu3#yzY`{McYVvhI`WZ2g&^c0+YHRF~>?BkWFw>33&7s||@(%O9<;<#de5q0=D5
&Sx&2xR8*1sdE?TP6b7USO&2~cmOXF`g%Ro+F_%`fyFDm@)KxWMy}t&eg7nt->+|My>9RauAugIHAO8+RN?wiLonugN=v*9xsL}`
2V0#f617sLKJw~JfXH*D^uzR?;KT)Xq4L?siB?9D%_h9@S2+gx+w1P<_iKwLhx;_Vx4ukKO>IeLTSe=`P%Ipm_>A%j3`UwEHrA;-
fzHS+N!_fvag)%8`Ur99Pz0@R12RStg|m+6Iu8%0_&Gwv=YeD2&zB_6wU6t0@4^(!)R@GlHh1%4;54X?jy}*4<yHqsh_hqVexzX$
rfv>sf(}g7ehA)ps+qw)*<}~L`6r~RMq~AJuGG&^>t?#?y!aaGK9IVq1*eV%Nl6Ff9<wHf?l^WA@j(=T)avw@vDD`QapzYf?AcgV
lXIBe+guoRmU=Sjnmk*%?cvg^KN<RsG~P(v^#S;2uSe{D6!G1u)caWKeUN9@ft-iBS`T;tGx`Xy*&fXlhk&yX;2^eHEqRrSwhMew
p?u02WVL|JI`@L9>u=1(gnbg7)jE{FZ^!cpx9hUl>xSKD`ljEUU+>hT#HmNgVF?r?@3euHx#($Nm#K6{7s8f?nJy_)|A5aFb-2c*
O%>4wq^CHqz!Hh&Ms8Tz{Cw%B6vB1?1#~*K<=(M>Co-K{lqh@t(Pqv~jd+^^y;aH5F~&qACv|D`Iw^DNct@vIO@t#{NBhf4_ei_e
M;Ntgl7g-EhFUg#{KRyBf_ff?q9!%(4nuJgSWcZu)Y~2vNnBEwB)A|P0f~jh5?z%?HhL!lW3nkS1)Xi^dMGX<jb$jsSWLmxeF93o
PC)!B0O#xL_wyyG$+^;xQhGbAI)hrRNk&1{@K>N;al&q_PQyjqst3?93trYk7SS_c!#TSGZ&UVUQ?J|I>}G?M1tgs|9Ix~7_LkQV
PT>crXGz)bHoBblRh?Rs*y&URfI>^Hdv8sjI$jdHa0?X!uPMaP+EUjx2NTEX%!x3yZ==1i$B7XNmU2xe)ZOhti!@rKP`Ugo((*(a
uJ8BKWZA7V-_9=`K&=)f&BTTC)NxX<1B*^@LA~X3Qm0^@eusJP+JRsp5XoRahA;tm!kUUlHr62hs3NBuG6Ws`jGf7Ma5zIpJt3on
lD}>^<r}G|&D&*Qr(Pv)_bQp|Sj`<NtV3r{B5HZyBP+F?>0(AekKu#sVt5hqs)NYdv-fL;5XEznQjd^k#$Akd@7L-m#80ch@v4`;
K&y$n%1ui;FTRGV)2P*}q&Eav6ES4$@Uc3Y!7-gwIAo(~fiY~%GVQ@h)DOHa{{=E*L2CB)mN2T?$@=Tj*L@yJH9rR5AEEA}=bS$;
zJ{vvsMV?jaj1&;z|4xxF*$q}Pk@q5Vp~Fc7o8}e^B-4G2T8(*LCss8NH>?{85p%;uRY#NKbT)9PR4T&F<v{K`*pYcQ0?5?-XBi=
O0@0!7)JeN)hOj~Lq*4pD3*)yxLcHPW>)1!Ackoj#zi#;GE*h#A+@&jYc|lJW{c5WsKm^Tj-^d%f*HPD5#vT{pJ;6<_bu=4E^%+2
ugYtjnwH=J9CkXCLjWn$Iq!I@sjimzI>lr4LslL$dMz(zq1PEomT#gjO+pRC+MI>0R)52|2RKI^EUdHSt~d6}&D5pV^L@+KeJYt+
z`yfvYF*;gy2M7ElvcGzF~Tvb+#Qj&b!Cd%-6t?(L8y(=wN0dhN-FH3=WsxSHSq*l)|@1XE*PrJc=-Ug0(PH~>lj8^NJ;0#*Kif(
)V)Mq|8Tn9A9aWT2TS;Ml5<LA)+yj<P^i`s;4T3#VKu@!tR(1s60JspQ_HCP%<AW;{d~syukl9h0_Ys!_-;GEsdI@_=aPVGY+=H5
)xF&)X<c1wGyxUobo6Ub&p^g@*<mUwzK@FQ4pEK#wnYO}?L*5QmG|)OM!D#q9X~#guKz$=(|ybC6AORWDA%cviOTgKQ(eN8@dbI9
E2erB9k}bjH4f!_+9PzPp7%|y1ySBDY7uCfgQ<K1FFQo58)>;=?1MAXk8;TR&&YL{%|6LEo)=%kRm|JHO#G^d$(|5C1QbR`iC(=m
Z&p)cK3-ZqOUl8lLj_H%Ls^YFotfzOCVp0-gQ#ycPgF39h%HDYC3BPajW#_sJ>Gc#2fAbZo_&hhZ)cyv-fm|SgEHsf@V@G_Cet*F
j-f;Cr?=fjG~B|Zb<W4&F%*}#OVOzb!AdC?6)CDyqYXETeZHFiyuh;$1iex3LpRkFS8Lk);%lf1dunGgLWk43p$`8H=`o0CWwq!E
w6PtkvyT=I+7B2)%h1j>N7mBzY6^^xjWKGS*PkjqT}3au5DLKd9N-(NyOCOZ-$>6>b@E%ctoWyPCfc|{#S_=m#;WL`2cCPkp+GRz
MVK%7Kq2vw(p2MW!Xoo?sMlmvH$;Ke9)1ZWp2K){hKS0B(Spo9y7!yk&u{EzrTb7rt@-IpZtUv~X4QZ=^)(@=wW&r9FpJTWTBG`@
W_@TMTxzRv@YKZbT`)0^!3@+{dxv_MCoe@Ouu>W6R7blr59Wm&=d<Xf6(28f=bPWpZ+yCcn%N^~QGY{{)z?IQGaf!_8}8skBQq<3
#2*$R>TNDcPKi^!{6-%|N0#^n*??Ipw~b((+TL^#*nJd0%r}aUBaf?655ns?;_(C>uA;<UE45dtihqB?sZ)m&rw%7+G1Y44BLYoz
Zx-w`9X|U3_fc0r{74G{PIMqrv&~g!bo$EACBH$dWO5%1aLv7a@RkwJ#N<jkm#%MNmrl&$`{lafccF$)?;FTCwK{QXb%H&2<B?7T
HxzI%IpB$hmIdPka<onj=yb;DY?zDA1%g+ra|;@_OE{IXGcb2<%Y}jn?qB!fZn!U?)7hYDbGf%FL>*3?I-G=E>=2Z3X_O>mCz>PT
MD*aNg)oiPThs}7Xi%MevUD8c#60qBQLYWuZ+5;~4EKOlbtnrurWa=aiZtJzO()*nH+)WKpXZ$3u?w|2(NuZVBTk++6KYH~^Hqwt
T4lrS`fRgcBz@r0AV?w|hecZtmz1`4guT@uuyHT3pDRG;0i8)2=aVkY+sR#^^V1#gV<X<VW3@U_nIptv5Ev{DO#8A6PodWJxiSf-
$wW9mRIsCE)QpiZhul(Y69=;+x`?-dQDt0J#XcL%_H(bTgnYd2pI^V9FG*>DYRI16<pVmcemHeHSxYBK^Oq4!5VA1U0&A&_o6ZR$
{ONF>cvvN8r=cz_YMQl_{fM9z#}>wVlFIAZenhu~<kr!L=>@94p*ny6cr@-lW4gQpt#GGSC*e@`O9)BLSysW<_VZ9nLWP=tmLq5-
P)E%|X$U7iWw($o#z31?%ec{QVQ1=%qT->|71Jj*Ve#b#clP`~zX^MDSvTBnsBFXg1x%+_C#oiWXt76s(;S%X=+3oirw#~aE*^F7
(s>4wnKyK7u97?EQI6=8C=u(niKHwJop7;TSNYW*%#HVny6in<bG40li&eXmI%EBTl%7=)u82BHRxCuZ+Pfc+V{Hf=K_yUXo4T?;
jy#K-Ms4yO7OpTSkYOhh#Cycln*Z~8$iIRrk|sHu-W`AH)ayh`ciPS{cB;e^_K>YQo+uBkGTb7S9mi#@v3^)>yhSDUsY|?7qXXQD
G)L9pC%jan#+g?W@L={S*QPL{uD&33H&PqIbz`4%u@CEeS5@G&-XzO<Fi2Y3_X8Q{YwY5U*5bgj+ofnIjv2679pRq#R=w)-lOve)
IJ*`p1om7{_3no8OXa`Ys(-+C_aUh1eLjJc8dFW^V`n-QJZ>m3osw<U606U>c{iMDWlJpj4Bk$+P^^7*d^27Z2bYwrf1=zzmJeN?
LoDO^%!7Xhd$x?Q?^{MV#d|gHf56g59y2wab*g0*2-`TS4ja~)xLN8H^vKO#F<t0iS0|qacRR4$`8YwI2eP?%J@^lQ2DQI>5PpF5
H&}aFw0Zz5FHQc>yoIgM=Jzq9Y9Y1M_Sa-ndW1=~i8ZW-1@gpaUOmr*+bGi`P}i16-C_<p*!gk7^&2RGJYP8WrqK^g0m|jlF4(F}
)r=z`ru25kDY&WWNnCiPq<%c19Hs069%7irIQ6-AS!_8D4Y7(6i)Atrk#&?4)N}4my?{*HV1tTrZm>x`+LGFlxpUq9#u{#{zSQf6
Q*rXy82BA~P~Q`$z9;B&$X`I!SKk=njDUy4gPbX7dp59#xo2WBI+5^zE+el~>T2Gyvui+`&jT=H&Nr~17AMm6#tUwNjCWhNcLYMM
Pt+gsp)zo!&(awys@>8yZPCVyamrZ?SYc2*p)`j|LWyce(jKC>YVdP*Ll(*%AoAI#rChB_Q~11L@DtdaH&@T+#n)gJ+0^*NDp`5z
L@|euh+eBzJq@8LDo9LfVeN`NjsrniJKU0SC42{U<W~0F33B^09C*3GO3Int6~&ZuHR8q^pIA-4ZtQb?HAU;Y5mwU^Mb8J(LWKm-
?rN4_%=L&1t2$`dG-uGF&8ioCPK0S_myT2n=uPYy%AC#-E-KRCweHg{&lc=8_?KhI{KrE46Lq|6W3D2ZufZzFsnJQ9bJ^^&jx%vf
&5#cD&IrRQ9d*|-L~O&V>HX?x9O=-C&ewroeb-%Wkb3ggWPc9gb6YN(x(`eWFIdx!)w%npV@Us#{W&!{(JKFA?;rZ5V`G^wPKPnz
T8AChdZ#S~ZOx;O&~PaHI^2Q2SI^^7l}xersR_pKnpEvHol`EKS)l4f>BImoDwM7_zn|Z@bZyV*q@Jsd-dmZW0wU!CJzSbPlb(m2
aR(i~Gv{G+{syuUCahv9=rH1bD!a1`<s;#T1GBO177Qm^*?{%deV~q?dMe(4Uts6EpMihh&%mkKiQCOi8j~zo9Y@ZeKT;<MDE8*u
)Ca%x3RTuxYKnHv02^*~AUW{Gm8rL_SRfULRZw7VuxfnzLjv|sV3U$-&uoKtqEnepF6<NE5W|EFlzB1x1a03;um^#{V;JFZG4`;k
nzAHx-Bj07TwDm#&Aht|Z;;!H<GHp_uCrc4)y8~H<@3On8>^~0&l_o%s}@=DTSuXAr-mnOB^Y_uvC~91k10UQ!m?_d<`3o@7}d)-
wvfkAp7@$bXd7G7v74L!XhA?B!lr!L<$1cEu)4j}9qtcvzWM$9#;5y6*oINeZ+x=K(4Bgo=+F*k6s}k)&A4U0Nmj{~-RKDGc60@{
eV(d=R~VfKS<pr$uD03^cS5@jBiCe~sEg`HKBd~0Z}k<n+C^)HiXY2w_ZQXmL``*|KRm+FmKJl0`rIRV>d;ZZ8QwtTE9j3<mljbB
A=?$~K&L2<xD)js7szcG<rS=tuT6XWufQhJ;BzbgtuI!z3%g~d)$upJO`R{|m9$LQ8NDpX9)!UTwb3l9JwY15<tsE3|4<<KrSH~C
8{`J7n$=TV?4=Yuw_u2OUQ_P*?uGVj54!K{{>EoV@pp!->^-O6CwW+PL=rtLPW=;k+=kdU7u-{a78mc7Tw9be95Mt;DPrm?o9!y)
oPPBL?)ItMH}F`^OG7o6?l)ec>s$55(#lYL*C@-W4T#o3AH^TBwtYIC&JSoh%(|!zL-wM{qM>c%bm*k*2H~(i^k99{ey?4-OV|dw
0XrVf$4F<FKXnxUHQ=jQ*uO6pcB+1JYJYMB-2GmgO1>~`L-tYm6QT8KbiO$w>Vd4>U~Ive>fPaS+O|XM`{M#CBBXZo=j6BNo`K&T
ch#os*7)Xr`^IatyKlwa#2;h%4Rl34wLw{FG3gGggz>2JD2gQl1AS%K&LUnrtK*t|pK2gmRR<`BH%D!0)y?6Y_?})vDCPtDE@=Hh
=2`n0yFJTSe_O}u)C|R`8OmTrDP`OaqMh64a;l@a7JG7P>J+QZ@svBHqQIUG_%wuM@d1yN*9ka;6L3t~ej4kd0;s5Ci$3FZPrUvf
YxU%_|AU4}`vh>EocWlG(5zbKJk=*Ud)zVxS+xGc{bLO!qe$sh9oAflh@oI4g}4Ys*=$abHRW6?=?R3ft}h1>geT}v*ku!<M8TgI
UjtSMRBIGf3}6d~iY#@!Vt}rruyY&M>GYBY{xFwTERzyZQqmE_!Dt(rD8CO9(s7b|taI@ft}Xcx0za(?`TOPj{q1hsz)!@t3oL4o
q87Cemt)QAkjtot4=EoZr~@1ne<XDtM+qYFQq+MUO~;~p6sl!7TGZ*oj|=D?;ZofPU^KRt(X{kspN?bqrg<)5VKlp!U_H}x&x(lj
mTah9ic`Cku=#n_GD+_RGVDD7bmDMWu0^k`3g~BuBGEy~Sp;{~Z0dRveV^DPz}w})E9!+q2iUx-l5*XD;?_&j8Vkhhy!aZdBH`I5
g+YMeTcZYF(-TREE<WQJ5>il2Y48+7Ir=({xDpr(<J%Ovtvhx=aoYRR>0S0r3_6c1aj!+g!C&{!uiwv?y^oZ2{@vRRC3Q;C>fXZ=
_fmoX@T~n(s}2<|VwDShI+p&Tjv^*@%v{vO*@nZW(O`Rg!nK2mKxz=ZJ4?3Cb4r|g^6a$YeDa|itG}^&m#!PZ--T)K`eQrwO3|s?
54H2?Y8)#A#l4}6;2UA-06CqZJ)Kx7!cZxg2TU6JgqF3bjY+gQQL6!)Uj5nDqn>96zV`ZY<+}d@Tjwm`9il$myCiL=W+_h1QnYEH
PWdG?TaVIO$Iq&dL277>Lk(JWMr$6T`k+x-X&+S?3QlFZj|-&2ACtDY=MX2S4GqG+PC9chSi=X_`-V&Y?s55!&#4C7sc(vwEC<fG
<vf?R0L)Up;B3(#L)C$zm)z7m7!f6MG-p;VsE2z%Q1_Cd(8^$m_NiPrw8LPOk}Yk1^85NNTxnz9uWxL*Zfw*#eEog+lazP6g$hdF
I(17lQ|AWfMBGD0<rvU{y=o^60+-bt(0Vn)R5!?7Or@l(eaatbw@Zdk`E=p<aXD*eHPvUj+xPS3N&xY{NdQq76$$YNlSG-Bu+C`K
R4|Eo^?3|&%R@AtIm!pxm1)G7UJoYc%5ACnq20k6ltH+B2~V_Y?qPp8r{E{BS9@>wzP-0o_Y@sZ_ds)~0iZE%6ugCM&5o#EaM5+>
{eh0o_yLFo@R*rF>&+eCcjVpN>T!V-CG%=sd}ask!}$mr#10kG`tpJ`-B?||e>$jZimWQV6?|%+;?zC`F`w0fN@qZH##k9AR^4q2
g47;UF`TjYOWFQoU^LFGXyOcT{jh7sHd-wqt0c7EsPist{nQ?=o}1}6>?H4}I#73Bd<|A%PR&ztZw=3D28=;zcQ{&9G=^ZbJUi50
-D|19>g=6~)ug(t?(;c%x91^>Mjd#0wI!Tj^R7H_+K1LM{p~68{#s6~s{J(Ajor1#<o88XPD_2Nws{~uJ389qk>Q5$Nq4AS+|h|)
u#BX$uAGlfEvs;QzNiTojHzYJXYAG$0vlzos?xt<NCW=Zp{AZ|i8tzUCu_#vBx|Z~ifrg%3N8TZsAP9F*2!8`=}j&7hO?M4F#=C;
3_cFB(CM@Q9e0wTOzmjfhy`+wa5zh_>z33`l}Zem&S|>5+QlZ!4fgDWpdU}yGmuuX8tuZrZ$E${pZceC1`p`!lATv*OsE!g78+Jl
8oZ-KXhxg(6Ro$T8PpP}VBw556mL5?fNy@U+^uxusCl2A`Xd!GpFV@VPO#YNOm9QAI;c2xP#L3#u&U~Q!{MurY0OyfSSxxc&r~`$
9!_m#b)I%0LN6xj(RF;t?3;4}bg$8>q2L)RPC*iX%#*ICBB_^x+OOMDs1N3Qk0C>J>Y*}q1|n1q8_n9#J*GrRTOP}Hs^B@64wvz5
H=8iT7po(bTO-1c5w=qnP(AOUHN_9W&g^3l_X3x<pYXaT-eAIg%c&U<LH_+Ik4|k=R5ShP%9GwLI*WsP>bR~>;5dwFe3;(UGD`V1
iP?&G>BH&l5Osi74`Q=dmUS+%{F)lcTtf=gz%{GOf!A?WcRaD~e*624*Tnl)OzsNYZ+FksQpM#R3TJ~h_@h|45*;_CB(Y?>JG6=7
#gKJKB_5?CYZr6Rt~R0?SFg)Vs@V)b8XK=+-CH|q{*{eUcP1a60MEC-U*9Te=eiYkWv0%(NN){Bfl=*MqSiK?I;5nuGCnySIR!IS
WHB_y@E*skA!+A{Pua89dUt0N^*B1ulQni9a-nq8@PzKv`%{V1CF<mm`+mBQAlu(59sj)Jb|JLd@4l^QQF|2?dOrg6;)v>4qmvyA
v1T2^Dho@8B0>LE`wsDw4|jDO%M<Gp)4A!??YU2y25=VrfO6S-;ZUAd`Lv{e-oJ34FV|j=|IJ>HTB<17^1*zJ;n3EOlG$()2ow0T
@?cYAx?v{bBWnK|tXi+6p^8plM$b9|`*DKY=WIu>qutVVx|dg?6MP9iEz|zM>Tay+RgkX3)0FYVCwjkrq|Pd8cKXOhZEKF8od2Xv
Rm7iGbs+_S89ElQ*QG;@gR0)L8tmAN;f>sd_i>@!X1z}dPuHPYNrx-!lgxHT!wK(v^ZSkUz7cjF(M~~q=SS3F#i_x{?C|xubZXx$
27TRU)0vc3c}r{fH4fq=Gz2|}@iPH!?mH!G%-G`gBSI_Q9HW*-PaMy50X{4@L%i;%^GvGq8=Y`?-mo>^TU2jhD>jzB9oX^lt2b}t
A1XtBXn(zxsd{ZK(U=)rM>Jw0tEvhE8`AM*I&1AT5j7FlYnDey*Rfx)+)w3X=lvJh;XD=el(6r-hI*?w^;S^<i;Y9aBoSOp!vO&Q
V9J?cRHMnDs%MEMU=AKeMK$WI22+r|;atTPNR6sGXXJa(epV{KKwC_{N!~m6tcEHowtkcmdNCt1rrPF3MvbIJ#*vn92SL(~rp_hI
MhvnUbSomxPP4^8K8Lo%opb@MQ>W2uXtk)Wa~ELdx2FhKI`xGWzj@uT65KnD`CU6Sr@ks`<NLrdgdXspunDH!^v7~L(UiDYT#rio
b^BmhWR*pk*L?<G(I>_HH`|M~>@iLn?hA)zpR2F>>i?(g%(5HFl_a_se&+|~VJ&&y2Li+Xm(X?*5fn8stGmxjN>o;r2}HP?1MX%Y
o$43t$c^x&ppoB#B?Fdy{OQYVGsNTQs-{d_t{$o}8jZ&^o@t|CC7(i5Zftpavwbg<>RQz`n@1<|Kd%lUk#xC!ZKcN?w_(|}dE@oN
3oBwF=Noa~QT<Er(b4#U4$>oKL@Aw?Ss$uZNp&1b58idu@|KEK=jLL7Q=gqSc0(AzC;TMyq?&!4Xe*S1R*m?9I+sr)=;!+{uoG(W
3>lj9i{HVL@DNs6G{uRy1#(8NLoCm=5ETlrW3;v%7WRW(`!s22!%nva@ft_t@mykotoya(8_w5f&bpt_S`KNMFSl<`Ymrnz0Q0dT
pBXb^)2(AQADP@{5XeSz#DXZF$VO~R#|Kx$T*A*~RTnH<4|}3LJz`Ug=?nzBdDgy6TEuX@fByORe4&fufBTB|`to<Y<T`X!dO&8N
PUcHR-CWZ`o5Y+OeOoG257pJh^_d0IA5%}>U<_P@!-`yN;tbBcfmH#QKTjxMdpUmqoc+$s@%-XfwDdbWq*XYIRRSKEq$&O`bNIzr
?-1bToL@|i9Lj3i(-G0Uy=#=tl`6!M&b@&1IIkJ!r*s)=VT<{Cc7MKq{`vR%X7`ru7J+x+7flt1rivbN{D-_*i|YSiaeYanA1;~N
rj~Wmic^l^N5T-JC2`Z`kUuZmA9aIdtEzx>^$8YD5tghf8GHAFwcc36^>#fClp?KW<t=Jb9P%oM9{e_{6@NW2f{fapDv#Gu59Z_>
)s=n&lSQAE4OdU@(65wLaH&dP`{0uaYA725{r1Aaea?%FUohAEFR)QGPFL%{f5$KRARYQDPO+ADX=ENE?eh++?l!X6Pp2uh7up8e
Qsxs?<X5v?n<z?i9lyyiAi<R_2fr8C6h58Bl^?<GtFm%^@jF-&8wx8^d>pkDX4{sdX=Evy4l|2(wV^pS>md`5=*nvf!3p2arMgyO
I*yZ|0g{Ic`@(Bx$^0<Ud;Q>g`Fnr+--dcoS8=GTI6qnt9E(RW<Bv;^-YUm(3E3hWX|#{pDq6Tul|UHSQw$NMv#Ycn8vx3KrQmWG
LClaTzsFa*nO^{J529$^dk{I4RUFDHxC5A>YC}PxbLOTfmGW+L3XvWy6WYWAmEO*7XP7G18X8vU>-uwrw?&{{L%j0WdC7hr<v$g7
eg=GcAMbIdw+|b+t#0!J<F$;3#WY&QvVue}aX4o4Tv4#~+8JWGUIeHcNHMbb%*DB3@;Cv9xR2p*SgJRmADm==LA<X|eg4PwDJm-t
l@-`b&_=LT8$$&tS~l6z2M2H9n2>}b@}|X&MpfD(v9vYEF;)EUOFbs9HsX{o2K+L>TQK3W_ak=$wokyE$6ar!{=S+<-Zq#ayW)^t
f!!*xDJo-HIBPz{EtobAT{%qL2C?NmL!`|c64SI?YEN+qoBG%-4H?57UR9nxfpE<p>T6%X^@C5?mGI~l$-$go{07*gx#H1WDfLKP
D>W^y5oqn|hLE7m!ma>k#Vm1q?{hdhd}}?FagMqeX&-45_{>-$uLUcmbh*MQ!eCKl9o}T#f5PjYc<p^UfZP#Hzx>KRyn}9mj%4(}
27?`4dyYiY*@<RK5#pZ73n9mdxU0F029G{Wq~>bGDQfKGC&-%zseZkK-4BBS?*7Rq@Xvv7_kQ5pqrier@}npkTX16OqbNL=%451z
O7DJk1-*tGvlhZ5tAaCqa#T*CPc8r+C(;D8La*w_V$*{8+JE>9;9c-<#lg3L{bM`IJwj|ar<XoO7f=~Qa|g+Ax5gaw2ykfMeMgl^
(Pe}laGNbjyeXS~ge9P1FR?z7YZq)u<B)d$CeD05f5PjZc+sf1-rC{?TM6C1-Pi%>fk78BWQC7?!t5Ig-6FpozwD_0rfo*tOy!Z%
v?x9ED~AXl=4LaZ?)|tRLyd}0;fd{A2m2G^C-D9fz1fNe_8sB~Vx}5W#!^(lLgc)4E+JtO(T0`-l5MWz)M<Uz%C_0KqEbe&;?#cG
v1t)V*$2vg7k}rxkU&y!L&i|iea0J}c->XUa&`#a*or6bJh!&Nmq(>#P$OvrxbDP)D+>MkQn*W=1+VwrN79ej!^|mFz36jjB2uSO
*W-kIZtR$^vx%)G9oaqlc!J7%{{*;Su9BK>ZMxqg>?Qr(6yrPO8RVGV9kn5)Y7P@fccWs&6to>YWA-6<GxZ6mkRB=rN^YFdS=Fj_
w0fLJ0U(Akm4w37h2!fsxtBeD#vcC!tZM>2t@Z6QSwOsdUWW5&dK|(c{5cfujj8CCk2VJpE<`<#8I$7Ldrsnb6BWaAH0^OAWha+y
Y_)-;(~|&=#1c=t^;f*<iPzpgLB^I_co*KAA$sO3klB8CMG|{tbX#IW2)3eCc%<R%Qe44o?oeskqKfa`3of>`a00HF%bl4W$a}Gw
b9jZGza6~Xo8rcvPESmfL*JTXdc;={S$Vk8=vAnCz6v5!qjB*Xoap?(``uW&6j4A?Xm<ju&?oNQ#kH$8{BGF+C`b7EvtEE`7*7Zi
M_gUfANLt=e&Xc-=z7bQghK)HobT3}2~)_;1F<P=1%+5!wuPl#Y*Cg5q!H`z+7em@@jv}!wnJgYArWT_s#Lq98OW@v_;<BW=oQll
?&YgW@q7DRPv%w0GQ(P)Z+S+Jwv3B;7rK#gVc_v0w&X>kX2(oHNsyw-PI{+S)iytdevL!F%Ti&hPr!Ar%0O_a(XlpoT#zZbs`Js_
KsfReCoY~|uxDDow)0hVak*99{g!pl0fToBCz386NtcBbc5+GNNfCoV9E_ua9#cJjG(fN5_6ew1Vmut&$cm3(LMEoQeX2HOvJS@B
<_Y8%wp~Aif4WAS_alIwrU1&NM^v&gZDv)9-Khe>UUeK1(Qd0u>AdpMfo5c|dJ<JapwHm5TcQzp8=Ra-iFj2X`g1jD*nb(s{~a(=
5~quCdIy*^iI@w*K1wfx0ue>q$+>LF!ik3H(hgvVH3q*F_-J9ZgM-k}DoS$Os{x>!_TgjTJ^+i_aCc(Sc)4@UiPxDYUVlBsj!tOK
_Vp{jy+83hOo;YB$bU-_IfN-b$`E_f&dz-vsUF(Is>T|@Q3cp>s3t(CChmh8#KY{lvC~<eS8M`rAj<IZWmqQO@4rIF?HC~!q*ZKq
i<jiM6<w0DqP8XmwaaEPr%EZiW?4Y2-T0}1?J&ccHmX!Wtt0M}k-XbWPn<i3>_*lbFFH%^b@KLSz@q2u4SRm^J797nx-KQ4`c@KW
xFOe-$u3<LVj^?vcL*+<<|+ab-Ez>RpwU7*$ojo)9s<z)_?7$c&e<OvL#`iOFMscE|C3{gN7RKgfQJ^XDuGPyOG=`*(lZf<IIoy?
rgA~vZlQlUL=5TvGXdnB0Ux{ksyh=}CUIT30sRs$z9YUG$?f}2I?q9tN75yDL}VIDw-hQ9B~T}Z(P;CE*t+4#-EoKXst2_#yuyi7
JRhda-HWu5*8O^)mAif6nqE5JUA%vAz5Kmi1LqzgoAZm`0h0*Pb5X%%l`XJQMDuF}kvXxrq^Rbq@rXGn`YdgL+#2G^E75@z>N;$%
dyZoRrH$P<YuyK61)%zE6MqAo89X^JeEd7Wq(8J=npHp!ruD<`K-H2nBc;YUfe2nWhV?bOBlKaZ$d%DWC-gVGXtGHs;BD<?>1Mss
pL<c6NEtuv>%9C1?4N+0f4+52W-Di=`gXC&e`vapOfY<`MZwl273a8tEF2c>z%Okb%P4rH5tqs`u{zP2ELu30XkeI+3v=K#Ai?+r
dvROu`(k+R`uSDFxZQ+%zh&)K(vI)lPCOznhypxDaeC?)`%~Cc*@By+L9tIos<JgY4ra`zI9$;lNL#vUDrPJ35F{TL=Dkt4FTR0r
c0;qDQ{fh#%YJQ_s}Rt);ksC+lV)EUZ`;s!^%q(%_;x;$m|Pi!8)CFtra03KTI_UK6f>%5hmv7Gdfv|NRlDP$s0>tu(VY)vME~D%
v~KJT1m&?;pR(r<K4Fiym4SPIJ?K$<q2o~dM8z!g<Jz=c0s072$;2Gm>9oo?J$~8~6{{ySAF`@2x=tDoCkL623+UeCd-C7{@=Sp-
m5+n!8*q98R-n4y(#P^2hRr<^Fvv1Il*FrwMb*5AUn;^CCmL-#7&Bygykgy!hHKc>dQ%1sm`!r}aAdz58^KI>E<E+RVs+b5*1gXD
`1=Q+uqP%r$%_8`;&;GgMdV+^fy@{*mW-xQ*X>YEJMz9Ja#sJzmQ|a3eFkZA!Hn#PJ`qb<P{JNK-#}Sxx&-qF;80=yDr0Ed$e-}$
C*F9Sr|K=Y#le}CFK=TZ`4JTuedyT!2{bmtTu%7TQEz0~4_wrh!;340DN|Kmd1adp#S}lX%5@StkU0zHs`+Lhc`Lv=^R*Yr<<Hpl
t;=_--MavY6pTj-rlAW?qkfF^7WkkKp3WVGJQs>md1<JpGGx=8%N^%Q0bL?Y{RnQaH9+@TyKq$^?)z=0ufHMo`xrHzU;K`k{D>k<
G-b6t|L*lcii#>=`!-_IrfqKIdZ^Iy3WDV*OtwYpTeJun{)uHgE~J@PAFs2=7sLup3};-|aW~-d1RSo$9;T{kqeAmEy(Op|7<rUo
YM`+IIqR5*bLp7wa47#CqWaM`blS1y(>6BR8&Lr-ww9GD#jE=^uGyH0d)WS(Cy<}-majvcCwPh$e?N=wHZ<}uI2Sxp=VE0or+O-6
{5lk24>-v3c(5_*(VSI^k0Eq4{+wW`c0si=Veot+-TNb%>nz5dGDnGaVe9iZy!DCKUd>gEI+b|OJiZGf4A6PRVvd3UbMtz%FkSS@
AaRDn(9@OXpcx&LiLh2LnAVG*h-wY4>#9lZ+$dO8@S4s2$nC-lzksjgx_-ufoqTNLhqp%{$i$$o|2S53^T^8~)5Q#Ha78TJ80GAQ
^+b<H9|<q&7)(^eE9mmJz77>s+f#D`g{s=E+rK-}UV5nb_l5f);R5W<6R^LMyeGhHVdl*L-eD&}q8ihzbEX}p(_^PU^|)bNZ}9cq
jk^%Mq)k1wz6@R+qib=w3>81=>v3U*2H6^}o$a?PZF=od^7jv3u``R#eduX9@pgBR6}Mo_Y(Zs9S2dU{?c5cSZcqJ^xjstquu3-=
7B^fjX&grK)(y0T#<@Fc*c;oKw9ld)m*C3Ecu}eLSH&1!;JUkMluu-z1@caG>GpqmSAiiN<Naw&JF&XdE^cKEuarWc^gIN!h>WbD
G_KlE33Np(zS_ef*y4P}s&?a?47`b5?W{`A8#f!SehwgR_xoJ9dD#=NXLHKi=s`O4dzgN!UKLD#RXVQWXID1$s&SRuRTUzaw|rSE
dxhvWz1EK2pVE41amPDaz@Q$^n{qDWM<HHlhPI!<x*M$BPb_b2z2LJM?A?Qicnm{G54L~^-<q4hh231IFx_whQb_ilQ+F{kRS9z-
lfKqaeZ!%d(&<@(0hcP5iQaPIK(N51&o?n{x4S-JyHg{0d-1(31L&Oeh{q&%C|{^1N6rzUor4qHu1BuaHW<KT@Pn)7ptPM6M;~j^
TM;W`hL00u++gEQ#245-?UuP0^`Ei&8*422dc($TV;1zkw@XYWL_B6HWi0&%QqN{Bj;Z_1<Q8S_w1#S~*ta3DRo)W|IrI-Gino0w
Q`?RgNDu9u!RX+HgM*LP+5d9A{{maz;FYm2oZgvcc*Gn$nlZ*PV5Ml0Moq!1EK&J16{kf(N3dQ$JN<uEztotyuVoTMJ2}p@pN0)`
XA(t}ebeQBFsSk2C$tgP9GNG2OP>*q@rcH_+BqHXqBcVx_U^XCX0Jx51(vf%S42=sQAw_qrQKuT1=VMXW)FUBl#mQPy5{_d_qCip
oj=UyRXk8%u!b9JDcAP_X0+vG)7vE`_k}Ha?RqaZ(i;||>c3`I3Y}J66)o$StuDl-R!U(R^j5Sn-D=$I54WfC0BiSts43q#kVuQ>
>wXBYr~^Y1w6T@*i{HVL?9hzK=v~v4r01-Y7uNKOb0YepNcxH6HlHaEB^0seTsQ$K3VtdI%M9&tg5*e7D_XAHan3vLK?xqsvv|F+
#v3c7>3kz_O@W<ldcQBocxcANDBNPlxng67%C1tzu~ywiv~JbP1x#abeqnpH5{io)>W<>qp3(#@m!8%;vkATXVW#wo#_<(*#0%&)
1bVy1<T*rRw1p2OYg<MWdT|3+FiuhCsAl;VvF9s2I~#jX-N(!k^iV{K9E9$wRVcY#X4E2`pw6qe5I>hC?oYb@{CmFaT+Ech`=pF$
j7Ky^`M@2vhjI+D6_weC4~h_CK}{K2+g0gL=<=#fU@#!vr~W1#tra^@umVX<!nE(1=kh5gj`msMV-M~HYre6T`!A>6DQN%UB)RS0
{1%LfW0o2s$t?LfP;N5{5qj<rz@xXV&_YhDNA_LOE-H4=Y~!@tyZ2{<O}xfj?Gtq7;`h@z<Hq-aI-hA`YgD|=7mT=bA@-n~T>oJv
;SCmS5FZ4OtWt$Ftn{Kt>JDkxL*PAf>7g~$jf>ll93bJBDmX%VS>a5VrO`8YPIBB>%Z-(0vhxk?r`uul?GlsawqlGTl!&A@WD;ep
J-8<3g-)gR!YDJka70c`6)?il7g8*pV*!IYncq=OXyXnP<=(`*IX8RrbrY9Y*bEoM`%vy3k)U;i?Eg?%uY%2UC*nr%Xq=&IBf2{j
ewVVyP`Ri0rb4>rtn%%^^v8&0@X>4{0m!mnlg&@CoQQms*FRxZiO5Y)J-_%JD>)8%7&_}VVOXMOHjSp>+Zz^YSW>uB7G4BgAcrHP
1gP>)`$)gwO!SkUSdoRYgytHaSjA!L*S-67Vb3<I@Q*es=&MH%2G5CrbGMQ(CatOr`o6~Orm7}F!8$9174B7s3f@U`>&(MU+wlH<
Tp)=KoN}EHT75C)i`=Gt0$Xpe&fR}Kn%zu5SHauOOO}gU8BJ9iH^6#qM08?{R<+n@B^FvY5{*19tr=);)?>H@SE5f1e=hCi#|3x8
cK(W9yY2al`}g_&3v4tCsWi;>#qVHAZb-reoKuF1)gy`yhcZOoVQ5pE_6RlUqi4ER5l%&D(`OOpai~PjDxgDjyV3w8!Au0lgeO>~
5Ro2l=w-Ob@rm_p8QtF*f4^h5QahSb?-!Xgha$`@1M>?*N47_}c&bS1lN>S-3`d1`g~J4bs_MSRIbtaYgy<7EFCf6X7dfC?dI72E
LDtXB<?d`A{eaH5r+h+qFQ4F1h4HAu)XX&6v9?Q185pF9^%O0sh+#}4PtM^~YE;F9DWa)bI;sW{SC6Kjw+>;ONTP6K@^dYJaBKV-
@oBTZgYdhf37Qi;(l8_9t|Q_yOD~!3L@jOYWoBEPKUA+78el~&I!?+dGdrxMS7LA}&V8&Rq)dWZ!tMoVm&^<=;_Bw?c>(`{*FNz&
WAC@ZNrLJ>uBXt4@#w?Y7F$=YP-Url9<R9MMSnzt;t>qqC8nl2ltFqCF)D0a%)%p8^EwL;AVY#M(Xb!TKf9DXL4U&jUyVvU8ZjP?
m}nP{A00Y0l=Wy~9U@YAc&Z|qjhdNBQH46x6P0a_L-c5L!=ddNGX#`0jf!Rb0KA<XzaCF~2fPmn|K;K6k%u9jKClr*bNMjhIBu-$
%)$6@U<P_d1>UJFqRJu}ENBxlB`fOTY;)LoCK7;>^ytJmqwj8UEj!l2nDcWpUwHi!uQl%eC*u9^^10MoF6Q02GIB8<xtQTrPRsA?
R#b6eJ?Fc4r$V0?5NBM`Ysb)3YV=JQs;3lH4yG99mTCe$3#?yuOJJQq=!&l8b7!$Tdof>r4Mn@HZ?n7n--T-wV{kfoOyxbC9q<Fs
F$g2Ga|8VW%#E672p%z^LputEWED#;cr=rp_Wmya0m?p6ook-!iUL2^zge3$KA*`8Z+PMj_laC!*#Cc9$m0F|1Nt#&Y(1O^r~)vm
8hXUED~_&>+dNioh530UH)BOQknrkWVTRd$Med_b)!Liu1DR(shIE~v?B3DL++byb`y>3FiO61clnq-Y<a&#Ujp0#wOZd5Ar?hzZ
k-aK>{3*RSa#DUTCIV2Um5MGS_Nj+7gLL7$;1q<)A#RNp%eF`d@owJWEZ5yQp2u+|a_W4Yci9W)RaNnAN%vdjwq?(67o9YTq6~g3
qjfQ)5cg5@L|%%jOV6uCFj&?0;Z)e_({D@ZTB&?E(HGln^7|SB$onzP{{HmSmQ`R9EP0H{E(&EYm{+x;Z-Wc>TYgWLCimWP)uSup
(UsA^SEUM~v4AuM|B5tSREF$!C>1)ZfRdG^6bw1%UrLU>A=FuLtb1IL_o|n8(dymU7`**<c=Yk}zxTJ>PzZ`r-xagmANZ{;qiR68
LmOL3Cy%ZoDr$qrRmApGZHcea<T3Sk=recXDH#XOrBsiG_TvQVb})G!#q4%Q1go_RDoU$&Y|r<PZ@lh~lI4=HC?4IDchJd~sLHt9
%YopO56b3?L&jtK#CoxmY!BrcK_0#1XCR`T`dqAO<>sf>GY%qg_=lUHeOdvK7pkpVOuvwS{!Z7=|6bp^dj~NjfQkiw<!w(o0y8Ka
JlY7{^b8upVl+-cMLYygEYa(^R;<3)BXZwuQH`&ngi8@#BrMc<-k_kHN=cJ!x~hcTC+Jmde7-?(XQSW?c33P-kRkQAr{pvQcm!t1
=-S-=SYrJOFiG`5ozdITl~Y7Xm}zR%2PW=;-ZU7oR{72l>ee9MK%v~wnsX!UZaYUR`9cJpxnKU?e~+$z&Zuj83z#g4tjt<gp(Cwr
r?}#_Ul`_4&~?a?*UY8%(AT1ZHdhQTr$W4_uGr&jyGBSvLtevq4eZWtJ7rJ5Ta5Kv+}94~{_&01<>x=K&+ZuYdVeE9_oqizW~y#!
nRQ`MLC+jK)(gML<)Vv90dgG6@5`S$i|y6t=~T}jLp9FsKS^QtFk0N3UZB&u{<&es{c-j)c6)cC*MD@PBPQb!lPPPCiN9AvAjY($
x<%B<JNVzCdwvS}D4a`sWgVN9oG@GqzI&T@nUG*Iyrvw}3t*e-=SGO104Hkm(^>Xik&cKA@>dUKLjAW#JS;v!`cKDrG=tc)6A#2k
np1_Nn*+C;gS*)lwd7jlID+5FQ9$?UXrkxw1#nT7P%0ubH-ozIx);3peyfB#H@@8)<VF-_8k#&7qs7V$+`!yGxkQm#u{t`J-S){{
t81YTwC-@BQ7-i}DN62hJX(`B@_IHHyR%^sF@bM;!+nN+nUbA);O{abVlo)VKadtW%u@C!@FQ1yrb)lf8B!2t29zBV;4NUmVE3eC
=hhV=mt!9^0Tc$Mymlq?6L5U#{_^e@z*pC6{72U-Ix@)8Jc>X3v{meg**v#O;<}jozrL_oQvs8^qDweRKbk-E;h|-Tv4^U(^Kt^9
q?NoU-)_JuoLPl^|7n5!ed$UE>E7giH$>#CS^n)xqa=f>-($s9IkOuHzkpd4bt8lQj2>ie0X<Tvoe=G2TP!#3KGDbQrr*u-8!*MX
9{k<D=zp-KdIEd`-``NhB$}z-&QZ|y<hPWJ7`{sN7*T^y+*>Lur|1M;Y-kGsP$5|A1k@vzD4|3B7fYRaW^Yh(7Lw7Hx!|A<ux};}
S8(3FV0AavuuEXSc`9yCNU7F$wHG|cBPla5>QK3RSft<-BAg0D?6BSPGmD9)GP?7PncAQqF-AtKkD_@qsu~^_S|XjIN_H0xJ<Rp9
hU@wM3v6u-rfe8p*<bt)mK2DR%v6FS<+a0>xKwEql$*kV0z%te@ru>ra|4yCu1ISUiO6&wXKmqgLj<?G9#pM7L4C1*-z?}G*#Bn#
?rC%KD9Lb^pWRYKu2e3;^&?jmhk64QxH2(z-cmv(bVY~*BU)>1pC0F-&4>i@eC$s1Av}go-vIOZ@WcP{*PnmSm%OE&b2z{F9V`hC
0U51i&BORE?$%w>=do0IpnI~??Ba#T!SJB=bL~oph44FDSH{^k2s_~ck_sgk<IEGRaeJTuZ|L)+|Hc|_tSGshZ)|CcOun{nmzb=F
l1yyf%~@kWP`{(F&h(e6Y}(PP$TV@7X?0Zr4u=!w#u}ZWWhx794hP!3d9_u{jpOTK-u;6Y+;q(mAQ;gPZ`YVihmuTRoWqGA^uwdE
??f_DQ^>y38jN0(s`)ur%Hqn<Wo#Hnv6ZwQ&p1pTrq|kd=l@@5^PcG4hhp#YGCDH&SUo(>Zp9p!^)mF2O_GXG+ZwWIxw&ciZIURr
-ce~7Mwx*q;c7ca)i+9lZ?Q3j%Qg1Lt^xlvmHm6ZWTY0)S;u!f0Ua66dmi;TxU!~8XheO`sI}@*6OmtC(ZI}jpk!f=c~m`^-b`Wy
o;enaq7&`zdD1I=W)~c;s!aX5v|quZg9XWZD~RRMk@4urm}Czgp@4oun7xXfH)INZ6RAP+y&}S(!Zk1LhG53FE*%PWO^@XX)|Ifq
279HieK}nB!SWUix)R7`C46JmKXAPf_rtcOS>A15T5K>3e^5lHpt>`T!ogavb)3eK)X+=2b>O)sHf$J3QY@)$icuU|Zerl$Lc2Fa
48h;1GuKP6ei!HaFR;^TkF;mM(%U5_t!*6{MWex}Im+iM+O)8TC@|fWZtxgxjgHEs@tj#dRaw%w-=267$K5Tk9kzK*F`p4?H!|0l
J}a~MKl%Fe@AVBUyL;;1UR|Oi!x`X1+=@OB1oK2<5>qjmhtI0Y6SWXAZ&rcX?eT4{C9qUyMyUsbPub%HxsUj<rcO_=#RvDfbp8$&
ZGwFT^j4$*4H<OrAIHc?I5==y!L76`1U;)RwX=o6@@R7_pb6q^snc*BG7`9+gPC=L&CEPwom1_ZWy^~xt1J5NTsb&jKfS=ZYf~3A
7dgkG&+J|M2ud=H5I#coQ=h!jYmRgmI)wtO>Id~$^jCv|RZNHYdDEv6lIqk^aobaN!&K;T!G)b+fE+Iz9F+Sn)xQ5zUSaPpw7YHj
?HZHUP>~T)XNpy{ymY5fR_vDLQ8bQ8u~k%XjxqI?CsruIMUI^58E2xj?RpuIWxt+hSg&jRd@Vnrb$~=V%DqQRUaMyXhvG4V&sxZ~
oRXJVc&nApU!$6i>p*<S`mlz!A~TE%ccurN{@#i9Jhnnp>RiID=KQG>BVF&GfBrpR@;TyQ{xKAaWDJ5o4^@|nyS~+KkLHwN#TJ>v
RsQHl@{CR`+T$Fv{rUhh8$tzsi?c99@Hj#4<3atJzCOW5rkp=@YJCHn;+~PR=NG?$4amhXp2R$ch`7G&75zSjSy7b`hvBZI=<&;$
){9}3pi}4!X%tm)+!3}lHs2M<ohWK>R{+?0O^yNT=tA}OPQms5>4nyZ=im3aUY)b={44`vG2CW6RNDye(G@|DKtEPrZP<gJhXcj5
R8(hbwe{aWL}twnbwztYg*CFxj|=dA+TyboGW&5e_UoRo<`eX-+f?s1)cOvv1F&O4in+OVl%y($aYXE*SBxTxqsQU!Su+>{&ZY$(
;y$jMZuW#Ab{3BdC`=NYhHEW9kZPT)eTKCguzdm!<$fpa3u42RS9}NE1Dzp2FZMW7!?1U8MsK=a4!n69qvA_@*iZC^43h-PCZsTh
k5rKdJfWv_ZjzjXyMb^A@6)#`*?xwOdS1OO4BoGGcx+Yehf;z_%`u_BZRly!13A5)sy31yNJi@DOzz@E);2n8JGWH{HI~{=W?8qS
w_YpGoEwNcC%W9%SbSv|dl$>@o^y8Z=bQslF<f*##$qn9<Yq?a7R*<zv`P&z2k*l;aDZdUF&UyJqOHWLjG9K(n?J|rC@}*92gW6T
1NxY3h|GC~_zAFo0^Wv_=Ud`m5aZ1M-eFIVZS?a<&K1{(!rU}dwTDx!Nt6%|wm915d=%U1Jxm9qyQ=F%qEj!1-La=KHs<_iA8M6!
1A%PX@|77|{~0?jPVR2He;Yb7fT`&MM`&V@+@Xq6geqc@DCHa1?v5QS`mTJV2e*jaS5%x83!72c+ft?*=vI?(*<FB<Aou89B#fQI
O*3!2;fdGXze%`;8|be~=^gX}^uk?P;ntwk#z48?F3b&hx&r<S%j<~?+)0h0zoCzVf!v{>gX=|T^Kn9^HO?8I?F)4M_4Ku5vf(rK
a0=9KA)$9wQ$QgGXVphiSgvB}h%&o6IxSmi>BC=#DU<4t5lQ796MSj8w4u+#WUM^7XLXMgD9O;#<8y_Em$}eF!SD>z;r{sz*qd^{
b(#+;(!Xt~42Z=9#9~a1Mo;28N?X?1L-bN0<I?)&5tj|(aU~&^f#+R}+SVDTAF;vc>mIY*nD@qx#ni9ZKb^z+^FH_md_1>Dbm{!!
cf=&ctr1hu{}&@pLtJuqFswtHIgB+#Hw{Ka3N4H@`rMo7o9_d|xF`y`!nr*n$}Wt+6#GQXiBPUzdH#363C_IbBH#4|2b5s~$}mA7
{MdTf+=w1npXhU+&geHeazsN7U7;}c*q=AX_P(+oV)|L-_2UGp71C=l>3XpCBx`u>q09FVu9v^p>(#$g-}mnX^kC47c<h-9#~F~#
cCfM;LaI7NPh(JlSGa3ZLEX9A8<<g5m8Z({aDR>&PoR5+x9ji)<l7O8{RQ#Wk7nQZqXmQ+0(vlt4dV1w*{>e8uT?U#V_BcJ@`!5I
q`Zw4?V(Drw}d0I0=6DWEaSG+(}@(s=m>?6CEjY}MO4N-58iIP`HA-w-`Q{Nxomp3-)3=yVZs)MK`qUNBOhXPS?p#g17_E1GAjEk
?e|Dos)p!YJ2)l<68(ZpRh46=;Bg`5`D30S-Z;Lkb+~`>3H#M3es*`gef~&==)u%Ax;CRh6sUFO4dLY=wmB73o*HB~QIX&iDiC$*
-GDV6E-&YHW`=<9jG>*m0qu6Q{B3jm02pScq`ANN9Wbd7K^SfkP-%{wv^G?c+l+gF->x3DJrAqDhhBn`ya>NS%h43FRRApXA|EGE
IGnRSxNC_E`J}v#8TtDM*UR7g+dZSP$Fbk#ZUkWhf-qw-Lr}0RaEQvH*c#2DY$BG%#3aKGS(MM2<tiGT3C%juYtCVJy|RJg1Bp_3
cml5Wbyoil7~cS2v-<h{tbRZc1~HLG<u=TvRYaMCHb+U*3@o#{&!N|aTYMQoFhwnvX>Hbakn>ay#<RO+TUqTb5li`4VcIaU70NV^
-#g;MTc3Ej*uUQLp<W(J?=Hsz$}nLo!)TGkDsZHuv4S>=(dkGtN!&jj*{tf&Dd{GQsXE2sz?6WJNh@=myP07VUR8*@8wkPkMFQjw
9rZKzdYyWvf1G*-lwktOFe*buDElEsU{)STi54{SMCq2#b3&1Ei0G=XU`i^k>DQrgq@kGmxPV4pi*@H7ppinG8IM5EQTme{)%(Xc
URR#~gg<2l5L|r6lNbsJTO;OJiCen5%@dUCw9Q2}wSfc8*vKBiLDCkH@>*}Awf-4q++$5A^dj=XYgJBsLRXajZ1;5i;1xUHq85az
NqQ$66cC092*Zrl9X-Dx*MaV_N<oK$ViKRA149oRGBM<p*hG?W)ow!>x{5e&v$+j)?`s%d{aEYdWBz*n`5kcnXe58To5_Qy!MHvd
JM?Xa!mLr;f?G9snlBv6bacGCAm*uGNe|yKaX`tf=Rv@GoIp7Ob<W;d&DrM+5{^LE4AKW)`^0+{ky}$L|A#rGK+io9^|4~03wTDi
a+sl=kDtTpO^JKhRu0Qt^U=`H=&B7GhHIF<&ZYeMxDb;ExeTfw$hn#Lw$%1BbbE_{hxa1j0Wp~1_N+Ufd2HfrqCvfJC>{>2<1B3=
wC)F{vRc(<X)hmTi_aqNdi1bm(Ey6%zH`3B^s?01#?MX8KLO4#jZ??%T^d9ICZGVb;u;Km_J-j}oogX|JC*i^VF*Iyi$#eE8!A<Z
+w^IvbO}?dzfI>i(6skPv=<Gfe?c2Gnr|!Y?w7yU>nQ?``*V5=m^6q2j2TK0UJt(_9-5ol+-@mE^x?Rs($X!C>zF>9X%?-w>W{e+
s_!G7r3pZZbfVSQi3@;5{$u=F2Yv^fN;xOS_ZPndCJmzdqUR_oB@lo|!drC4v?bqT&m|pe%;ZPRy^gvkWb|u@YTy$+mK|FcZ3Bg9
sQz*vD_qkafB$@h^aEhD%1<%scPq>>JiX5ktzyR+mD#z>G%LrmT1S=73c_>NRoqxA^y|vS>oHr3#*WI?1l6+VLzn%|C9c?dE#$th
t~q|K{jRH4cb#f%;VazYV>rL~9Wcoc*%xKERD4^98|Z#d$LFu)yvWR$HXWsO>w3}yNXI^v)xzZ0YD>GYnGrzCe%&(|Cy-x`^uHta
wCbVc?ceq61;k$Pnt1rWdWS#Sa5&Q|zrcRNThM;U+_Y-Liu7CbFu21*`Y**eOlWS4Q9Hy`c9@{%`dDJ?efUZ~e^_D+dm`SB@0@!A
S}y^u7cTttf2$r2G2Wa<44%PNMo{Xqigk*<3x$j3yE4g~<EScVkzaSa8DIltPtZbl?TN6P^7XEMLj+*%J$(K6s;>3zeeZ_cRl0Zc
TjV4^q+aG~qtgvLBB!)fbsqflFx%`EZ>OO*JqpN6G_k23v}5HoLqNu69}IvPD(9ISzHxlp9QFRmC+rcu;QwvWU~k@TXObRTFQev!
U6a<**`v-FN=uzVK+b3t9bla)`EoS+;Hp-;*yge1JC3zm$~Mxy*4km_22{nMV);rwzXQH*QrtgoQV@8d{&_5#R5EQ&;>Uf3=*50i
2r6_e(Mvsj_VD8vPPItZXE3{Q`bU&amN;qKIRu~^uy;B9w#32xf_P8V{d0aXpzy-k$OGQC6lQ~)T2Lf)^kgAsv2_IcakPq9&8m!G
Pi!W`7M@lh_qO;GvEQO7G>hNVa(4-sZ4UtxefBzCc=HqQb!Nx$)=iv6Q8*hYCcXDb-TkCk3_s?;(oLb3E~g{=L;TKrjB2@-h!(xu
nd49$9;zPGX!Q|bO=FRjI=P0xBR%27JIxd2wxzA#h;#n@TQI1-PZiVo#qWU0gh;;3l6yC1k4{CFo^HMoQ4F56Cy$JrrSFsbpo(*f
5-76N+T70V@t6&CuX@Tin-gFKbyL4>>~DZmG3R9Y{^D1_h`rGC_sGF6hPt%2R375T3qi<Cbz*xLYnp;6a-FtIcu?|dO4M09W<<00
`M!Xby~4#_R}gNS5}}!`3d!FxiXV8(6R$V!ek+{Xrs=)f+&0bQM(-gkq8pqEnB%Z?$7yrGh{DoyDdrK4(xn)tYQlCHI*+opxyns<
paQd@XZkGkTHWS#friPPFqo_{ZOZR&eCJR9Uf=B~8MX!HJ&^gX4<?}f63~9J^y2CB?oLEhVI*g9pBYtG+s=ut)3Z6^(T-5eVj5k=
IFY@%w(=>axZ!fMgO_!>VT%PArAPhS=!mq}+x)qS(#CrI8p6(6*YJ-kEHq%~w0RuOG}oCW?R`{7PcoLv12Z!YbUArcLA59MX_a8~
!TTu=I`muEebRp#Z*%e$H(?5YzMFUKlbMb01NM{N<$usSG+?+weN4P(E9NeZwkJHxx<c5&hDdAAx6(4@u?tk0xUCy&=*roxt6JCz
5tJLP%ccB=w*G`RZx!-g#J+t5Nrs5OgzCo@%}{U)V-nYf!n7;XN9Ag6B)o%}6gP`orH7dm<zi>b-_%V;g>s+a;t72(AzkIKLT%~C
rQJ=4$gaF4qKLnQE&ifp#*ydZJS+7hpmeOAP(qKQ(b~|Q2Q21rhp|f(d20QIe74@xc|<OdeuItHoEyP^HDkQCufP8Md%pZPGsZy4
#(n5RF(EDI2Ogo+tg7qmQuPrqOA`N>h}inYMFdp!IK1n66Csc!O0`eN0ZD`i$?xEHf@M_g>o)iTHsKF=PCLJ&7;tm?#2(8TqwUwU
R5bB5v?p>Hi}U@`LT;)66_~0!FpE?aQ{|FWfNmG`aB?C*Lh<zo#uMz;vt<%5Zxz#1i|xi5Zmc%v>y5DWD7PQV+a)I9q5aa$s(pzz
s5-ILEOCsXLdoFKswYq3cN%vvju@2gqSny0(fk&T4el)cK)WBc5?p$sjz0OXaUs0IzH}!O_w?@sC<B@=$QV30@vcP=3s?@-(9K4)
xtG=)QDZB-o^CX;1MVQ0S*-fcXH``*g%fNE`y4J*Y+_Fw-`rZ=PiTwRKA<&pfAKq7@*AQrGakycXn3kt4yN0L72pu8j0C;n7lwR@
OZ&<2yRV0G^;({r*ZoVMDA^D=QlFnZ9GMmPv-7h%4*_nh@y6=!zr3Yh&R&Oiv=hx2bXy<Pr}$%=v9@h?uS>hyI8|-<BxS}VU5T{U
(?>a@=%*Haq(B>`+q*cP{-;Rb))NPls&0$9pdEUdfrUTu`r+U68yoMx9V_WA{zH!~ApR2Ko?=)GX<<n1W;&QN6}RDRU#n>sQ}S69
=*Y(~v#xolz-Fwl?hVp+?FZV8TEY6nvD-Zp@tB|5^MEM)N!Jhmp5HiEuQxossj>PK{_m(sbI8EdRZ(lLTb?sSu6Bc=OS$^Bu<O)g
hI#K~B1?(SbOTwMzNhNbw$$2a!+tI019kQ<hZxRX@4vv#j0XL0kJ<RQL=zbp&YZNw5Quan)upCah{2)#%d`LkvsE=z+%u~_q6#Yx
FXGtpPz>antvoJ}dx>$ueS$UNwH3zy1lAh51JL`vzWg08i4Of2{mVqui%O#2QK4W!&gqMgiW?(yIPR4%luuAwLWQ*Kskq^e&ZN}i
!nqeWWq;y@7c;81NA!iprx&>8hU=~{DE7JA6ZfR#+f^pxAp~=n*qCn#3r|BD!$(rCidsMgV82A+^w}>_WptRAYln7tvMn)FX_zG5
Xz^F)EIEcJYPkRBDmDBmudvG{O_J<;X_A2Y3;s|KE)4QmwJr{`TK6i(IX84wRrL~?cR0ldl~hX7Lxo4+ISqRB@+xs#Xl;-j8^(G{
{cNx$Zq*unjvTmz7p(QhnyzP*Ca`#Q--mZi0!Y9FBw*+Rh+UDXXuA%Pooah%B1aANo$4|n5Gno4*@de?T)zgIt%+>zL@l&zjAU#M
7Y+=4%SWrg6&30$?0R}QQBcRXH4^GC0ri(=@RkpDc2)leva_zWz|^K5zUfpgTZCWBfD^OFDVz7KyTM*)GhslILy+!r_oDq|Sn&;Q
;iwRO`ttV75WyFkU$wMrp*5PCr%hSwYDB|&qnjllB8KvH><RnwC7`7zg^pt^KU{2Eb7`a8Xqn9T1+8;Gq4h*v1}yyB@Qd0@K<!0L
r!6*PjA;$4a(T>UxQZM`DMOF`6jxq0C)#kj6SL=tQ(UMw$mZih$@Wd$37!?(zK|?0t)F*=XYQB3*Xvn%qJ;6z{ylJi7*KmD2;T<P
@ykpzGv~0|t6UEjidBaaM#ITYfi0o{!(~p43WL#3)R-P8P-aYB3ijFzXIHIDFO`P<1#moNG1K|Q?|?~g2)iiyDqWN$%7AcZgzUB|
Mx+3P6{EI`Ghyo8nie&jNQxJ$R6*zMmhw7*?)`u;$q8uJ%I>w>y52vyUjAOMry1&=ae2GKBsqj#T+S`x2`SR9C`u#QpebNkEa<c;
iXWEU>fEwNn<_s=pv9P0%7}G5E}$g2-Di6Oa$CEfo3hQ3zv6XIysoDEt?-mOe_P>mR~ry^5w@XBZ15LWxmHU`3Ie4mmML|ZOxp|I
_9!5ttgKI_&#L^=yZHZkECFPQypmh+Pw2(wm+lt-{J|&e?jrO2l5fd8&E1$$KE~KCZkdEf-&0Xy54mesFV&<Op|%igD~qRXRiiYm
0EY{^pUN&fK?8I@e$`xYc&|1751-Ele*%0pi^P94i=g5XP;uFQ)R2lfkI+jE$o$r6dTu@R)QzftTa@k4kl@%s>+CYaP^zcIoE{fY
s!=h%a(&dhb~gJcC*Tnl;wQZRiPv8B%GPQCI{L=x?Sn|pL&XILl7$nN2`crcN<Ae(m3PS>_J}SYK6bjYRk2ilhh-u8T3bE3Q0vD9
na#l@ZTNt$@L9kUjlZ*qy|&0zIU!h-%l(!|PlTNE)_^R~c}xe*!(rZ6y;#FkSv$L;!&vCHSU<$)EkpC-8puIy3XNqsCYOf-cUDY%
T#)ywGue6rp{_RW^JQu{dsJVrt1jUV_4HeRSN6fZ&~AR{v#+b!t?sF8AtrB>Zi1`1nKc_Ta83zu+8Ty-l75-k5mUrJM)`8HdZgQ+
aM_ppobn?)D*z*}7W^l`@d-Hi=UaYHNr_XxRr?93xWEk_i)*HVv3l!s2-=b2YPsr5uVPP+sESV!y=WO2R^hU;)e8eC&bqT97|dLg
<Y=xsnif?N|B}Bwlkqe5cy?Ov6QZ{**QmGzR9sT1gAr7H?yCN~D(b_u(3B3XzMsxaJ_yC>s!$g&U1UTc&p=zrbm#66(6V1^dam4$
8Ua5cj+}bykMoP)5t9><acSF~%W=J9!a|=oG5UupbVoi3xqI!6IPGkXX^3UZ5F_q`lf*er#Fblhm(%HD6n^SawfX+Z_44<6-7*Yx
L%Db62m$pL3<4f&jXu+yv(!VePs^=R$;^Y+0MXdJo^j>nW>B$O;7|4t>Euv!hI(#_6!uN9;<b4KVrJ^axx}Ym0AGUV>Am22K)ofP
-XcU%`=B!6g}7%?zP4F>!f%z`)yc+MW8a)l+d^T)iPv85As=U50?-}pO1fiL+J$xePCLE<-cOro<-Z;~QX%RsR{!PMj*2cwQAkLs
7mF5=p0;9@`RM!R0)fe|)F4m%g*?1!E`JVb<b6tLaaZ#nfE`*(f1>igH_s~%@Wwy(3D@twMc&zsaa-fy?dc)nErj$(*%BAZ%BJf9
Jcc0BmeDYiH7;bDbb>Ov;zVGAqa0}>*xiDq19X=s8UH4|7K9`&9LU9fEmz~d47qUga-Jsd(Z9D~NrDKsFjt~n98oCskt42*my{oR
1dpb&s)~*#EYie@Fs%-lcc}QQmM*&e<N=acQQT=v8ULJPM=x_yAztsFfBrpRGIAVeXX-n4glJ1Zv}GY$rpkZOYYK<&S)k)F!r@h2
xaN$bjXf8YDc&H&>$>Xistu~*V6&s$@yV-d+42O-H0vMHTXa!^f5GZ+tik&04ZmBgw>Hi@5{hC=K(VDQMF?~mLsg8L6>|?o<vGx5
S7<=Q-!ciT&0EV#960;LuveMJ_Z^NoizfFKt;3Cj2QPhTEsKBrD{Ox&tJZ%UUm(~L5NruirPRc2(5Tu_r5D!GNE-@n0X_bv%3B3M
2}Tu4(i>CpjNX?pw9|KW0!Wy}<|rG^$F5CO<OmnPfDJd;Q>chHqObp@$VRaxpxCldGYG4C&Mvr|RlF$0!SgZJv2eR)CyHfR>mO+|
WGV?^pFYkucHqLBF*8XQ4lGo-*UQ<Y=g!!NvFEWe--O+G#2bz?a3-JMS5{mY1*BU{j%Wx9^Pw6VsUh_LFcuSyOFgPU40$kARF%G!
79F-bdM4vxY2A8UXbEu$HM$E23SjArAb$K4Ut!041}*(#1`X+!fOL!ERrfj3HfR)>dzc6WPL=;Q(hY>KoQ*}HL@}jhl=I_}@RxAn
r)PUv*<yzlH#K)Iae6g=AxQ55#rWs^X+FWGQ`u?1VRss#@9-`2M8t)`yoW<>At*+;=(H77CNU=<g1o8<OCij7&sp0VM^$>{S`dw{
TSRH(^TGkRtg&`($`=l<%Y;>#DBoxI@z43ga-v3M{(i&aZ<V-neM>J8aY6d$!6g}9Mi{oC;1iQ59o|=p6Ldq0PbiC6gqeGGvCTSH
6LA_te5%gfElJlNk*>P)>^@$T`7V8p8RZprITdREDOJ1GLjxKvjG`(G<i1QFs_5yCEn%7>b{5OgF_>86;7CiM+l<m8n)Gu|=$1X$
yg_n6P!-bR4OaZve7WoW2DWg(sfYah;&-qlJS1F<sS!_vAV9>1pfI4#yQN$aI56W7Kkl7Df{q;3$|CoupA;=~I9JwhD;0+|>iNuV
3G{?U@z&A5AGvb<@WOhYF7ZYT;dY~VN9mDr2}rrjrV46uB51@AjylD~TsPX>j8Ln((}R`{BO0oBrN7aVxW-gu)7Ga6{Bfb>;p0-;
-l(w!jh}BM<DdEpThVM!VZ`f;-@%gbka7|K&Z?e!-yTXctwZ%SH>j0qYbCs6mZS(ZP$%*!2>n5$XK*dHd|u%Il7b0xX`V|=&G=8S
=5{T5cYpx{$J+351h0=cD!wCn-&RppuIU(dC?}7}W!T{nLKi_3)iw%oZO`tjboFD)N^Fp14uynru{91n{WeAZynC&=U;bXNrvX>^
hXGeW#U<2z;5nx6CMz*}@1o+rLV=drV;igmHlusd<FrI(3|8KpD5lmpx6?zqQyoAz;F`So04&N@KiB?00Zt)aR!eW6IFww%R&wcm
c+*g~*outk+}EW?PZ=(8Y^ab`6eGOFk$i;iYi|K_P!YPT^BbU%C~8VcAAn1A=4+b!VTC!E-R2H&PiRqd33V%3x4dPWRCt<&u%Q@z
8KRpa#1p5N)MjUjUA4#2bDBNqSK6jm@z?|&pv);~zZ7#75?fR>ylh~X?;l(*f3Me=_vwm1zxW+6ISw6{Vq2_HR8bI?pFRiti$fHN
;J8~+SXs|cT9%ip8LrnA?>GrX^BjSS6X?!U@Sq#ekG(-ZA=Za?4O#nld<`)dY&!8s2%K-Cm?l!uhSxLY8uY+*jA6qZNwh(apGpl;
v=AJP_Cst>6uCbxq?uP$9Zy`!)TqNHE9xDe58Z{=J@Ez`@3&ksmo4J^-9ffP*~PDwRfp=SVvZD3uF!F0R{ok|pvJjAnSP>!cQ-kR
m8ym=h1R7(J-#7x9Ig`OwEl?KakzgG54ayp_ZhppjgG@Vu1`^Sfto&!qpzl#Es8;C|BmXl3A5?37jhOhAU4M3#O{u&=Tw`nEb+GF
7%HMtJb~`D-jhx@U>t>+X0kb62FDlP^ejl-pSV|_cPtJGTX5FA+13%Imx$8K6o*iysUk?9yfbD}df=I=O`r{;O*~>h6yKT)t?#}Z
@0v-=R)xLV9v9%stC(xNaG;*-zeMKr$9~}EWnY|bUCwt=F7oiit?rVN-|nyC>nR)o=Qs|Bl+RQy+2R-pSZOO`puW~(ucj-&HKiF>
&mEn&eGUF$#a^aR+@PxDV~&zb690nL-B{gDh1;%;x=CS{^U!yw9jNi_L-W`rn~7@)IgdkZS%Gy7Qx6eVruL8zEf{HF4KfuFE2XzZ
y!dgUO}x^od})+bnw35O4NiPEJHCCc{E6CaJB;%UpKcpi_ZGDWwNjv-reJ(f^cA;R1_M|<b1jKZIz|suUD^g1W=?N0kXBH1Do`4N
R(T84Y_wz)e5Jz^bxE)NS>>s?_JobQ)xJI}=NG?&4S-epOH-+#Y75}hE{IWd!yr}`#4>!RzrxL_6*eJ8e-u&w%-mV8<ioAKzCp5!
nWwBzu%Fyueg^yBtY9LODG^ndwzNiDtYG?J30!vO8C>R4JvcK1QW4rEi!A6Av5RU^UqhfFbzfEkk_Hjfm8-iNgA~K_%dE1C*Zb$6
f3F5Ps%Bc`gMYiS39$QiZ*}G7j5cyn-W4J9sxHhF;UQVLFgzc)nUK*6A*TAPT>Wd89FGemo0oRZC)gsgkUyvCZ(t)`|NGkaoisp1
!X<7A7k%og73aQ5Rn@Fe%(34HRy>|KH&Z@rkBz$z+Ph=G2+R4vb+I|Ofk2X@_Ymlxn+N@1)%Q_B|GmE9_Wv{%e7g?{Xt~xyTu~89
wVF}DjoWGdK#}thnJ_q!gi!P=8N~yOiS$9c;cDV<V$tV52wUt{#Mznh8`|&_+Dkjqy`Q3vC_P~8{$OxAi}ggW(5qrj+jX@l);p>`
T|M~81XC3Trm~$%rJTiaws1$BscaDuP(paT_U>ko={!gAuY))7N3h$2Yuj4AOB86dL^N7>W>UwOxCuh{As6f5nMElh>fIDvZxy+H
aWa+qdg7F}RdFQa<4M*4xp%GN)ww(OIed7zO$zDH>;L~fU#=6^^!~&(BF{qJeqffnN`=H|zlySFqoAeALj^r{lM1(b+lchg(Tzpo
@W(_FJ~L^*^8=2=WHnpQ^N{rC`@M{-KcS5r{*hhdyHmhOCq9Q?;=y|9!`5&dO1er^PC3~fR?n7+oJ}yS?ig+wnSuT>#Cou<NX@i$
K4Ud96zjETU3o5T!6GF^&I-=6?EC-o3)brmcN*u!_nOENffjW7A6eCoU(^uxXuDfUMZHBviwTdz&(^dFRuEHOqBh;CL}fpxB3f}2
P60vdH)?kh%5?T=ZfQtm6>Wy++x%Hh)cMcpAH^GPH|162BHnIe(i$QyV$8Lwko4NL-L%7I0W-?Ks@rM2DzwOpS&mU>9JPfUN!QUU
^3Bpt)Iv+9V2aFKI1m%fUn-9Dr@X>0_oSP7Kj{|HWr^sr9Qy6V6U^X9$uVSr37cvTZU?v&7fqYUJfkx0778QU8?;EP=<mA~c7r7N
Ivm5#Z9xuBIe*Q;_4@Pg_01W3!#`p#k}MHP7UhO{w2qIN!?`|Th??CDNMj#iqAC=)9B88)U92+dK~!EVD*avGm-`ze0Rr_0^8}l>
7Qm}G**CDKrfdrDHDx1mEF9%NFie=Cc2j!8()pNHQP`(_MNYz~xhh8=$1x^R!j6`Wi}aG&u||GeAon)N=GvvZ{VJ2>lm4!`lmKtA
XKBxOr*qqWCsGU*aoX~(DvHRmL}Xbk#xecCset|ieU8hmIkiuxiv5@-77H0$RPjVHVUdWwL^L^$XMW{z0p7riE$#z&2`>tr7d5x$
6Lh{k^)|}+#qWSga>%mKLVUDRX>dFePJz~YdLPZf#o^o|k0O`{v)%i?E1}t=&{k|uOsSqgNy!eg(I?<S|M}M}_Z@J~`{do8U;GM~
!$yu}9%(dRs%lGmte8lr$Eukn5_t@aMzd`Ps;GJbGaW65_S~`0>s?*z+!~duTK%GCyC?%>i$HJ(&oy5uUl-Uu@w!~@xBPYvL1XZp
Fm9yvfrzL_kfH4(&2iwmrst5RwnKq|{*~mnO8o&ft7BQeEV~r@9+$ee+Yxa?X02)3b2pH0c`x5T`2^mcbAwzThIbtl5jB>$)mX%6
nn+{HWhCvCj5KS~Mm)MA-L#mp+bZs+&m{T0&|xtu(uS|1?OTmyBc&uFz?7H8-uHH)kW7OAgx5XsMw{-pT-i^edEd+w(PfF3E=z)+
FMrh1Z3m}C-X>={O3|gxXsAzRL-F>aa#>ra=zFn@BkU(pkZFTgSzp}~2nq1j5z*g2_=KG)kbD~qzIzhUWx>YqvCRr{p$pF+)SF!_
%qTIZNh3bi){B$LwhK@ir6=21R4H%8{l^8AY@)qUu07z-DP)fS_K@uT8Myn$H(q}wMS94H(ws29y(isfsCbk-DkgDlV65xL^3)&P
jvsC@oyQ?;MP#j;qf}MRP36&0nqOjg%87Od5g=2H`V?&WfKJc&=fmT4Hod)IzaGHE{p$NCkz|N4%j%pQtJ2`8xCQ1*MdE55hlvA!
gEm4CAsKy!K(n6ssc=F5oocOfUnjJd^qQY%QU06hQ2q_@e=;442(w^Q@=*BAdY<S+NULu1K(6;gtgcmbh(ihDio-5EzdRzvB~Mi_
xlX(G{n7?XUhyTnj}=BX^UE;dPk^)ClbY8TzXK)_BFqvKrzvrmu}o^Bo4ts|iBNPixC(VcWt6G8r{xAsVmXFGOQ#ac&=vAHf%^UU
)mkrH;bhJ6a|=j1Tl3P@OSoTmyXMx+de^rZ5oV!1<B{}t_0e-$B9<|ha)otsAvTLH$YHews-Dg?BbvUdW7ob?kN)UIrS#(h$_fWW
Xm3Ej6sJERKJS>!`#YwHGE4M(V8L<K*%B>l)2Ox!gp0OZb3%p_+3?+3KNk0pBEw9Na4}MiO6tw%Xpr29ox4fTUgBWC6{z0<U&r(A
{qcN6nI-ydG8B5jkU<&kK=~oWB39I+BE%Az-Um`KC^{=TC@Xd@Lh2Of7`?l)kBk9IHo-#p3Sn_e6qIj=R`<#5Ra4XQxKCgAA=|q>
fiO$-du*WuT+y@x3?)ZJN;!%N<zl)wD($-q+9BC4L&NM5T5VjGAB73^P4EG_0f!vT2Vkv({oHi*BjDXs%6#-Y8PSL^3-=Qb=k1!Q
SWz`CkMEej&5F2QK9VTE#bcwHf^z(vT3;Iuui%%>#OQM$umF^&E+lh5T-2)k8~;$0f5)4icwI5~ThW<YzvAs~CjFtzf&*P1tnNTS
nI4Lka$QP$Re5>PX)z3hp*Vd((?p-D5b&JPr?HRaflT@fB7XG+x_>!$yRoOw*b_2Y_kG^G>JQ2r5oYmt8k9I@+!tSnYKzlhn(HGW
FVD_o<V<=*%Sz3v7EmE`DCFThb3T3<nIOHEWZVZ}wCuhfx%>o}$<6HE+rLGGS&%+>*s4G#{-!F`w`SrI(Bkm`D<OAII#p9e4rW;B
z#NnhdJH=PYyJc*pnHXDxsHfVQO>P^MTu>{;>}OIE{6N9xChDpr5PWQR>1*&H)7=`vQrps67PW%AsMgT>{nEcQk54`?Qf<<@sBD(
eMD7|WSH}qGti`>S1hmXEA*FfoO{FP&)Bmz@ouHB=NG>NCjFttqBKm|F%YO0C(?tb#KtiJCM~M8VrfiVcv`r(C++G~y9FKP5zZ4X
fD)TUXYYJ1z}lUZt>PIfR$Tssw><HN>*$LxUg{O4?OW(1LUdU~Y_x+_J82!YmqqLBA+n(mEEa^3Zs6221|^i{8?yaT5lZDiLfX>r
2Qj*R73Sk^X}N&xwSL*xPlTVa7nT{fVsn1+D`0e4aOZmL<H4@&;NbSXDk@tA5|t;`SUclkTVBdK*&HSf&y`Na$UEtK?XD9r(zCpV
dY4sYpM6I6ZF77ByhT{f&Zc)IENU$1>pWti6~t(*FrR7)54~?i+)4?+rTcbBaNCnp>}@i9lPXt~<7i<&hydN2Bb`dbCt&Jf+8hJY
QNDcO&Ce^yvK_L{cl_=w#JcS54H?A{*MyH$MUARIVq3^*PxzULzp`PrK|GIB*(gFyk8CcConiMHlyy{?AMxDP$?kJoMay{O_>m&z
eII!N=jBX>TcY~yz91QHAr=#|O?0p{1qNSns}kFA1@B0_J9*@^!dSL5_=(5t#5@%hPJ3*+A(ZF7z%2cOgAu}Ox10SD>=pw^{`}&1
u%th9SQNLkIT!L{BdIj9+(9W?bS5MfHZXZ=wNH_HE+^NBt&4xgEgkQ7)8+;VSyv&mH}MG;w+xan)5gBMV0Aav-C?ocu)D99IjwhX
kP$tWh#rgff|kqZv1`t84ujhItbQVNub8~JZW7dG6{ki2#hexRW^jGrD1SbBTsi7BS+mQfysxKKrhQ?c`Hy>r?QZ%R{y{&{V~Oao
2vm1Wg7l*)IU80>HA(a;O}EH*F|L|0?a}st!pg@8sLZw{dOA0o6Ucowr&zj2B=ZkaH!lB#HqZyc0aJL_5E2n&p#$`B*rJabhZMG>
_N^Iq9yptZIa*s>`>n3W?ocVB$SXpM(LGXvOTWx`Tqp^{$<<<iK^x4EYYPY3;}~zr5Q;1jMHWR??Er;gq+~fJ8sZFvo735>o}mmQ
%?FCJHssdCnp!Y(Apx%c-{l@C_u7VYz&BrZkpbz)z!2X)p}4X7=gQiAy>SXVXa9brDWb^2CHKP&L8gf?Wj%jW6z)hJmz2UpmZ;}E
Rz(Um=wYi>^_24r8KyS1f6seqp=C}*iOyc|_Km*{<@1nlKF!r`*#2xrCxOLxVpx%0;fNv&vm7c$kt0BaK$KzW^Bt-?#NNz|+9+*`
BfBki)W%jI#>7Z58*QJ*2@>-eB|8_*1?R&J%)%P35OIPHH`tK#^@iJW!<@st<@HFjV6pq~s}<J}W{oX1Uk$AwWwF}Ew>0#?d4-SZ
sZZtzu`_)mwuB_So#z@Sx07AUuEYz+k4<FxPk6;mXy9Oo%L@M%Eg23?7V(Eg!zLOlt~S;8wkdL|#P7&bD=cb}1>9hQYQ!-8LN5gG
;W)b8sTq`TWEBVHUNtIIEpGMr+@CebjWs^8UVobqLE{QCY45K3IELc<8b09|w9?{5*R&~&UHGSQ#HEEja9K~n$JHu9wgi!8#p1dq
xojW5>C;bpiE-SzV8DL@-MksEA7_689j|Xanm3pizEuQ>2(qB%`p8+3>I#0U@^DDab&DulnancL#A#?^!eqiwlql-up<=5!y6oe*
E$SYv&_5Pp`oJ8`msa%rMEUo8DgW(O2SJvIAPe$QsKpwy8rE;?(5~jX*Q{Q|a*inW*M?Qm*KyE340_Muuobv&AI%EnW)j)vcwd=r
7p44^J1s9*(~ULU-=BvU+u80dXwn_3EJeGRE8ecnDJ(}HGl&Fh&CuL*{%~Gd&9JSPU*ejI*|hoVZ(7w<yN?C19Li>IoqvMPh@f%(
eqUSX>k>Ghpwr&G=Nr~~8tJvv@hxi79;z%`Mtv@opsR|Ib&(6_6E?h7;nyk*<LN_z-zokSpQ~5phjxdVZrj0cv^;<eK)MSDJy<D!
&C&T4cE+LugGO_H@jF<u-d1H%a1gt6-Q}Y}%myNx@u)N&kHd+*p}%=d1>oka7J46EPL&>0Pt^%lAi2=dw!KnuJ}>(`vQz1U{hV0K
jWrp2y|JB$+`iO&2b!dZD9bRVmSq)_wKa}o<{%zlw0ehKZsG4sJBw;iKSr*hHsrJ%<F6?kb!^TCScruPZmAax&a|@od~A{blvmW{
?!oc@=)pmhB_hh=IO?vVV%^h=SL2F!#VJ<7h-qtK5UA+WXvxrOs<(r4rJ9DZQh1yochhv%UcT3C_tfvRDK1L9dBIw5tY=>dZ&)&P
=HB@2-4o(05pfnqy;S2h#$S>4I-KH!wrHK`&x;gmtCrM8MPGq?85Ju1aAg>J!{<Ir1}y<OmwY{X`>x%-4#nR1USQX|k=OkrL375y
5$dD);MSoyr+TyR#_mI#z_+rr4@RLay=#Y{ylQNV9ZlzkgSNvLG43)cpYuP8leMIK(Y_MRpV6Mj^zk3Z^jsxUfjvZj6iS(x7jbJf
&$<{cS8O<rBJ$hxboG=-AWOB0HjkTGbaPtf0m`|wRcTMJg_h~FAUdrrv`r{aZ~N>U?0H+Aw@+ia-w7d+L;OE_o)Bokk@=BZAyOTl
kSbO|^QaTY5!1j?jV>k?n?5V2I6C7*EUMD9!@0nhtvtN}v&<?#;~5mr_J6}!O4){j;rR<)KmL1t>n_s4t?Hf)DenE`LPV;Cv+GBt
r8|^Eg+FSc$Fv6XUc+p(6A$j%6Uictj9yn7BRRxHOzA@<VclyEWMXph)u$WCw=GidpL_yu&+eg9KjbZ9avusUp`o_Pa8l@{&=wu1
p0eGRrLCZ<bacJ$32OAZ8dsAlxPs~{4o5d)pY}Ppl9zQKi(Qiaa+v%hU|f9mb(wn`=SX`fw6s=~w1O7cnal^@70*UV!E%wO5@|)1
cq06RhS=B`S6?lwqD_a={N|ki-Mb^{-|+!By+&p4e*vuW=6^e<>@R)?OzKO!(Zz^|%%s@M;HHvwQ-D15mNhjapC*Fjhaz1Rog=AW
`zhWp4n4M@>j{+Ls^Ajh*F7Pk?A+Bx{{h%N0sAYSz)TV1WRf|)y-Y=-1ufEtk0mM59bwqYjG&&JBGQp(?|K}oZ=Pv&*X-mTZzx+1
6{=Rh%f!@ib5Hy?b_^-r)f)(%o%LI3eea$dJCS*xWcl-pUjd^w5VtUksB#L8n;fA#*6fGMVy7IPmzLHJ?Pi5#E6UtQnq}g!YmtzQ
rs=_aoIrOw6c_W?n)>sm&%?-zo;~kA;q_0v=e15gO)=|LP`S6zNrgzXI5Bn_)p4Fm7Ek5VA-vQhP8`B<tF?}SY1N4Juqsu>t%s-v
9?NI!sOPi=#NWO^=TQ3#(YO9Hc1$rzhu)rF{0^9Oh%O7BqOJPe>`;^ttF%e=5_1<?<?dT(YgO^;f{^pkRl+QkI!(;_h5D9(+dw(e
s<zy_)c+dnz9XiTI>o);u?>V-aAA6=;P74yC~DiTT<kzaOAM{3{+Ng^IGS9v1o|Q@CBZ|lN7zGVT@S+JM7p;#zi)iq9s1-E@Wr?w
f5ID{c%LVuDs#6kRXL4ye@9MEM4)9b`!*({r^yY~fxRv5bxJ4HryMkNhGvf;lB7U4F{<^Vc4Bt=-S*}HF^Q#y(^%`oQT@J&f4vaS
=MDA?^nk6w-8b?saxmT)(Ps&%9^wuOA!ppF4h)pM@^VLTDDvN9%Ap@44NKPmcIR#yr%bB{W}ngmlrYUr_qEjVzG}$Zk@u!bH{STf
>ptGv0|NiPbYL=!c>+%8!aUl+e3lBlFzD^Xlv+G#u~9Ak0xDrRYeY8PBk-;8esrXK%Hx8(AH<Yw`hdPAwZ1-x@iX>#GrfNZX+@M;
up)V^6vQFsT4>{HU*O=HOS4UE$XYtG7aGuu&bUl>j%wM_Owli<%G>PYS~O(|dbA>5fcJ%PdFf1a&mUYbf3Mfb$vss_e0zkCLJOiF
4^_)kR5=tRa4QZo-J%(5Rk0ez%b3E^{uaf<4Yngv9)cJ36Fq5XkB)%i58%Z{jrjl^wo~ovWZ6%EbBwnt$J-Sq4{ntfQnhHCJ`lLQ
r2-Uxo-?_o+-Mf@MD&)1lEH|HGEg*QBA0s1E7T#NtgQ*MYuDymGq7Ny>7KVa>HhJJw?5xVXb=BWJTOAv8AE$ihxY^hZ>qLC@>5C4
A}Nrld~)1!i!UweZ+f(w9!#;jbsSqRwKK!G5o5ZhU)*Q^f&9C8>xu9cdj604tr4{rKG4T<rKeH2H8TiWBsvuw>XPV*;3rRz#^2Ws
GsYC*KKc=jsxP0~)_UGRi2}x%I}L6D;_xCsZ0j$8J;WIy9sia=qu2tIdWaNpk}2w}!ilS2gq;&Tsa!WGGbw>X`Z{8$G-~uwx4482
dtCK#0WG}x=T%?%(N;b`FDb8s0xnhmldXJYl8u?>$1dCyaU&zrhiC>jQYmAtKqomaL}RygdAc4Zx^7I$Bt78z9k(GSKpE5v9M!oG
z);a|@$Ea{aM_8xZ{Olf0!O!pNUup#HFp}Zi{80|>**Qsai#e>(TA<Hh-{hbQ2|?92LWe=Y`^w7%m%u*1o{xKE9|+`&08oie!^Ry
cw-LtTW+^w>{ivcYfTzNv_(XoZt2!zGbqw!-;LQ9y9u{f(Zh~)c<7jiiEW6KELGn-NxBu!-5hJ#k6$)-Xy&N7x|d#^>s;pE)Hn8e
3t-y!0+^8wET%{w+Mz?W>uRo}eHoXD3_PgN5)Cy@kEKGx5RV(q8h;>2ytJg9t9OX>;{?i_!)XS5-b0ylH~X*g!kPQ!@AayUe5rlq
x0{3Hhf+&nX@`oEYV^TtC->Q{5=UM5e4`qvg*pPZccRcVD~8y+@<?8ow4Hz{DS55YTo<Tz`$2P%6(W^IFrV<+Cti15AnUCV>m{9Q
-<|BE+Y-@jY1N9h;ohr95eWe%a=HtxO+WN(9LGTR#KmBgPi&@pwH-6$RhmB?JU3(_2U7g!^X5LDK>E_GeO?ON`{#eJZ(Vx+Bf)Hb
7x~{i>|{h_T#_=PQ({io<_4r9dKKqD(9^j?3rBa9qDzm5XVeZeb3cwfsnQyqRwriKBkevrzkpD!xbiiKT!i(B9RgUcVRrZK-j%v2
qTo`{)ne@a2r8|$%zYWgX#=(wH65v94-Tz7YCJd=OL<QE7{^hUJptRiqaL4F`T%UWT!~yFhv&Y&Ui=g9O<{4pLq)gP^p6%P`cC84
b6IsD(Vz!QMRugMSxG01ejY`xp-r#7Jrl-TW0_Gpqm|x5{^teVa|fYUZT4^j`OzpR|G7?4pWu;p-N*gz{Ni`S<U~YWau!*uQ$e`K
AtK>u4{zSk1W}h#AIGM!CQ2=_KE*zf370K0+-18cfs_*hj0dmO=k^@4HQzc)T)1EU-rw$4E)KEZ#%V-d@J4v(nImb~jD1JPXGjq+
x1zv|WS~-bPby%8R}ONeAX&>S&4H$>kJ}S$1KmrUY_uPM^-+|sar!%8CA0tSW}N-S?|{jPh`RVtIUlIzQ2HK0iNr^3Rb~~(AsRX(
hth{ja~^A<w_uu8fsn^YQ9Sx_0o{N(?>zy<-)@UtykGuauNk15iM~fnDn!-A8^&W0_YuWcs<wIp%#j&45@AwljM<v&-fc63<`~5|
rNW0Q+%5D2(z+kOlJBs4_B5+XDf$;!_Z4q?;!PLTbK4N~Ced$q2T5`3yHxC{RF)pTc<&A*);(G9{~9}!9Z8xbIloJs>tOpbuhM7`
ZX4z>7y_Ij!3*D=@|n9wZdG30js7Duvi>d!Pcv0fGgT2YdvT4>n~GUl6m?-XDAZ%<=cQpFJx=Il>m8^pEO$&xe{3;HU%{u#QHg_)
@Q9eKh`x(LLOi-33Ikc2uPr+i-jFRihSHwt^vTVp>U?$;d`At5E6}#|6TfAzPNYyK68-g1KL|(OVsdxIas$q9!0t|@nGtc)V&H#I
*hz~BymTe)<y3O%Z)nkC#)kYTYPr1}7()$%%d(!hl1&!ig;OmP+#Epfr!CC1Zv^MIeBcR$jIJV;)+$bE-T?Q@MNhZe-TN)trB0Qw
$3RU|tlOw>48!bb@l6@8Aj_>-eb6b_v{IbnGp>iq7%C;(LBQ)4F@F>Tw?)`Syq~&{cPG;6duM+XTdsVC{w@XFb19Hec;UWO<mu2u
cH0t2l`{=KJp3Y36}9AzYFd}4!gCfIOsaVghw2C_q;=(!fdG^&?m~&-18}BACfbPR{x`h!jW=ASJKZ!n-3H9*3A%ml!}r%hr&p|g
%&>fkttqyZL!Y}jBs>fTD=sJ%wivNFPrXdrn157sPIXr?K!!YNJEu1`ZtXwG_+N*Qu71T{f0gJj;kze2-9&*$=6ngDh&`eRs$|02
7jaB>9L~3JAVo><E%)O|xzTrJdrLbK+TkUdof8EVNx^`s%hlU;GHaiHRiwG>eIj<@_2!K?zyF23nsc?!{Smtv98&qpDh0h@*P?Kz
PmFe>*mFyGF<XZ`q7r)1dZ$U)*4e8zrTBPCXz}g}7sPv&lw97>n0);tFnDG2D@WeYy}6fl{@bz+0H$E{+<gZwD*`ubeK3{MQXDE0
kLnn$vIg<HFs;WXac<Xeal*mkc%4A&e$*(Co`60U1;W9|#=9?o?HjPYehZ$7&FvUm`QH=v2=<8V@+gGiAj%gVoNwrBJjISS5Klqh
6Q90NaINS?IUh3%`pU7}eVv%O!3Zk9E{5;z@7-1MyXEc%Z_f>=fBbDHCJ=L8x`qnIH3Jfu6)F5F!q*h2l_ZbhqG~Xk$|Q*%Q;V8O
?pnKu;JD7FH&T`d4u#j#bX%^C>nwfd8t(G^#_QgA-wk?>UK5ygd}h`OQJ91%3|hHPWtL-WItCo{f2NG>Gc6HtkPekqMxaAJB)o%$
GKyD;nUCFaw;}I`jbP6Q^q9<#{)2nH+}P<JC9jw3i$4P{0Om5WmM#k2BE*U7L&6^wZOq-N<ZW)xx~;6(;-IgUKDW}j11+aLDL~==
SiM{O0oZUKtWA^jDLx+Ze(`U-{{AgsSBeZFN38xaid3L0IdTWo1M=s-iyS#6#ymL0n5+1jd*<THpqs~~(kLU%SQM~B+lmG8bwP$i
;S6YRAjH4uzjseu_qT8C{x%MB&$GG-p_qhF43(6__#;K}Bf2_*f-zDRZN%Xf%T;>o9k2T3aH}s@58qfLA|~52`2@NbN2=G+0f1@$
;Sk!ERNiaj!W-Urqj|q&>C)Xz#*YDzu1comUINz+m9XeX5BjbYL3~!3n9@)sGmAGZY6to??V(E253&(fEczD|DPI@ly(P<CG5T|+
^k+xE4_~qGBej2SW7zy8u8>fU;Q;X!RdE^AO7&Z(6IXF9)I7ES47v&mAQp2%W%VWs7e~pQz!&XUk?!6$5dkRW3?u02GhqLtn)w~z
`Y(uzCq!c~vV6s5nsaH5RF7ldj|(PG7w<C{Rt`($A^zi8tiw!IwTNG3RWrV9`Hl^AXY*kE)gtfrz+?P$TYEPd$NS|U_qS!sCfa9D
=7e4h=Mpb#mG{i{nJdKx#pP)T4Y4ceWrNb$<ZNLboB@|i&y|)p<3T}$b#Fg_5;;`r=K2BHME7F?;V0lr@47zgT_<MTkqUejq#Tai
hi?qBC6pcW?$hm4VZ`({SGR~cDNe(tZEDmynKp|aH<=dDvH?3WjW=K=dWr&76t29N!i6`z@rLT}x7=0>W*XK%u4XbK3NmGs!;ZCZ
Ew-yEIT|DnnTsBxPN`3f&P7R*f{H(~wqy%kWmn5>&U8L&S4q}^RT6F>+^EJ+x3%v6!58d=Wa0(1+drjnmLX-a;zb&VGd4q-%|swS
m373(i9ta-QxDR{<Ip};Qtv~RS6AL!v)g){#~*t+^BT={^X<1KIzF`eOH_WoLtVOmeB*W3fr;J<W~<v)yfvPnlM&I8@tlDm4qK)f
7@!X^h>A*@xWnum|4vSFrnrcLbzBG|rsn&B5zh7`*pLZzgqAlDvdZUk5O@FJ3wG?IIUA#Le_q$*L3CtFYY65YD$fu6-CSh^L|GhV
$4Tp27YqSic-jt5NmoXK5CfdH<v=%3(u&sC)kWyfB2m>!q&kat&2{4~Z@k{V-#QPhwUwWl9*QyuW4;b9D@Bs6e)XuXa)HY{8?zSs
c)vOTt437Fvlx3Ta;OYwGw7GlHv0fFQ939I#t-O$!+dQq#*zK|Bkh-~<nm=tcU*7T67OgdpP-WwQIsiD2$j%d+s9uj5#up9>~Irj
HQ^N*;pRi@LW|z1B-n;|NxL_w7JgljDHkK3=>|d@{pY#ZdjH@Hc9n~a;uS$DPcwN5L7B7#Wt@r~Zyfq~!6;><xOHB|-HLL|5;N);
!r^e~*OA9`o+cWtf|%-_)!aaN*3tUw$py+qRgskD1>DzJ)IAeo-gxhJ<v^C-W2WIRtQtX?grJPdz=al7<T@aY&JYf_Ga?i<WSkbd
-t^5Mv`_1sjHHAr92%bNd0z))R(N##QsRd0Kl>_N>?4>j*n_z(z4NmPOX8@Au7{WMOKVfv+N`4AzgI=2=R0$r+gM5o5$7f)^1^t!
P#mG>a?pxO4ZjOqfbPZN({)R?0V5^%eZ1)>;O))J$@!y6Z$d^UAtTe3!JKzoS~UF)^Z|+HplLGA_V+$ksq;8QLs}qiyW+}ZcbQIu
>gxi!7l+cj{Q#_excxJ#e_tHkc<l$?`zMGBo15u9ZbWh;f-=snGz>kxD?4OBhU(h2R3+{?Q}l-NT7w(Krm%O|+8O-DjYFyE+=xJ?
3{Z`g-q-{^f7kuW?=^B`w`XViX`%iY^vI2FAElBOF}p2+p8A00CZc}IDF^|o@NLz$h`yaF@eyM~`Cp9tU_R=6)&ja$bH4kMHsHL^
-@h`wpMW!WE~nn~<7y@&A}E8Po9!M&HQ^|6D)q&VrIdn+Y8f#m5w?SJCQR+Zp?@eR&XBTI2HjCwKv6;taXX}KAp2@AelnB2V}`q5
{&Br#lWu?E$0tliL{NrK2?n|?U2Q>CY@f;dGV@_cCv!RFk#>x(V$9=$)KW^?m;w`V27jGE_id4a`(_`7iQb5*3|+W%vENJ9T|d3i
o}KNy6ZSj+ImJAk=pidZP4OxSOsTjMA;n)vHHy##v;Y}B%*ykT!z0C%n#AW8YL|+MBJC<1j&!b!8aMSw#_oW-aT6y$qQ<6wWsf3X
xHnktFqEgxFa8Xc1nBoDy|Q*z?2TnA%#LxaNuizh>5BeHQDNKlKnLCR;w46m&I|=L^vJhZ0U((V35hv|H`wfh`Fb?{18iob=@gWG
Dprt_p;h%oyQs(v7tCg5m8ZrYj*FJIR7)9s3dX0!jKraisZ^QGN_Ew4O{-cfuM_0%LQuf8=My|v@SXrr{P5>iyRo_(t9$?H?US9#
{_{_$$$MzZFc~dwoSVbd&vhc3QS6{JtSujUoV|*5q?wHCdf<lPI4?@A3MZcx3us}{IH=V(>JZJhv{!z)&#<`<4|g06PhiP;sK}VZ
92qt->q=%vfxPrwj%~tXT!_6@;nPpF4tg_Oce*1e5xQK@zKL{tnudhE@&{NPEX8uLShD34R)1r?|FkxqHX81A{^?q4iznhg@tW+a
I+<fZa>Z}DmR)OFtF8NnL5b`1z1lVus_`4H<h_W(UD<U?qO#)kvVttXesd9SZhRlGJ$^?2+@?n1sogly+`zdQBUz#qNnw`4J7(r=
oJv=VMw3Aia5!y>D8xmqO$<33vy^UfvPWYs_(Vwsi?dAnhE{(LZ{FZOfekm<c!dr8Ah!m2d^T7}99ShJWD=L1%2#`Y+cQhw#EVQ@
shKjc9c~I@M+`^tDqmH#*rJ88Oy}Yy?REp;LN3yF$GUL*?f|;{3ZHR@Ti!iC%eyD^V^B#{5JmuLp{*eHi;hK0Q@`OUdNHda!sNvB
Fudm*Mc<*{$XtF|#4OH-EWWct1;3;}q4mE*oAw+ebHMd63X|%PjM*ajNjwdWxoB4(T-w_@f<n_F3VCqJS*jDS?0zwds+u+xW0?9c
XB0l$`9rGVTEOx5dd}rny#D!*^JU+}#%=%hwB68)p`d-mLD#J_%Ah@ry2KqPrICpu#;WHO3jFesnWmI{Q?L-R7=*u~8ftqgY?N@d
+g!Np(c|JijhOoITd>rm^fy0RDI`Q*5?V1y`|22&Da@(og~InCT7l}6n6<--+S)@O>F|mQK`%wyQsokYd#Ax>xa@?rid^*H9&I7(
r1PBi2AgiM;ra~e7fqwc<i*ExM1*2EpLs>oBGs}&S|7?y2e;e7g>J}W+EZC&^l(&nDxIbn>3}PXL0j9lGvkSt(nG-|`x{2}pRE*v
|0Lpkp-#8aSba7cOX$QP@2Mhs=~t)hg=)=gg0T?boQ2E!hNR9KKA-~8R971jip9aGSbd4wd^=|V62hY`m&_aNS68(B05<*&EC~*s
7;LV5SX@Lp1^-qio5@YprlJ)L$WIF=?pfLS5I5!ou2pdfU&SsrtIX#^R9ra==(0zScY=$1IPvTszOm*Ts}1FP!*SQ}_YB9FS3)O7
JZEu(!!?83YThHHl|oHMj7-1%k;N1(r=3~Bt$XYHGIolHQdIBY3)+o3ri<Hd)YwpbqiOjw>?`DABJv!2(TPdu#EiAuF16{~Rz;?$
n`LR0Mk;^nR(DBpO+f%Xn50kEf~i_8B1uO(A2Dl*R|L&3IKLf;{fYKm5aDkNg1m-KjH_PHb7mCMRO%dCrXn&M(UwXp&R@lIMA6XS
$qE{?V?UXdDO9I!4{T6wQkhlt$NSNif_RJq9m4)TeZpF9tf7YM4W;*6o9U_4r$)yY{N>EBg_H1r7^JwOgNKW|i}PTQ?gJ9BMbtgP
%z9a6qUpTQkThk-V9@RWq1A0J95lle|D9Bp&#>W=y8$MiU;G&?=?$3}h0`9ZxIxr&>>VFaAsIDKRU2!RuD^do4)Im(F(<Em<^{8%
d^_vrXMiMO6cr%nDy`?G2zrBB^w;g=jkVrbZM^^V4!!$Q^+~%qp%;_3UW}st;9h|dZe_OKPbr%gaffIlbLQz`>4C2Kl(qO*8<U}F
G@M@-+P&}XsWMi6GuQ3zAAG`HwG{(}TsXh@Gg|W8mWesEn^Y3v8=koyg{bvN5kC(!u|yhzg0s^zSN8Tt9`?|dWKLGgch^RsWYZPr
ZG1mt@xAh$L3{&ydC!?=@3}<J2WIgvCa!HBLB#98MLe4BI`go~BC#uzVUDi4Uc^2QhENXi_!LX$@N+xOoFGZc#XJ82Ru7z>Kd8r7
tmh2+`DF9`4iO@rW>`<KNp$GMw55tyWDx&$45M)Ni#^j*8)K#kJ36Jp8H5w;wd=Eq)D(`-)>+8`mrYlKclO4CI_RfNcYPjfz98pY
tSb`KIXx~4k{u#3zSnUml_gwu4K_wc2`Vp|R<6qVfw!uq4L8=R$dFtRg@{Vc2LSUXKLF*Bs>HJ|-~uda^Ubv2cYybi$$94Ubauiu
J`?$`c+eT9DmZR^kHw}xx{Ahi<T`}6Biv`k?g}oVYOG>$xPVmM+J?a!=mwnPeH^jp&ap5mst}3B`3qkA#%r%CpMh=;F3$^`rxcA`
41Vt~Z!r`1^axkc#U*fzmZx~6Ogm1<N3lpj`ZZlp&8HohnKnMC@zS|C(s?mi@GJd*{$&SVVb0pG*zLc(2}yh?#T?A)_hn;RY_Q&^
iU~uNsqgeKl>!ynW{;zk#MFZk#aFym#g_&2TpT&=>qss|+y~(8&Kzl;D(|D83$J_QJ+0jLTRysf!J#>!8^d($ONH<%y(p3GyCH`i
$I;XD+J&Kezn1d0;Y8W)-r?ZewAt=l+4mDTArtJB-Y@cQ&oKk@&3Lu^x<A^D{ql#!I_uFWcK2OzY56j(IIY;VShMsd&~1y?nAqiv
Gpp9qdQ(0QW0e+Sq2Zk4A^KVmyZJmo$t9J0whzGB;M5*th?n-*2VVci8*RPcvZ>t1S5MCx1sSYdUi6+qfS3R(%xzOTp{_A7Jr1)g
>&4b$ZLM(=JP_hc`c$2JRl9pI1Q}8s&Xs%t!BXZE)wqM6|B4-LdV9M>JVj~5W9ZO)1(BX{#Kd_T*7U7r?w7KP%N4aev>vq5k0Tha
512~lHfQqOE#Akk6X-s|s{XW&JpmW)5`LU%{s5f!{b|bQ7k>s!Hbg)s(05pc*o#KQfth>LCex!TVsWaMVkvDn$C;*W`h8EVPnE`x
QtCA4;_%E4;q6tfnsWnA_4Ck-{UhL8L*{AjHPP71@8P9NTJ^rlqlG@g67vunqKmI~)q-u$cXL|3kb*>P28s326b=?m=jW0T(7pYV
E!UC=`>whWrLk~%XBB_{_{Mt*1@5<Ytji_;h3%svleUTsmjmo2KlC5^C_}WkqdO5}r<z5DlxmdKbMBsltT^Z{S4tUL5pA=5f!yN;
3UlcV<hMQhC&bU-!`0hIQS;c_N4p1ioG(VPT}$P#tD)YOopW(PofFd%%)1*qj)n(^_9;x2P;E!j_ML9iQ0f)x6VAEqcf<*6R)6;F
e*lhez~TOo$dlX4ee?0ap2I#w0bZgVv7)vjM!|)8m{y3ah>~qJA;sG{mcfQ9g`xVqOf7mBvePfew0*7x=CEJ$okM;eY^D1LU$FD%
v^=c2zW6g>a^jYe!BNJlvR3Ho^d;Kfw1#)H6Z2m-$5m9I46Z=%8qQ78(fi`M8|7>p0Vv0-!WGM(0EhSo#FrIZc$P&<ToZA#{OX6c
(lHeaTIihDPrPE+vZB_^am)cvJzQn*iXL;-xFSvXtqpWIUnf!qbfXdfkKYkTpPau2Xg&a^H(-C&jvRs^S&!X%dh8&llNu5$2EtYU
KvpQ*?v-3Z6XDQPH`)3!19Ze;R5(XBsRX(~gF`b^ENfdvY|NEc=dMa`5B!__Ikmih@CAFiDU<yRWkN>=v%Htd%5Fh9PPMElON9pl
p{bdewZ@AU^gObn`Jp-+-viO;NuvO^KZi%t<pjC`dsqDp=*LY%`V-<)tS+2i{24LH5c!xxNSh<#>8}(0H>y`w)B0E)HBS9E8*RY3
P>*$4(NIj=SS;(s0e9&wq!@ZxJi@Qb2D|kDQAzrui&XA&FMFNFY=RW8vjY40h)IT9KBhK9g)NpG4#S{mFAS`z2uBF#sIGZ^43*O@
sY+bs;Gm#zaPG4b|LX)=HsBcZ8xTEb+AtBz^73XI*N@8^ufKmO<(J#-wJ0Dy=5cgn5;`(S_ePN;EsyTSPBRDM2P#7~w7iBvn>C=s
f(7DH7mji0+6}un^M9R?%ifA9mp72BHSzo6C||K(eTaW=NJKt{Q@<D44~xU3Uvz9U*QQ)>z%%oj9vwC9Hsi!aRHYBh;TD2lPGv$=
aT{J2(8y~s*FoI|OmET;YWEZH9u|z@c~~$ZAHz-6i^)+sR7{!<_pe%^m~=G@q2UnsKx5RR$EQWjvA7rSsCt&OuFXXOO1DBZ^;DPL
K;FTwa6^2bi{F6j8*sSOWBuhS<1)Jzc*IUFL_dZjnA%&>f^Du%SJTSg97wC9tu{H(&sF73ST&*m-c<$kg6U`$A3aw`-G>L!8duW|
L`;jxQf+0$nRl$aZi(+wyl$8D>n)2cZn~Qk{|ue1h>{G{Ga(RjXn9u~hayQgVhyDZrH+hGZf@OK6$MNVDv-3&d{FYo&2NW2YtA5I
ZLIDFa(Q8Xzrr?OurvLC%GdqH1v8-}LoePdnm$D8RGE<4Vo^XY3Lu$*FY&t;9r;C}V49u~LK%y(HpKXy)=PO^Kv~!boP7d}qWv$9
c9p?>{esuN@uq8K(bxB$Uwb+Lp??!j_)?Oy;?9a90ol{8V!#b?D21--m0yP9w$rXnVu6L;X17FNmsbYuCa>dlAx1F>#glU5piulg
dQ$Hne1UGyLH})E`!w;NxME6Wk3-<9Ao7-4Q?W6TPuMwI@6EwwOLh2e)n!nciB07|*nVJPy53H}!QccIQTurVs@gS<I|pOj`}}<W
xc>Tpd*00Qjx+Aklgv-SkE>n!<6pk(|KFjg7P$rS#vMhxJ~JSeQG*lnpA3K1sow@&=2p>WA^X~Be|cSi_Zkr~tQQVF=wiRABh_D@
aPtySy-`v-zxXp)vLb3SN+G$WwhSjkM~!v`EejtzNnML1h%`+|>CjRciq~<JRyczkJ%q4cC&(T6kdrTOu=cZ<jE}zqoA=$swk~@F
OCCf?hFRy4&|W-HHS9{&8AU)v1Eq8T)A}$_i$7e7E6%BR4$jR`c<QecBozzosQa?&1WT(Dva;NC??88BbvM>iD5vgj5`r9eM31=z
Ihll<%y2V^AJ>>fEOPG#ce{xQl|F)H(4Y-#%22{Q#Ggkn%U2PrCE7Rk&FzVHKjMmU(}{z{<-*sxu>NwNVY^%VCOm83>{XW#kja?p
1(dVxSPEja1#@GfC^PcGv-8R?Q}ON4npP<VnO5!HUE2=DuL~qZl%eSO3GAn#K<|DJc8g8L^NT-&CG#O3Gm{Fv;$j=E#p3`~q7B0|
@0G)CQn{^tr0i`~csT{^F_+d#^$Oc=D+_Iq`!dI!bA5HY1SrXyU$pqCZ29tF{f*UbhQ}Le8}RK>p2t;8(%T9$6dV<+3nkW7(ET_V
pP%T09EaWv1C26UX6!TXV7;gngOXm~db1lXrJz!b^%ssGm0-C6e&A**&D~RJkE@rAhiFV2x%r0p(c!smjWf_<sB)XZ(1;r<^3Map
ha_3(vriFGjA)u-^Xo#%>UCUFyq__CW?wV(53rf}%G0amsUr@R7!Dp^zF1qT;{RB=DP1&$jfKNO4Wh}*h}4Tn=plMqPaDpz?wBfE
^c2x2eqA6pSh@~3oUkQ`O`#_}yNkr#Si_CghIGBL<3i@}^s$c*)dOnU*Wj$)Gb4Z#w2~W*3|bbwHa$e~x6S;cid6-?F-6r<ZllMc
Z&WAN*NK*{NbwK9uYNb`tfl$QqjTf?fE}*sTLgR`+g=cdLEq$+Y-b2W*(#ZR4j)nv!|lNxI!DaJ<RYeZOdK${iSYY|+fU4@c6Jlb
09SM+UJ2u;SfRV#KmYlU^W|StDop6Y&?NPmBEf!?jup9OBHXGHWoe{o6_vF-=RV75igL$N{lB=4NAbD4khgd*Aa}x0jcDT=toxkZ
t}XZttYa8JANBm=&tS=JXu_bHKQX#=8S`P+8Q<UD>DWN~F_2Vo39lT*3O!suaHisPD~G&&Wj07cuQ$=%Pq6A=w%^*Qe}Jv{Od$YW
-QzMKsi6l`;?bB{r);(X<4{lLMVh`~Ar!kv$ifpPsTkC{-aaELqgU`;biXc;gkEn;c9+|?o^1H!E9>ef%kp%BO?WM^X6yOIpTUyU
kb-e4g%$KIvz-dLMx1P^s7#Zor!FcntFo~QhAj3|kD_OMC{-(@9ZV<gCksdz8P>z;4K{Ph`=!C~2iPm%hQ9<{#9tEPFH|m7T+kp<
I?b>uj^h!^(dS`@J5+W0BiTctgQMhOrZ3pGh{WT3v3V~b_md6rBDU$ffZ`vX?7yU*n9zMm=)N3Q`)Q7&A=f6-(zMT(;)I^2{&GEG
FB;)WQaz#KbE;lZk=BYLu{g3n=>j0hWj^l4Mx^JVk40R%nppI-uMB)S*56oDy}sXf*5@VP<8mOS)jiZcmT1DEFp9+j&PSP5Cq6s!
^oi`{!%&XEgt*~ACQ3=jP&HA{BF<xc#H)zN8??R*@#}y^J)Jpj)cNMT`7fLojTeSSUgWT8#2vFWb)o^QC#zZrZe_E$%pBzq4-*+)
M^&`wHe#vPtoWHY<m&=S-G&>$`6xL_DO=F=^W|?nyW`G&oc#?070e%}r^$-UO%cXJFVlnSGTdQCv{TvjaLbRnTP|YhlM$e>#_Y+^
p`ifWGuoAuadB)Xqz!UE*-}fr!D=~tZeu9F1A8j8?b+(`1l9s}H?|Z-e6I?a!$3veu4Q{LFYTv+-;P7Uw1rq1JPeFbW^1ubF42y%
d6+<QV-th%A-utwX!a;9mJ6<a!dh>vA;s$rw^Q1-6f#e!-D_J%ytFu%C`xZNs*KQbH3eZr<L1;ZL=YR>imED&h%B1p=MvK_98IWt
<Az#j-9CW`Hklj8RyC+!8#wD3IBwW@Y{uI<Ha>y%fTduI1I@t&8^~dw%6k>+Vfo;bvDicOMq6AC821G2H{12BjmWte<*qIPNlGIv
+BevM#?80V=Ns7T(9%91T4q#SxD<R%>fIr>so0RI$i%UeITYT8$d>9d@q|U|M=EW>CnNgkYdI86*GU$3?&dWZSKeTip0U~CxbW+P
JsVo~ciG?X*xdqvT+Wl0TxLWbH(F&k1UE`Kl#CP%s&R%pU7FvZx4k1>+Ux8iIj1TJ(}gg4=Qv3Ga>rms?TNwR@=B{$^HBP1nI7*S
e1^`qoQs^IB99L`y|z`$i;2dW#j;T~i6OPH^my|q*q;;Z9QxONtvQt^Y>LJ7+)#9%ULpQm7146Or`LSrIwdqIb?K1w=jqu8Ui-#-
kqy1$wl`Mdvpt54{Mx-nFE^sHo8o42C?AS{1+9cgYj4!@Q9$VfrirGY3TVzN4qG@ac3J;sJCWxTxx%~qK&~kJqn5Y!D|CAv_MKWe
{t0jaFp{6EmRYr;l}L;CT?=3il{#yAtc+LC2byAOsw)DMzlY&o3CqiZ7tub52k2hY<*s?pwx{^Xo!;j^08V?RX%B;hC%_fJ+}siU
F-ur8amZ(4oO8@%RRm9!$4bfti5y>A3d4v~88eWl)E_8*?1T8g=-GbF(R={59I(DAd-(%kANPn*+F$(h*XzIk?|=V~|N8esq2Tpz
FEcHaOchx372#@+ajwM}PtgmX1bn;?r=4fApZLl+#<hd!u-Pq@umAm@|7-r&|NM{tbF}}MuYdc;KmXtV2ebUuAOrecords=709 u
nresolvable=0
"""


def node_id(node: dict) -> str:
    return node.get("node_id") or node.get("id") or ""


def metadata(node: dict) -> dict:
    value = node.get("metadata")
    if isinstance(value, str):
        value = json.loads(value)
    return value if isinstance(value, dict) else {}


def normalize_greek_base_letters(text: str) -> str:
    """Return the same accent/case-free beta base letters used for alignment."""
    out = []
    for char in unicodedata.normalize("NFD", text).lower():
        if unicodedata.combining(char):
            continue
        mapped = GREEK_TO_BETA.get(char)
        if mapped:
            out.append(mapped)
    return "".join(out)


def _empty_citation_state() -> dict[str, list[int | str]]:
    return {key: [0, ""] for key in "abcdnvwxyz"}


_LEVEL_BY_CASE = {0: "z", 1: "y", 2: "x", 3: "w", 4: "v", 5: "n"}


def _reset_lower_levels(state: dict, level: str) -> None:
    """Apply the hierarchical reset rules from the PHI/TLG ID format."""
    if level in "ab":
        lower = "nvwxyz"
        reset_value = 0
    elif level == "n":
        lower = "vwxyz"
        reset_value = 0
    elif level in "vwxyz":
        order = "vwxyz"
        lower = order[order.index(level) + 1 :]
        reset_value = 1
    else:
        return
    for item in lower:
        state[item] = [reset_value, ""]


def _ascii_payload(raw: bytes, start: int, end: int) -> str:
    return bytes(value & 0x7F for value in raw[start:end]).decode(
        "ascii", "strict"
    )


def apply_id_codes(raw: bytes, offset: int, state: dict) -> int:
    """Decode consecutive high-bit ID bytes and return the first text byte.

    The command nibble is implemented exactly as documented by the PHI/TLG
    format and by the citation state machine in ``tlgu``: commands 0--7 are an
    increment or small literal, 8--10 carry a 7-bit value, and 11--13 a 14-bit
    value.  Commands 9/10/12/13/14/15 also carry an ASCII suffix or string.
    """
    while offset < len(raw) and raw[offset] >= 0x80:
        lead = raw[offset]
        offset += 1
        if lead >= 0xF0:
            # F0 EOF, FE end-of-block and FF end-of-string have no payload
            # when seen at top level.  Zero block padding is consumed by the
            # caller as ordinary non-letter text.
            continue

        if lead >= 0xE0:
            command = lead & 0x0F
            level_byte = raw[offset] & 0x7F
            offset += 1
            if level_byte >= ord("a"):
                level = chr(level_byte)
            else:
                level = {0: "a", 1: "b", 2: "c", 4: "d"}.get(
                    level_byte & 7, "?"
                )
        else:
            command = lead & 0x0F
            level = _LEVEL_BY_CASE.get((lead >> 4) & 7, "?")

        value, suffix = state.get(level, [0, ""])
        if command == 0:
            if suffix:
                suffix = suffix[:-1] + chr(ord(suffix[-1]) + 1)
            else:
                value += 1
        elif 1 <= command <= 7:
            value, suffix = command, ""
        elif command == 8:
            value, suffix = raw[offset] & 0x7F, ""
            offset += 1
        elif command == 9:
            value = raw[offset] & 0x7F
            suffix = chr(raw[offset + 1] & 0x7F)
            offset += 2
        elif command == 10:
            value = raw[offset] & 0x7F
            offset += 1
            end = raw.index(0xFF, offset)
            suffix = _ascii_payload(raw, offset, end)
            offset = end + 1
        elif command in (11, 12, 13):
            value = ((raw[offset] & 0x7F) << 7) | (raw[offset + 1] & 0x7F)
            offset += 2
            if command == 11:
                suffix = ""
            elif command == 12:
                suffix = chr(raw[offset] & 0x7F)
                offset += 1
            else:
                end = raw.index(0xFF, offset)
                suffix = _ascii_payload(raw, offset, end)
                offset = end + 1
        elif command == 14:
            suffix = chr(raw[offset] & 0x7F)
            offset += 1
        elif command == 15:
            value = 0
            end = raw.index(0xFF, offset)
            suffix = _ascii_payload(raw, offset, end)
            offset = end + 1
        else:  # pragma: no cover - command is a nibble
            raise AssertionError(f"impossible ID command: {command}")

        if level in state:
            state[level] = [value, suffix]
            _reset_lower_levels(state, level)
    return offset


def parse_idt_schema_and_index(
    raw: bytes, block_count: int
) -> tuple[dict[int, str], list[tuple[int, int, int, int]], int]:
    """Read level names and the per-text-block citation index from the IDT."""
    marker = b"\x03\x00\x00\x08"
    index_start = raw.index(marker) + len(marker)
    descriptors: dict[int, str] = {}
    position = 0
    while position + 3 <= index_start:
        if raw[position] != 0x11:
            position += 1
            continue
        level = raw[position + 1]
        length = raw[position + 2]
        end = position + 3 + length
        if (
            end <= index_start
            and level <= 3
            and all(0x20 <= value < 0x7F for value in raw[position + 3 : end])
        ):
            descriptors[level] = raw[position + 3 : end].decode("ascii")
            position = end
        else:
            position += 1

    state = _empty_citation_state()
    states = []
    position = index_start
    for block in range(block_count):
        position = apply_id_codes(raw, position, state)
        states.append(tuple(int(state[item][0]) for item in "wxyz"))
        expected_terminator = 0x0A if block + 1 < block_count else 0x09
        actual = raw[position]
        if actual != expected_terminator:
            raise ValueError(
                f"IDT block {block}: terminator 0x{actual:02x}, "
                f"expected 0x{expected_terminator:02x}"
            )
        position += 1
    return descriptors, states, index_start


def parse_tlg_text(raw: bytes) -> dict:
    """Decode inline citations while creating a base-letter offset index."""
    state = _empty_citation_state()
    letters: list[str] = []
    offsets: list[int] = []
    citation_runs: list[tuple[int, tuple[int, int, int], int]] = []
    previous_citation = None
    position = 0
    while position < len(raw):
        if raw[position] >= 0x80:
            position = apply_id_codes(raw, position, state)
            continue
        value = raw[position]
        if 0x41 <= value <= 0x5A or 0x61 <= value <= 0x7A:
            citation = tuple(int(state[item][0]) for item in "wxy")
            if citation != previous_citation:
                citation_runs.append((len(letters), citation, position))
                previous_citation = citation
            letters.append(chr(value | 0x20))
            offsets.append(position)
        position += 1
    return {
        "normalized": "".join(letters),
        "offsets": offsets,
        "citation_runs": citation_runs,
    }


def validate_idt_txt_blocks(
    idt_states: list[tuple[int, int, int, int]], txt: bytes
) -> dict[str, int]:
    """Cross-check the IDT index against all redundant TXT block snapshots."""
    same_chapter_matches = 0
    chapter_rollover_matches = 0
    for block, idt_state in enumerate(idt_states):
        state = _empty_citation_state()
        apply_id_codes(txt, block * TLG_BLOCK_SIZE, state)
        txt_state = tuple(int(state[item][0]) for item in "wxyz")
        # Block zero begins at line 1.  Thereafter the index stores the line
        # immediately before the boundary and the TXT snapshot the first line
        # in the block, hence the mechanically observed +1 relation.  Seven
        # boundaries happen to be chapter openings: the IDT then records the
        # preceding chapter's last line while the TXT snapshot carries the new
        # chapter and line 1.
        same_chapter = txt_state[:3] == idt_state[:3] and (
            (block == 0 and txt_state[3] == idt_state[3])
            or (block > 0 and txt_state[3] == idt_state[3] + 1)
        )
        chapter_rollover = (
            txt_state[:2] == idt_state[:2]
            and txt_state[2] == idt_state[2] + 1
            and txt_state[3] == 1
        )
        if same_chapter:
            same_chapter_matches += 1
        elif chapter_rollover:
            chapter_rollover_matches += 1
    return {
        "block_count": len(idt_states),
        "same_chapter_matches": same_chapter_matches,
        "chapter_rollover_matches": chapter_rollover_matches,
        "boundary_matches": same_chapter_matches + chapter_rollover_matches,
    }


def _load_source_nodes(path: Path) -> list[dict]:
    nodes = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            node = json.loads(line)
            wanted_id = node_id(node)
            if not re.fullmatch(r"passage_plotinus_vi_9_\d+", wanted_id):
                continue
            meta = metadata(node)
            nodes.append(
                {
                    "node_id": wanted_id,
                    "source_fragment_index": meta.get("source_fragment_index"),
                    "description": node.get("description") or "",
                }
            )
    return sorted(nodes, key=lambda row: row["source_fragment_index"])


def _citation_for_norm_index(parsed: dict, index: int) -> tuple[int, int, int]:
    starts = [run[0] for run in parsed["citation_runs"]]
    run_index = bisect_right(starts, index) - 1
    if run_index < 0:
        return (0, 0, 0)
    return parsed["citation_runs"][run_index][1]


def _chapter_votes(
    parsed: dict, blocks: list[difflib.Match], local_start: int
) -> Counter:
    runs = parsed["citation_runs"]
    starts = [run[0] for run in runs]
    normalized_length = len(parsed["normalized"])
    votes: Counter = Counter()
    for block in blocks:
        start = local_start + block.b
        end = start + block.size
        run_index = bisect_right(starts, start) - 1
        position = start
        while position < end:
            next_run = (
                starts[run_index + 1]
                if run_index + 1 < len(starts)
                else normalized_length
            )
            count = min(end, next_run) - position
            votes[runs[run_index][1]] += count
            position += count
            run_index += 1
    return votes


def _new_values(citation: tuple[int, int, int]) -> tuple[str, str, str]:
    ennead, treatise, chapter = citation
    canonical_ref = f"Enn. {ROMAN[ennead]}.{treatise}.{chapter}"
    cts_urn = f"{TLG_WORK_URN}:{ennead}.{treatise}.{chapter}"
    label = f"Plotinus, Enneades, {canonical_ref}"
    return canonical_ref, cts_urn, label


def build_payload(nodes_path: Path, tlge_dir: Path) -> dict:
    """Rebuild all records from the live nodes and TLG E files."""
    nodes = _load_source_nodes(nodes_path)
    txt_path = tlge_dir / TLG_FILE
    idt_path = tlge_dir / IDT_FILE
    txt = txt_path.read_bytes()
    idt = idt_path.read_bytes()
    if len(nodes) != RECORD_COUNT:
        raise ValueError(f"found {len(nodes)} Plotinus nodes, expected {RECORD_COUNT}")
    if len(txt) // TLG_BLOCK_SIZE != TLG_BLOCK_COUNT:
        raise ValueError("unexpected TLG2000.TXT block count")

    descriptors, idt_states, index_start = parse_idt_schema_and_index(
        idt, TLG_BLOCK_COUNT
    )
    expected_descriptors = {
        3: "Ennead",
        2: "chapter",
        1: "section",
        0: "line",
    }
    if descriptors != expected_descriptors:
        raise ValueError(
            f"unexpected Plotinus citation descriptors: {descriptors!r}"
        )
    block_check = validate_idt_txt_blocks(idt_states, txt)
    if block_check["boundary_matches"] != TLG_BLOCK_COUNT:
        raise ValueError("IDT/TXT citation-state block mismatch")

    parsed = parse_tlg_text(txt)
    normalized = parsed["normalized"]
    offsets = parsed["offsets"]
    search_start = bisect_left(offsets, 700_000)
    search_end = len(normalized)
    anchor_cache: dict[str, int] = {}
    rows = []
    unresolved = []

    for node in nodes:
        wanted_id = node["node_id"]
        source_index = node["source_fragment_index"]
        description = node["description"]
        needle = normalize_greek_base_letters(description)
        anchors = []
        positions = list(range(0, max(1, len(needle) - 31), 16))
        positions.append(max(0, len(needle) - 32))
        for needle_position in sorted(set(positions)):
            chunk = needle[needle_position : needle_position + 32]
            if len(chunk) < 24:
                continue
            if chunk not in anchor_cache:
                first = normalized.find(chunk, search_start, search_end)
                second = (
                    normalized.find(chunk, first + 1, search_end)
                    if first >= 0
                    else -1
                )
                anchor_cache[chunk] = first if first >= 0 and second < 0 else -1
            if anchor_cache[chunk] >= 0:
                anchors.append((needle_position, anchor_cache[chunk]))

        if not anchors:
            unresolved.append(
                {
                    "node_id": wanted_id,
                    "source_fragment_index": source_index,
                    "reason": "no unique 24/32-base-letter anchor in TLG2000.TXT",
                }
            )
            continue

        delta = round(statistics.median(corpus - local for local, corpus in anchors))
        local_start = max(search_start, delta - 250)
        local_end = min(search_end, delta + len(needle) + 250)
        matcher = difflib.SequenceMatcher(
            None,
            needle,
            normalized[local_start:local_end],
            autojunk=False,
        )
        blocks = [block for block in matcher.get_matching_blocks() if block.size]
        matched_letters = sum(block.size for block in blocks)
        match_fraction = matched_letters / max(1, len(needle))
        if not blocks or match_fraction < 0.90:
            unresolved.append(
                {
                    "node_id": wanted_id,
                    "source_fragment_index": source_index,
                    "reason": (
                        "near-verbatim alignment below 0.90 exact-letter coverage "
                        f"({match_fraction:.6f})"
                    ),
                }
            )
            continue

        votes = _chapter_votes(parsed, blocks, local_start)
        ranked = votes.most_common()
        if not ranked or ranked[0][0] == (0, 0, 0):
            unresolved.append(
                {
                    "node_id": wanted_id,
                    "source_fragment_index": source_index,
                    "reason": "no Ennead/treatise/chapter state on exact alignment",
                }
            )
            continue
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            unresolved.append(
                {
                    "node_id": wanted_id,
                    "source_fragment_index": source_index,
                    "reason": f"exact chapter-vote tie: {ranked[:2]!r}",
                }
            )
            continue

        citation, dominant_count = ranked[0]
        first_block = blocks[0]
        last_block = blocks[-1]
        first_norm = local_start + first_block.b
        last_norm = local_start + last_block.b + last_block.size - 1
        start_byte = offsets[first_norm]
        end_byte = offsets[last_norm] + 1
        start_citation = _citation_for_norm_index(parsed, first_norm)
        end_citation = _citation_for_norm_index(parsed, last_norm)
        description_sha256 = hashlib.sha256(description.encode("utf-8")).hexdigest()
        flattened_votes = []
        for vote_citation, count in sorted(votes.items()):
            flattened_votes.extend([*vote_citation, count])
        rows.append(
            [
                wanted_id,
                source_index,
                description_sha256,
                start_byte,
                end_byte,
                *citation,
                round(match_fraction * 1_000_000),
                round(dominant_count / matched_letters * 1_000_000),
                len(anchors),
                *start_citation,
                *end_citation,
                flattened_votes,
                len(needle),
                matched_letters,
            ]
        )

    by_index = {row[1]: row for row in rows}
    contradictions = []
    fixed_expectations = {
        1: lambda row: row[5] == 4,
        50: lambda row: row[5] == 4,
        136: lambda row: tuple(row[5:8]) == (5, 1, 9),
    }
    for index, predicate in fixed_expectations.items():
        row = by_index.get(index)
        if row is None or not predicate(row):
            contradictions.append(f"fixed point {index}: {row[5:8] if row else 'missing'}")
    bad_305_plus = [row[1] for row in rows if row[1] >= 305 and row[5] != 6]
    if bad_305_plus:
        contradictions.append(f"nodes 305+ outside Ennead VI: {bad_305_plus}")
    if contradictions:
        raise RuntimeError("STOP — fixed-point contradiction: " + "; ".join(contradictions))

    discontinuities = []
    for left, right in zip(rows, rows[1:], strict=False):
        # The requirement applies within each contiguous Ennead run.  Check
        # both halves of the half-open byte envelope.
        if left[5] == right[5] and (left[3] >= right[3] or left[4] >= right[4]):
            discontinuities.append(
                {
                    "left_node_id": left[0],
                    "right_node_id": right[0],
                    "left_anchor": {"start": left[3], "end": left[4]},
                    "right_anchor": {"start": right[3], "end": right[4]},
                }
            )

    ennead_runs = []
    run_start = 0
    for position in range(1, len(rows) + 1):
        if position == len(rows) or rows[position][5] != rows[run_start][5]:
            ennead_runs.append(
                {
                    "ennead": rows[run_start][5],
                    "first_source_fragment_index": rows[run_start][1],
                    "last_source_fragment_index": rows[position - 1][1],
                    "count": position - run_start,
                }
            )
            run_start = position

    return {
        "rows": rows,
        "unresolvable": unresolved,
        "idt": {
            "size_bytes": len(idt),
            "index_start_byte": index_start,
            "descriptors": {str(key): value for key, value in descriptors.items()},
            **block_check,
        },
        "ennead_runs": ennead_runs,
        "offset_discontinuities": discontinuities,
        "txt_sha256": hashlib.sha256(txt).hexdigest(),
        "idt_sha256": hashlib.sha256(idt).hexdigest(),
    }


def _payload_bytes(payload: dict) -> bytes:
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _decode_payload() -> dict:
    if "__PLOTINUS_PAYLOAD__" in _PAYLOAD_B85:
        return {
            "rows": [],
            "unresolvable": [],
            "idt": {},
            "ennead_runs": [],
            "offset_discontinuities": [],
        }
    compressed = base64.b85decode("".join(_PAYLOAD_B85.split()))
    blob = zlib.decompress(compressed)
    if hashlib.sha256(blob).hexdigest() != _PAYLOAD_SHA256:
        raise RuntimeError("Plotinus remap payload checksum mismatch")
    return json.loads(blob.decode("utf-8"))


def _inflate_records(rows: list[list]) -> tuple[dict, ...]:
    records = []
    for position, row in enumerate(rows):
        (
            wanted_id,
            source_index,
            description_sha256,
            start_byte,
            end_byte,
            ennead,
            treatise,
            chapter,
            match_ppm,
            dominant_ppm,
            unique_anchor_count,
            start_ennead,
            start_treatise,
            start_chapter,
            end_ennead,
            end_treatise,
            end_chapter,
            flattened_votes,
            normalized_length,
            matched_letters,
        ) = row
        canonical_ref, cts_urn, label = _new_values((ennead, treatise, chapter))
        chapter_votes = []
        for vote_position in range(0, len(flattened_votes), 4):
            vote_ennead, vote_treatise, vote_chapter, count = flattened_votes[
                vote_position : vote_position + 4
            ]
            chapter_votes.append(
                {
                    "citation": f"{vote_ennead}.{vote_treatise}.{vote_chapter}",
                    "exact_aligned_letters": count,
                }
            )
        previous = rows[position - 1] if position else None
        following = rows[position + 1] if position + 1 < len(rows) else None
        records.append(
            {
                "node_id": wanted_id,
                "source_fragment_index": source_index,
                "byte_anchor": {"start": start_byte, "end": end_byte},
                "derived_citation": {
                    "ennead": ennead,
                    "treatise": treatise,
                    "chapter": chapter,
                    "reference_precision": REFERENCE_PRECISION,
                    "selection_method": CITATION_SELECTION_METHOD,
                    "dominant_exact_letter_fraction": dominant_ppm / 1_000_000,
                    "citation_span_start": (
                        f"{start_ennead}.{start_treatise}.{start_chapter}"
                    ),
                    "citation_span_end": f"{end_ennead}.{end_treatise}.{end_chapter}",
                    "chapter_votes": chapter_votes,
                },
                "new_canonical_ref": canonical_ref,
                "new_cts_urn": cts_urn,
                "new_label": label,
                "evidence": {
                    "text_source": TEXT_SOURCE,
                    "alignment_method": ALIGNMENT_METHOD,
                    "description_sha256": description_sha256,
                    "normalized_base_letter_length": normalized_length,
                    "exact_aligned_letters": matched_letters,
                    "exact_base_letter_match_fraction": match_ppm / 1_000_000,
                    "unique_32_letter_anchor_count": unique_anchor_count,
                    "anchor_semantics": "half-open envelope of exact matched letters",
                    "previous_node_id": previous[0] if previous else None,
                    "previous_start_byte": previous[3] if previous else None,
                    "previous_end_byte": previous[4] if previous else None,
                    "next_node_id": following[0] if following else None,
                    "next_start_byte": following[3] if following else None,
                    "next_end_byte": following[4] if following else None,
                },
            }
        )
    return tuple(records)


_PAYLOAD = _decode_payload()
PLOTINUS_REMAP_RECORDS = _inflate_records(_PAYLOAD["rows"])
UNRESOLVABLE_RECORDS = tuple(_PAYLOAD["unresolvable"])
IDT_VALIDATION = _PAYLOAD["idt"]
ENNEAD_RUNS = tuple(_PAYLOAD["ennead_runs"])
OFFSET_DISCONTINUITIES = tuple(_PAYLOAD["offset_discontinuities"])


def check_payload() -> None:
    assert len(PLOTINUS_REMAP_RECORDS) + len(UNRESOLVABLE_RECORDS) == RECORD_COUNT
    assert len({row["node_id"] for row in PLOTINUS_REMAP_RECORDS}) == len(
        PLOTINUS_REMAP_RECORDS
    )
    assert not OFFSET_DISCONTINUITIES
    assert IDT_VALIDATION["block_count"] == TLG_BLOCK_COUNT
    assert IDT_VALIDATION["boundary_matches"] == TLG_BLOCK_COUNT
    by_index = {row["source_fragment_index"]: row for row in PLOTINUS_REMAP_RECORDS}
    assert by_index[1]["derived_citation"]["ennead"] == 4
    assert by_index[50]["derived_citation"]["ennead"] == 4
    assert by_index[136]["new_canonical_ref"] == "Enn. V.1.9"
    assert all(
        row["derived_citation"]["ennead"] == 6
        for row in PLOTINUS_REMAP_RECORDS
        if row["source_fragment_index"] >= 305
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--tlge-dir", type=Path, default=DEFAULT_TLGE)
    parser.add_argument("--verify-source", action="store_true")
    parser.add_argument("--emit-payload", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.emit_payload:
        rebuilt = build_payload(args.nodes, args.tlge_dir.expanduser())
        blob = _payload_bytes(rebuilt)
        print(hashlib.sha256(blob).hexdigest())
        print(base64.b85encode(zlib.compress(blob, 9)).decode("ascii"))
        print(
            f"records={len(rebuilt['rows'])} "
            f"unresolvable={len(rebuilt['unresolvable'])}",
            file=sys.stderr,
        )
        return 0

    check_payload()
    print(f"records: {len(PLOTINUS_REMAP_RECORDS)}")
    print(f"unresolvable: {len(UNRESOLVABLE_RECORDS)}")
    print(
        "IDT/TXT blocks: "
        f"{IDT_VALIDATION['boundary_matches']}/{IDT_VALIDATION['block_count']} "
        "citation-state matches"
    )
    print(f"offset discontinuities: {len(OFFSET_DISCONTINUITIES)}")
    print(
        "Ennead coverage: "
        + ", ".join(
            f"{ROMAN[run['ennead']]}={run['count']}"
            for run in ENNEAD_RUNS
        )
    )
    if args.verify_source:
        rebuilt = build_payload(args.nodes, args.tlge_dir.expanduser())
        embedded = _payload_bytes(_PAYLOAD)
        live = _payload_bytes(rebuilt)
        if live != embedded:
            print("source verification: FAILED (payload differs)", file=sys.stderr)
            return 1
        print("source verification: OK (709/709 records reproduced byte-for-byte)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
