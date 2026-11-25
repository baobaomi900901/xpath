"""Deterministic business data; run identity and metadata are kept separate."""
import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROFILES = ("basic", "standard", "advanced")


def make_fixture(profile="standard", seed=42):
    if profile not in PROFILES:
        raise ValueError("未知场景档位")
    if not isinstance(seed, int) or not 0 <= seed <= 999999:
        raise ValueError("seed 必须是 0 到 999999 的整数")
    rng = random.Random(seed)
    context = dict(run_id="", batch_id=f"SC-20261117-{profile[0].upper()}{seed}",
                   today="2026-11-17", deadline="2026-11-24", profile=profile,
                   seed=seed, plant="华东工厂", warehouse="一号仓")
    suppliers = [dict(supplier_id=sid, name=name, active=active) for sid, name, active in
                 [("S001", "华辰供应商", True), ("S002", "博远供应商", True),
                  ("S003", "恒信供应商", True), ("S004", "停用供应商", False)]]
    inventory = []

    def material(mid, name, current, safety, target, unit="件", plant="华东工厂", warehouse="一号仓", enabled=True):
        inventory.append(dict(material_id=mid, name=name, unit=unit, plant=plant,
                              warehouse=warehouse, current=current, safety=safety,
                              target=target, enabled=enabled))

    material("M001", "轴承组件", 40, 80, 160)
    material("M002", "密封圈", 150, 100, 200)
    material("M003", "传动齿轮", 20, 60, 120)
    material("M004", "紧固件", 60, 60, 120)
    quotes = []

    def quote(qid, mid, sid, price, available=800, moq=1, lead=3, valid="2026-12-31", active=True, unit="件", currency="CNY"):
        supplier = next(s for s in suppliers if s["supplier_id"] == sid)
        quotes.append(dict(quote_id=qid, material_id=mid, supplier_id=sid,
                           supplier_name=supplier["name"], unit_price=f"{price:.2f}",
                           available=available, moq=moq, lead_days=lead,
                           valid_until=valid, active=active and supplier["active"],
                           currency=currency, unit=unit))

    quote("Q001", "M001", "S001", 10)
    quote("Q002", "M001", "S002", 9, available=80)
    quote("Q003", "M001", "S003", 11)
    quote("Q004", "M003", "S001", 6)
    quote("Q005", "M003", "S003", 5)
    if profile != "basic":
        for index in range(5, 25):
            mid = f"M{index:03}"
            unit = "盒" if index % 5 == 0 else "件"
            safety = rng.choice([40, 60, 80])
            current = safety - rng.randint(5, 25) if index % 3 != 0 else safety + rng.randint(0, 40)
            if index == 6:
                current = 20
            material(mid, "轴承组件" if index == 6 else f"生产辅料 {index:02}", current, safety, safety * 2, unit)
            price = rng.randint(300, 2400) / 100
            for offset, sid in enumerate(["S001", "S002", "S003"]):
                # Two equal prices exercise the lead-time tie break; others vary by seed.
                adjustment = 0 if index == 5 and offset < 2 else ((index + offset) % 3) * 0.4
                quote(f"Q{index:03}{offset}", mid, sid, price + adjustment,
                      lead=4 if offset == 0 else 2 + offset, unit=unit)
        material("M901", "外厂物料", 0, 90, 180, plant="华南工厂")
        material("M902", "其他仓物料", 0, 90, 180, warehouse="二号仓")
        material("M903", "停用物料", 0, 90, 180, enabled=False)
        quote("Q-EXPIRED", "M001", "S002", 1, valid="2026-11-16")
        quote("Q-INACTIVE", "M001", "S004", 1)
        quote("Q-LATE", "M003", "S002", 1, lead=10)
        quote("Q-MOQ", "M003", "S002", 2, moq=200)
        quote("Q-UNIT", "M003", "S002", 1, unit="箱")
        quote("Q-USD", "M003", "S002", 1, currency="USD")
    if profile == "advanced":
        material("M099", "特殊耐热密封件", 5, 30, 80)
        quote("Q0991", "M099", "S001", 20, available=10)
        quote("Q0992", "M099", "S002", 18, valid="2026-11-01")
    rng.shuffle(inventory)
    rng.shuffle(quotes)
    return dict(context=context, inventory=inventory, quotes=quotes, suppliers=suppliers)


def create_run(path, profile="standard", seed=42, agent="unspecified", track="cli", obstacles=False):
    if track not in ("cli", "sdk"):
        raise ValueError("track 必须为 cli 或 sdk")
    path = Path(path)
    fixture = make_fixture(profile, seed)
    fixture["context"]["run_id"] = uuid.uuid4().hex
    fixture["context"]["batch_id"] += "-" + fixture["context"]["run_id"][:6].upper()
    fixture["context"]["obstacles"] = bool(obstacles)
    path.mkdir(parents=True, exist_ok=False)
    (path / "fixture.json").write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
    metadata = dict(agent=agent, track=track, profile=profile, seed=seed,
                    obstacles=bool(obstacles),
                    run_id=fixture["context"]["run_id"], created_at=datetime.now(timezone.utc).isoformat())
    (path / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (path / "state.json").write_text(json.dumps(dict(orders=[], exceptions=[], events=[], failure_consumed=False)), encoding="utf-8")
    return fixture
