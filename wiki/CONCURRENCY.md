# Concurrency in the Bull Gamma 60

The Gamma 60 was designed around one idea: several pieces of work should progress **at the same time**, each on a different specialised element, while a single control unit hands out the work. This page explains how that works, and how the machine already had the ancestors of three ideas that became standard later: **fork/join**, **wait queues** and **locks**.

See also [ARCHITECTURE.md](ARCHITECTURE.md) (elements, classes) and [MEMORY.md](MEMORY.md) (catenae, words).

Sources: Bull, *Gamma 60 Data Processing System* (1961, "B61") p.20-31; Bull, *Cours de programmation Gamma 60* (~1958-59, "COURS") p.24-38, p.52; *L'Onde électrique* (1960, "ONDE"); for comparison, Dijkstra, *CACM* 11(5), 1968 ("DIJ68"). Reference: [`docs/MACHINE.md`](../docs/MACHINE.md) §7. Points that are our own deductions are marked as such.

Mnemonics are given as `en` / `fr` (the two languages of code B) when they differ; `PROT`, `LIBE`, `SIMU`, `STOP`, `ARIT`, `COMP` are the same in both.

---

## 1. The machine in one paragraph

The Gamma 60 has **autonomous elements**: an arithmetic element (ARIT), a logical element (LOGI), a comparator (COMP), a transcoder (TRAN / TRAD), magnetic drums (DRUM / TAMB), tape uniselectors (MATA / DERU), card readers, printers… They never talk to each other directly. They all meet in the **central memory**, and they are coordinated by one **Program Distributor** (DP, from the French *Distributeur de Programme*). [B61 p.20-24]

An element works like this:

1. it raises an **instruction request**;
2. the Program Distributor serves it: it reads the program's instructions (address loads, branches, central operations) until it reaches a **directive**, the order meant for that element, and sends it;
3. the element then works **on its own**, fetching and storing its data word by word through the memory arbiter;
4. when it is done, it raises a new instruction request.

While an element works on its own, **the Program Distributor is free** to serve other elements. That is where simultaneity comes from.

## 2. Vocabulary: from instruction to thread

| Level | What it is | Elements involved |
|---|---|---|
| Canonical instruction | one machine word (one "catena") | — |
| Complete instruction | the instructions up to and including one directive | one element |
| **Elementary sequence** | from a **cut** to the next cut | **exactly one element** |
| **Thread** (program flow) | a chain of elementary sequences | several elements, **one after the other** |

A **cut** is the instruction that names the element that will execute what follows, for example `ARIT`. It marks the boundary between two sequences. When a thread reaches a cut naming another element, its current sequence ends and the thread **moves on** to that element.

> **Key point.** Inside one sequence, and inside one thread, everything is strictly sequential. **Concurrency appears only when there are several threads**, each one occupying a different element at a given moment.

## 3. Two sources of concurrency, one mechanism

**Within one program.** The programmer can split a program into several threads with the `SIMU` instruction (see §4).

**Across programs (multiprogramming).** Several independent programs run at once: one sorts on the comparator, another reads a tape, a third prints.

```
time →           0 ms           5 ms           10 ms
Program A :  [COMP: sort ........][ARIT: totals]
Program B :  [Tape: read one block ........................]
Program C :  [Printer: one line ...........................]
```

For the Program Distributor there is **no difference**: it only sees elements asking for instructions. Branches of one program and independent programs are served in exactly the same way.

## 4. Fork and join, years before the words existed

| Gamma 60 | Today | How it works |
|---|---|---|
| `SIMU x` | **fork** | starts the branch at line `x` **and** the instructions that follow, as two threads |
| A **join cut**, e.g. `COMP 1` | **join** | a cut with a count of *additional* conditions (1, 2 or 3): the cut takes effect only when 2, 3 or 4 branches have reached it; the earlier arrivals simply end there [B61 p.31] |
| `STOP` | thread exit | ends the sequence and the thread |

Programmers could thus write a flowchart "in its natural shape, a network" (B61). Where the count *m* is written depends on the machine profile: B61 puts it in the C.C. field of the cut (as in the examples below), COURS in the X field of the following blank catena (COURS p.52).

The terms *fork* and *join* were formalised by M. Conway in 1963 (CONW); the Gamma 60 already had the same constructs in its instruction set by 1958-59 (COURS).

**One detail.** According to COURS, `SIMU` starts the **named** branch first, and keeps the continuation in the Program Distributor's own waiting chain until it can serve it (COURS p.36-38).

### Example: read the next block while processing the current one

Without concurrency, a program reads a block, processes it, reads the next block, processes it… The tape and the arithmetic element take turns. With `SIMU`, they overlap:

```
Line T.O.  C.C.  X     A.F.  Comment
000  SIMU        008   R     fork: processing branch (008) + reading branch (002)
001  (blank)
002  MATA  1                 reading branch: tape uniselector 1 (fr: DERU)
003  (blank)
004  REF         3           prepare: read forward on tape unit 3
005  L     0     100   R     address register 0 ← BUFFER-2 (fr: G)
006  TRA                     read one block into BUFFER-2 (≈ 50 ms)
007  31          012   R     always go to the join
008  ARIT                    processing branch
009  (blank)
010  …   ADD, MUL… on BUFFER-1
011  31          012   R     always go to the join
012  COMP  1                 join: waits for both branches (1 additional condition)
013  (blank)
014  …                       continue: swap buffers, loop
```

`R` means "relative line number": the program can be loaded anywhere in memory. `REF` and `TRA` (tape read) are B61 mnemonics; their `fr` forms are not recorded in our sources (U-29).

```
time →
Reading branch    : [Tape: read block n+1 into BUFFER-2 ......................]─┐
Processing branch : [ARIT: process block n in BUFFER-1 ......]  (done)          ├─► join → next loop
                                                                                ┘
```

The total time is the time of the **longer** branch, not the sum of the two.

## 5. Waiting: the ancestor of semaphores

An element can serve only one sequence at a time. Waiting therefore happens in two situations.

### 5.1 Physical blocking: the element is busy

If a thread reaches the cut `ARIT` while ARIT is working for another thread, the thread does not spin and is not refused: its sequence is placed in ARIT's **recall chain**, a **FIFO** queue. When ARIT finishes its current sequence, it takes the first waiting one, and so on until the queue is empty. This avoids blocking the Program Distributor, and it also avoids deadlocks (B61 p.24-25; COURS p.24-31).

Each element has a "busy" bit (stored next to its instruction address register) and two registers for its queue: the **head** (first waiting sequence) and the **tail** (last one).

### 5.2 Logical blocking: virtual elements (`PROT` / `LIBE`)

Sometimes the conflict is not about an element but about **something shared**: a work area in memory, or a subroutine that cannot be run by two threads at once. The Gamma 60 handles it with a **virtual element**: a "fake element" that exists only in memory, two words long:

| Word | Contents |
|---|---|
| X (image 1) | bit 24 = busy flag; bits 1-15 = head of the waiting queue |
| X+1 (image 2) | tail of the waiting queue |

- `PROT X` (protect): if the virtual element is free, mark it busy and continue; otherwise, join its FIFO queue and wait.
- `LIBE X` (liberate): if someone is waiting, hand it over to the first one, who resumes; otherwise, mark it free.

Today we would call it a **lock (mutex) with a FIFO wait queue**, built into the instruction set and managed by the hardware control unit, a decade before Dijkstra published his **semaphores** (P/V operations on a shared variable with a waiting list, 1968, DIJ68 p.345). One difference: Dijkstra leaves undefined which waiting process is released; the Gamma 60 queue is strictly FIFO. It is **advisory**: it protects a stretch of program, not memory addresses. It works only if every thread that touches the shared resource goes through the same `PROT`.

### Example: three threads reading drum records into one shared buffer

Three branches each read a record from the drum into the same buffer `ZONE`, then add it to a `TOTAL`. Without a lock, one branch's drum transfer could overwrite `ZONE` while another branch is about to add it. The lock makes the pair "drum read + addition" indivisible.

```
Line T.O.  C.C.  X      A.F.  Comment
000  SIMU        020    R     start branch B
001  (blank)
002  SIMU        040    R     start branch C
003  (blank)
004  PROT        100    R     ── branch A ── take the lock (images at lines 100-101)
005  (blank)                  ← A's link if it has to wait
006  DRUM  1                  drum: record A → ZONE (fr: TAMB)
 …   (L, DAO 17400, TDC 2)
011  ARIT                     ARIT: TOTAL ← TOTAL + ZONE
 …   (L ×3, ADD)
017  LIBE        100    R     release the lock
018  (blank)
019  31          060    R     go to the join
020  PROT        100    R     ── branch B ── same body, record at 17600
021  (blank)                  ← B's link
 …
040  PROT        100    R     ── branch C ── same body, record at 17800
041  (blank)                  ← C's link
 …
060  COMP  2                  join: waits for 3 branches (2 additional conditions)
061  (blank)                  ← join counter
100-101  lock images (initialised to 0) · 102 ZONE · 104 TOTAL
```

Because `SIMU` starts the named branch first, the threads reach the lock in the order **B, C, A**. With the program loaded at address 2000 (line *n* = address 2000 + *n*), the lock and its queue evolve as follows:

| Step | 2100 (image 1) | 2101 (image 2) | 2041 (C's blank) | 2005 (A's blank) | 2061 (join) |
|---|---|---|---|---|---|
| Start | free, head 0 | 0 | 0 | 0 | 0 |
| B: `PROT` | **busy**, head 0 | 0 | | | |
| C: `PROT` (busy → wait) | busy, head **2041** | **2041** | next **0** | | |
| A: `PROT` (busy → wait) | busy, head 2041 | **2005** | next **2005** | next **0** | |
| B: `LIBE` → C resumes | busy (C), head **2005** | 2005 | (used) | | |
| B: join | | | | | **1** |
| C: `LIBE` → A resumes | busy (A), head **0** | 2005 (unchanged) | | (used) | |
| C: join | | | | | **2** |
| A: `LIBE` | **free**, head 0 | 0 | | | |
| A: join → COMP starts | | | | | **0** (reset) |

The queue reaches two entries (C then A) and is served **first come, first served**.

> **Lesson.** Here the lock covers the whole read-and-add, so the three branches run one after the other: the program is correct, but not faster. Giving each branch its own buffer, and locking only the update of `TOTAL`, would let one branch add while the next one reads. Keep critical sections short, on the Gamma 60 as today.

## 6. The blank catena: working slots provided by the code

Did you notice the `(blank)` lines? After **every cut** (on a real element, `PROT`, `LIBE`, `SIMU`, join), the programmer must leave one **blank catena**: a word set to zero. It is not an instruction: it is a **working slot reserved inside the code**, which the Program Distributor writes into at run time to hold the dynamic information of the queues and joins.

| Role | When | What is written into it |
|---|---|---|
| **1. Link of a real element's waiting queue** | the cut names an element that is busy | bits 1-15: address of the next waiting sequence's blank (0 = end of queue) |
| **2. Link of a lock's waiting queue** | `PROT` finds the lock busy | same |
| **3. Join counter** | a join cut (`COMP 2`…) | bits 19-18: number of arrivals already counted (0 to 3) |
| **4. Link of the Program Distributor's own chain** | `SIMU` (placed on the ordinary branch) | link to the continuation kept aside |

Three properties make this design work:

- **The blank's address identifies the waiting sequence twice over**: it is the queue link, and it is the restart point (the sequence resumes just after its blank).
- **A queue never runs out of space**: every waiting sequence brings its own link. B61 notes that each new sequence brings a new temporary storage register, so the process can go on indefinitely at low cost. Adding or removing an entry touches only two or three words.
- **A blank is harmless when executed**: its leftmost bits are zero, which is the code of a "never" branch, so the Program Distributor simply moves on.

And three consequences follow:

- every blank must be **zero** before use;
- the program code is **modified while it runs**, so the same code cannot safely be run by two threads passing the same cut at the same moment. This is our deduction, and it is one more reason why shared subroutines are protected by a virtual element;
- address 0 cannot hold a blank, since 0 marks the end of a queue.

## 7. Summary

| Concept | Gamma 60 (1958) | Modern equivalent |
|---|---|---|
| Unit of work on one element | elementary sequence (cut → next cut) | task step |
| Several flows at once | several threads: `SIMU` or several programs | threads, processes |
| Start two flows | `SIMU` | fork |
| Wait for several flows | join cut with a count | join, barrier |
| Busy element | FIFO recall chain | wait queue |
| Shared resource | virtual element, `PROT` / `LIBE` | mutex, binary semaphore |
| Queue storage | linked list through the blank catenae of the waiting code | linked list of thread control blocks |

The Program Distributor is the conductor: it never computes on data, it only hands out work, keeps the queues, and lets every element work on its own for as long as possible.
