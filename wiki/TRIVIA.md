# Facts and anecdotes

Short, sourced facts about the Gamma 60. Source keys are defined in
[REFERENCES.md](REFERENCES.md) and [`docs/SOURCES.md`](../docs/SOURCES.md); details in
[`docs/HISTORY.md`](../docs/HISTORY.md), [`docs/HARDWARE.md`](../docs/HARDWARE.md) and
[`docs/MACHINE.md`](../docs/MACHINE.md), which prevail.

## Birth and name

- The project was first called **"Gamma 4"** internally, then renamed **"Gamma 60"**: "60"
  for the target availability year, 1960, according to a company history. *(NAM ;
  encyclopedia.com)*
- The French word **"ordinateur"** was proposed by J. Perret to IBM France on 16 April 1955,
  the year the Gamma 60 studies began. *(Perret letter ; FEB)*
- Philippe Dreyfus, one of its designers, presented the machine in the United States as early
  as 1958, at the Western (May) and Eastern (December) Joint Computer Conferences. He is also
  credited with the French word **"informatique"** (1962). *(DR-W ; DR-E ; Wikipedia)*

## An architecture ahead of its time

- Its instruction set already had **fork and join** (`SIMU`, join cuts); the names FORK and
  JOIN were introduced by Conway in 1963. *(COURS ; CONW ; BAT72)*
- Its **virtual elements** (`PROT` / `LIBE`) are hardware locks with a FIFO wait queue, a
  decade before Dijkstra's paper on semaphores (1968). Dijkstra even leaves undefined which
  waiting process is released; the Gamma 60 is strictly first come, first served.
  *(COURS p.27-31 ; DIJ68 p.345)*
- The wait queues are **stored inside the program itself**: each cut is followed by a blank
  catena that the Program Distributor fills in at run time. Programs modify themselves while
  they run, and queues are unbounded without any reserved memory: the process "can go on
  indefinitely at low cost". *(COURS p.24-31 ; B61 p.24-25)*
- A blank catena executed by mistake does nothing: its zero leftmost bits are the code of a
  "never" branch. *(COURS p.42)*, i.e. NOOP
- The central unit **never computes**: it only hands out work. Even the arithmetic and logic
  calculators are "elements", like the printers. *(B61 p.20-24 ; ONDE)*

## Hardware

- A 32K-word core memory measured about 3.2 × 2.2 × 0.8 m and drew 7.5 kVA; a complete
  installation could cover about 370 m². *(FEB ; ONDE)*
- Germanium transistors (Philips) and diodes, about 3,600 sections of 4 amplifiers; a few
  vacuum tubes remained, in the central unit only. *(B61 p.4-5 ; NAM)*
- The magnetic drum, taken over from earlier Bull machines, spun at 2,975 rpm with 128 heads.
  *(ONDE)*
- The wiring documentation was kept **on punched cards**. *(ONDE)*
- The console allowed step-by-step execution (by cycle or by instruction) and a stop on a
  displayed address: a hardware debugger. *(ONDE ; MAI)*

## Customers and career

- 16 machines are listed, for customers such as the SNCF, EDF, the Belgian RTT, two Italian
  banks and Mitsubishi. See [INSTALLATIONS.md](INSTALLATIONS.md). *(calendar, probably AVG)*
- At the SNCF, the computer room was at the **Gare d'Auteuil** in Paris; payroll ran on it from
  15 April 1961. *(FEB)*
- In Belgium, *La Meuse* (6 July 1961) called it "the most powerful electronic installation in
  Belgium". It billed about 600,000 telephone subscribers, and the paper stressed, in capitals,
  that all these operations could be done "SIMULTANÉMENT". *(La Meuse)*
- The RTT kept its two machines until **1974**, the last ones in service; *Honeywell Bull
  Contact* said farewell in February 1975 with "GAMMA 60 GOOD BYE". *(RTT ; HBC75)*
- Lifetimes varied widely: the GMF used its machine from 1962 to 1973, while the CEA and
  Printemps returned theirs after two or three years. *(calendar)*

## Legacy

- In Jean-Luc Godard's film ***Alphaville*** (1965), the computer **Alpha 60** is modelled on
  the Gamma 60. *(A. Utterson)*
- In 1971, M. Bataille, a co-author of the 1960 *L'Onde électrique* article, already called it
  "the computer that was ahead of its time". *(BAT72)*
- In 2018 the NAM-IP published a period sort program written in code B; it is now one of this
  emulator's test programs. *(NAM)*
