"""Data Distributor (J2): one catena per cycle, priorities, gates, CARs, incidents.

Acceptance criteria of docs/ROADMAP.md (J2), tested with synthetic elements.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from gamma60 import data, debug
from gamma60.__main__ import main
from gamma60.catena import Catena
from gamma60.data_distributor import PD, READ, WRITE, DataDistributor
from gamma60.engine import Engine
from gamma60.memory import Memory
from gamma60.registers import RacMatrix
from gamma60.synthetic import build, load_scenario

SCENARIOS = Path(__file__).parent / "scenarios"


def client(name, kind, **kw):
    return {"name": name, "kind": kind, **kw}


def run(clients, profile="B61", **spec):
    s = build({"clients": clients, **spec}, profile)
    s.run()
    return s


# --- 1. determinism ----------------------------------------------------------------------------


@pytest.mark.parametrize("profile", ["B61", "COURS"])
def test_same_input_same_trace(profile):
    def once():
        s = load_scenario(SCENARIOS / "drum_arit.yaml", profile)
        out = io.StringIO()
        s.engine.listeners.append(debug.DDTrace(debug.Names("fr"), out))
        s.run()
        return s.engine.trace, out.getvalue()

    assert once() == once()


# --- 2. throughput: one catena per cycle -------------------------------------------------------


@pytest.mark.parametrize(("profile", "cycle"), [("B61", 10), ("COURS", 11)])
def test_one_catena_per_cycle(profile, cycle):
    s = run([client("ARIT", "arithmetic", count=100, address=100)], profile)
    times = [r.time for r in s.engine.trace if r.what == "transfer"]
    assert len(times) == 100
    assert times == [k * cycle for k in range(100)]  # 100 catenae in 100 cycles
    assert s.clients[0].done[-1][0] == 100 * cycle  # last buffer filled at the end of its cycle


# --- 3. and 4. drum and tape occupancy [B61 p.23-24] --------------------------------------------


def test_drum_uses_one_cycle_in_ten():
    s = run(
        [client("DRUM", "drum", pattern="periodic", period_us=100, count=50, direction=WRITE)],
        until_us=5000,
    )
    assert s.dd.occupancy(5000) == pytest.approx(0.10)
    assert s.clients[0].misses == 0


@pytest.mark.parametrize(("profile", "period"), [("B61", 190), ("COURS", 266)])
def test_tape_uses_about_five_percent(profile, period):
    duration = 200 * period
    s = run(
        [client("MATA", "uniselector", pattern="periodic", period_us=period, count=200)],
        profile,
        until_us=duration,
    )
    assert 0.035 <= s.dd.occupancy(duration) <= 0.06  # « 5 % » [B61 p.24]


# --- 5. and 6. priorities -------------------------------------------------------------------------


DRUM_AND_ARIT = [
    client("DRUM", "drum", pattern="periodic", period_us=100, count=10, direction=WRITE),
    client("ARIT", "arithmetic", count=200),
]


def test_drum_before_arit():
    s = run(DRUM_AND_ARIT, until_us=1000)
    assert s.dd.stats.wait_max["DRUM"] <= s.dd.cycle and s.clients[0].misses == 0


def test_reversed_order_makes_the_drum_miss():
    s = run(DRUM_AND_ARIT, until_us=1100, dtd_order=["arithmetic", "drum"])
    assert s.clients[0].misses == 10  # the drum loses its positions [B61 p.24]


def test_quantity_before_instruction_and_pd_rank():
    s = load_scenario(SCENARIOS / "quantity_first.yaml")
    s.run()
    order = [r.get("element") for r in s.engine.trace if r.what == "transfer"]
    assert order == ["ARIT"] * 5 + ["PD"] * 5 + ["LOGI"] * 5


def test_pd_feeding_a_card_reader_passes_before_comp():
    # COURS p.6: the PD passes before COMP when it feeds a card reader (rank of the served element)
    s = run(
        [
            client("COMP", "comparator", count=3),
            client("PD", PD, nature="instruction", rank_as="card_reader", count=3, address=50),
        ]
    )
    order = [r.get("element") for r in s.engine.trace if r.what == "transfer"]
    assert order[:3] == ["PD"] * 3


def test_tie_break_is_configuration_order():
    s = run([client("D1", "drum", count=3), client("D2", "drum", count=3)])
    order = [r.get("element") for r in s.engine.trace if r.what == "transfer"]
    assert order == ["D1"] * 3 + ["D2"] * 3


# --- 7. CARs --------------------------------------------------------------------------------------


@pytest.mark.parametrize("step", [1, -1])
def test_car_gives_consecutive_addresses(step):
    s = run([client("MATA", "uniselector", count=5, direction=WRITE, address=3000, step=step)])
    addresses = [r.get("address") for r in s.engine.trace if r.what == "transfer"]
    assert addresses == [3000 + step * k for k in range(5)]
    assert s.dd.racs.get("MATA", 0) == 3000 + 5 * step
    assert [s.memory.read(a) for a in addresses] == [1, 2, 3, 4, 5]


def test_read_fills_the_buffer_register():
    s = build({"clients": [client("ARIT", "arithmetic", count=2, address=10)]})
    s.memory.write(10, 0x123456)
    s.memory.write(11, 0x654321)
    s.run()
    assert [v for _, v in s.clients[0].done] == [0x123456, 0x654321]
    assert s.dd.ports["ARIT"].buffer == 0x654321


# --- 8. gates, channels, multiplexer ----------------------------------------------------------------


def test_each_transfer_uses_the_gate_of_its_class():
    s = run(
        [
            client("LOGI", "logical", count=1),
            client("ARIT", "arithmetic", count=1),
            client("D1", "drum", count=1, direction=WRITE),
            client("D2", "drum", count=1, direction=WRITE),
            client("PRIN", "printer", count=1),
        ]
    )
    gates = {r.get("element"): (r.get("gate"), r.get("channel")) for r in s.engine.trace}
    assert gates == {
        "LOGI": ("c0", "DDC"),  # LOGI in class 0 (U-09)
        "ARIT": ("c1", "DDC"),
        "D1": ("c2a", "DCC"),  # two circuits for class 2, used alternately (U-32)
        "D2": ("c2b", "DCC"),
        "PRIN": ("c34", "DDC"),
    }


def test_multiplexer_serves_in_turn():
    s = load_scenario(SCENARIOS / "multiplexer.yaml")
    s.run()
    order = [r.get("element") for r in s.engine.trace if r.what == "transfer"][:6]
    assert order == ["CARR", "PRIN", "TAPR"] * 2  # round robin behind gate c34 (U-43)


@pytest.mark.parametrize("same_cycle", [False, True])
def test_ddc_and_dcc_in_the_same_cycle_is_a_setting(same_cycle):
    s = run(
        [client("ARIT", "arithmetic", count=4), client("D1", "drum", count=4, direction=WRITE)],
        behavior={"dd_channels_same_cycle": same_cycle},
    )
    times = [r.time for r in s.engine.trace if r.what == "transfer"]
    if same_cycle:
        assert times == [0, 0, 10, 10, 20, 20, 30, 30]  # one DDC and one DCC per cycle
    else:
        assert times == [k * 10 for k in range(8)]  # U-40 default: one transfer per cycle


def test_request_raised_mid_cycle_waits_for_the_next_cycle():
    s = run([client("ARIT", "arithmetic", count=1, start_us=13)])
    (rec,) = [r for r in s.engine.trace if r.what == "transfer"]
    assert rec.time == 20 and rec.get("waited") == 7  # U-42: cycles aligned on t = 0


# --- 9. incidents -----------------------------------------------------------------------------------


def test_key_error_is_reported_to_the_element():
    s = build({"clients": [client("ARIT", "arithmetic", count=1, address=40)]})
    good = s.memory.raw(40)
    s.memory.poke_raw(40, Catena(good.value ^ 1, good.key))  # one bit flipped, key unchanged
    s.run()
    assert s.clients[0].incidents == ["key"]
    assert s.dd.racs.get("ARIT", 0) == 40  # not advanced
    assert any(r.what == "incident" and r.get("reason") == "key" for r in s.engine.trace)


def test_address_outside_installed_blocks_fails_selection():
    s = build(
        {"memory_blocks": 2, "clients": [client("ARIT", "arithmetic", count=1, address=9000)]}
    )
    s.run()
    assert s.clients[0].incidents == ["selection"]


# --- modes, settings, errors -----------------------------------------------------------------------


def test_diagnostic_mode_warns_of_starvation():
    clients = [client("ARIT", "arithmetic", count=100), client("LOGI", "logical", count=1)]
    faithful = build({"clients": clients})
    faithful.run()
    diagnostic = build({"clients": clients}, mode="diagnostic")
    diagnostic.run()
    assert faithful.dd.stats.warnings == 0
    assert diagnostic.dd.stats.warnings == 1  # LOGI waited more than 50 cycles
    assert any(r.what == "starvation" for r in diagnostic.engine.trace)


def test_invalid_requests_and_settings():
    engine, memory = Engine(), Memory()
    dd = DataDistributor(engine, memory)
    port = dd.attach(object(), "arithmetic", "ARIT")
    with pytest.raises(ValueError):
        dd.attach(object(), "arithmetic", "ARIT")
    with pytest.raises(ValueError):
        dd.request(port, 0, "sideways")
    with pytest.raises(ValueError):
        dd.request(port, 0, WRITE)  # no catena to write
    with pytest.raises(ValueError):
        dd.request(port, 0, READ, address=12)  # only the PD gives an explicit address
    with pytest.raises(ValueError):
        DataDistributor(engine, memory, mode="other")
    with pytest.raises(ValueError):
        DataDistributor(engine, memory, behavior={"dd_cycle_grid": "free"})


def test_car_matrix():
    m = RacMatrix()
    assert m.size == 128  # MAQ [ONDE §2.2.1]
    m.allocate("ARIT", 4)
    m.set("ARIT", 3, 0o77777 + 2)
    assert m.get("ARIT", 3) == 1  # 15 bits
    assert m.advance("ARIT", 3, -1) == 1 and m.get("ARIT", 3) == 0
    with pytest.raises(IndexError):
        m.get("ARIT", 4)
    with pytest.raises(ValueError):
        m.allocate("BIG", 125)


def test_max_configuration_fits_in_the_matrix():
    cfg = data.get_config("max")
    s = build(
        {
            "clients": [
                client(f"{kind}{i}", kind, count=0)
                for kind, n in cfg.elements.items()
                if kind in data.load("topology")["classes"]
                for i in range(n)
            ]
        }
    )
    assert s.dd.racs.used <= 128


# --- command line ---------------------------------------------------------------------------------


def test_cli_dd_trace_in_french(capsys):
    assert main(["dd", str(SCENARIOS / "drum_arit.yaml"), "--trace", "--names", "fr"]) == 0
    out = capsys.readouterr().out
    assert "DCC  c2a   DRUM   quant. RAC0 02000→02001" in out
    assert "occupation de la mémoire : 100.0%" in out and "ratés 0" in out


def test_cli_dd_pd_reads_at_rapa(capsys):
    assert main(["dd", str(SCENARIOS / "quantity_first.yaml"), "--trace"]) == 0
    out = capsys.readouterr().out
    assert "PD     instr  cpar 00000" in out and "pdir" in out


def test_cli_dd_profile_and_mode(capsys):
    args = ["dd", str(SCENARIOS / "tape.yaml"), "--profile", "COURS", "--mode", "diagnostic"]
    assert main(args) == 0
    assert "COURS, 11 µs" in capsys.readouterr().out
