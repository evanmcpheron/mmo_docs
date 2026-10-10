"""Render faction source records through the existing offline-manual section format."""
from __future__ import annotations

import copy
import json
from pathlib import Path


def section(title: str, *paragraphs: str, rows: list | None = None,
            headers: list[str] | None = None, steps: list[str] | None = None) -> dict:
    result = {"title": title, "paragraphs": list(paragraphs)}
    if rows is not None:
        result["table"] = {"headers": headers or ["Field", "Value"], "rows": rows}
    if steps is not None:
        result["steps"] = steps
    return result


def value_text(value: object) -> str:
    if isinstance(value, str):
        return value
    return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "`"


def record_rows(record: dict) -> list:
    return [[key, value_text(value)] for key, value in record.items()]


def faction_localization(root: Path) -> dict:
    catalog = json.loads((root / 'sources/factions.json').read_text(encoding='utf-8'))
    campaign = json.loads((root / 'sources/hearthward-campaign.json').read_text(encoding='utf-8'))
    strings = {}
    for faction in catalog['factions']:
        strings[faction['display_key']] = faction['display_name']
        if faction['selection']['locked_reason_key']:
            strings[faction['selection']['locked_reason_key']] = 'This faction is not available for new characters. Its campaign and starting content are still in production.'
        if faction['story']['authored']:
            strings[faction['story']['journal_key']] = faction['story']['concept']
    for npc in campaign['npcs']:
        strings[npc['dialogue_key']] = npc['intro_text']
    for quest in campaign['quests']:
        strings[quest['title_key']] = quest['title']
        strings[quest['journal_key']] = quest['journal_text']
        strings[quest['cutscene']['key']] = quest['journal_text']
        for state, text in quest['journal_states'].items():
            strings[quest['journal_key'] + '.' + state] = text
        for branch in quest['branches']:
            strings[branch['text_key']] = branch['text']
        for node in quest['dialogue']:
            strings[node['text_key']] = node['text']
            for choice in node['choices']:
                strings[choice['text_key']] = choice['text']
                strings[choice['response_key']] = choice['response']
    return {'schema_version': 1, 'locale': 'en', 'scope': 'Generated from factions.json and hearthward-campaign.json by build_manual_indexes.py; do not hand-edit. Future story keys remain reserved, not authored.', 'strings': dict(sorted(strings.items()))}


def faction_properties(asset: dict, root: Path) -> list:
    rows = copy.deepcopy(asset['properties'])
    quest_id = asset.get('faction_content_record')
    if quest_id is None:
        return rows
    campaign = json.loads((root / 'sources/hearthward-campaign.json').read_text(encoding='utf-8'))
    quest = next(row for row in campaign['quests'] if row['id'] == quest_id)
    fields = {'Objectives / alternatives': 'objectives', 'Reward / source guard': 'reward', 'Branch choices': 'branches'}
    for row in rows:
        if row[0] in fields:
            row[2] = value_text(quest[fields[row[0]]])
    return rows


def faction_sections(kind: str, root: Path) -> list[dict]:
    def read(name: str) -> dict:
        return json.loads((root / "sources" / name).read_text(encoding="utf-8"))

    if kind == "catalog":
        catalog = read("factions.json")
        sections = [section("Taxonomy and source of truth", catalog["scope"],
                            "Political allegiance is mandatory and permanent. Civic reputation, personal faction standing, regional pressure and hostile NPC affiliation are separate facts with separate owners.")]
        for faction in catalog["factions"]:
            sections.append(section(faction["display_name"], faction["ideology"],
                "Stable ID: `" + faction["id"] + "`. " + faction["story"]["concept"],
                "Authored MVP selection: " + str(faction["selection"]["selectable_for_new_character"]).lower() + "; existing continuation: " + faction["selection"]["existing_character_continuation"] + ". Real deployment still requires cooked-content and solo acceptance.",
                rows=[["Starting region / map / spawn", value_text(faction["start"])],
                      ["Story entry / cast", value_text(faction["story"])],
                      ["Initial separate standings", value_text(faction["initial_reputation"])],
                      ["Services and rewards", value_text(faction["services"])],
                      ["Starter / presentation", value_text(faction["starter"])],
                      ["Content readiness", value_text(faction["readiness"])]]))
        sections.append(section("Baseline symmetric political relationships", catalog["relations"]["symmetry"],
            headers=["Factions", "Score", "Political reason"],
            rows=[[" / ".join(pair["factions"]), str(pair["score"]), pair["motive"]] for pair in catalog["relations"]["pairs"]]))
        for organization in catalog["organizations"]:
            sections.append(section(organization["name"], rows=record_rows(organization)))
        sections.append(section("Non-playable antagonist", rows=record_rows(catalog["enemies"][0])))
        sections.append(section("Policy and tunings", rows=record_rows(catalog["policy"])))
        return sections
    if kind == "implementation":
        contract = read("faction-implementation.json")
        integration = read("faction-asset-integration.json")
        return contract["sections"] + [section("Operation-to-proof map",
            headers=["Operation", "Authorization", "Atomic commit", "Required outcome", "Evidence scope"],
            rows=[[row[key] for key in ["id", "authorization", "commit", "result", "verification"]] for row in contract["operations"]]),
            section("New and extended assets", "New definitions: " + ", ".join("[[asset:" + name + "]]" for name in integration["new_assets"]),
                    "Existing owners extended: " + ", ".join("[[asset:" + name + "]]" for name in integration["materially_extended_assets"])),
            section("Phase integration without renumbering", headers=["Phase", "Configure / current scope", "Reopen consumers", "Acceptance"],
                    rows=[[str(row["phase"]), row["configure"], row["consumers"], row["acceptance"]] for row in integration["phase_assignments"]])]
    if kind == "campaign":
        campaign = read("hearthward-campaign.json")
        sections = [section("Campaign setup and exact graph", value_text(campaign["tile_contract"]),
            "Root: `" + campaign["root_quest_id"] + "`; full faction slice Phase " + str(campaign["complete_slice_phase"]) + ". All placements below are authored tile anchors requiring real-map collision/spawn verification; no map binary is claimed present.",
            headers=["Quest / asset", "Prerequisites", "Next", "Why it matters"],
            rows=[[q["id"] + " / [[asset:" + q["asset"] + "]]", ", ".join(q["prerequisites"]) or "New eligible faction character", ", ".join(q["next_quest_ids"]) or "Shared region story", q["why"]] for q in campaign["quests"]]),
            section("Safe spawns and reserved future starts", headers=["Spawn", "Map / zone", "Tile / facing", "Allowed factions", "Authored / safe"],
                    rows=[[s["id"], s["map_id"] + " / " + s["zone_id"], value_text(s.get("tile")) + " / " + s.get("facing", "unassigned"), ", ".join(s["allowed_factions"]), str(s["authored"]) + " / " + str(s["safe"])] for s in campaign["spawns"]]),
            section("NPC cast and services", headers=["NPC / asset", "Allegiance / organization", "Map / anchor", "Services and availability"],
                    rows=[[n["id"] + " / [[asset:" + n["asset"] + "]]", str(n["faction_id"]) + " / " + str(n["organization_id"]), n["map_id"] + " " + value_text(n["tile"]) + " " + n["facing"], ", ".join(n["services"]) + ". " + n["availability"]] for n in campaign["npcs"]])]
        rules = {row["quest_id"]: row["expression"] for row in campaign["objective_rules"]}
        for number, quest in enumerate(campaign["quests"], 1):
            sections.append(section(f"{number}. {quest['title']} — objectives", quest["why"],
                "Giver: `" + quest["quest_giver_id"] + "`; turn-in: `" + quest["turn_in_npc_id"] + "`; marker: " + value_text(quest["marker_tile"]) + ". " + rules[quest["id"]],
                headers=["Objective", "Required units", "Accepted source", "Description / alternatives"],
                rows=[[o["id"], str(o["required_units"]), o["source_id"], o["description"] + " " + value_text(o["alternatives"])] for o in quest["objectives"]]))
            for node in quest["dialogue"]:
                sections.append(section(f"{number}. {quest['title']} — {node['speaker']}",
                    node["text"], "Line key: `" + node["text_key"] + "`. " + node["authority"],
                    headers=["Choice / key", "Player text", "NPC response / key"],
                    rows=[[choice["id"] + " / " + choice["text_key"], choice["text"], choice["response"] + " / " + choice["response_key"]] for choice in node["choices"]]))
            sections.append(section(f"{number}. {quest['title']} — commit, reward and recovery",
                quest["dialogue_dispatch"], quest["failure_policy"], quest["late_arrival_policy"],
                rows=[["Exact reward / source generation", value_text(quest["reward"])],
                      ["Branch effects", value_text(quest["branches"])], ["Journal states / key", value_text(quest["journal_states"]) + " / " + quest["journal_key"]],
                      ["Optional scene / skip", value_text(quest["cutscene"])], ["Follow-up", value_text(quest.get("follow_up", quest["next_quest_ids"]))]]))
            for route in quest.get("contribution_routes", []):
                sections.append(section("Contribution: " + route["id"], rows=record_rows(route)))
        sections.append(section("Interaction anchors and trusted evidence dispatch", headers=["Interaction", "NPC", "Tile", "Objective / evidence key"],
            rows=[[row["id"], str(row["npc_id"]), value_text(row["tile"]), row["objective_id"] + " / " + row["evidence_key"]] for row in campaign["interactions"]]))
        for name in ["project", "legacy_arcs"]:
            sections.append(section(name.replace("_", " ").title(), value_text(campaign[name])))
        for name in ["recipes", "resource_routes", "encounters", "visuals"]:
            for row in campaign[name]:
                sections.append(section(name.replace("_", " ").title() + ": " + row["id"], rows=record_rows(row)))
        sections.append(section("Full acceptance route", steps=campaign["acceptance_route"]))
        return sections
    if kind == "acceptance":
        data = read("faction-acceptance.json")
        sections = data["sections"]
        for case in data["cases"]:
            sections.append(section(case["id"] + " — " + case["title"],
                "Runtime status: " + case["runtime_status"] + ". Prerequisites: " + case["prerequisites"],
                "Expected: " + case["expected"], "Offline evidence scope: " + case["offline_scope"], steps=case["steps"]))
        return sections
    if kind == "compatibility":
        data = read("faction-compatibility.json")
        return [section("Inspection scope", data["scope"], rows=record_rows(data["revisions"]))] + [section(row["id"] + " — " + row["subsystem"],
            "Sources: " + "; ".join(row["sources"]), "Observed: " + row["current"], "Required: " + row["requested"],
            "Resolution: " + row["resolution"], "Migration/test: " + row["migration_test"], "Evidence: " + row["evidence"]) for row in data["discrepancies"]]
    if kind == "traceability":
        data = read("faction-traceability.json")
        return [section("Traceability scope", data["scope"])] + [section(row["id"] + " — " + row["requirement"],
            "Source definitions: " + "; ".join(row["sources"]),
            "Assets: " + ", ".join("[[asset:" + name + "]]" for name in row["assets"]),
            "Phases: " + ", ".join(str(number) for number in row["phases"]) + ". Guide: " + ", ".join("[[" + page + "|" + page + "]]" for page in row["pages"]),
            "Integration checks: " + "; ".join(row["checks"]), "Documentation scope: " + row["documentation_status"] + "; game runtime: " + row["runtime_status"]) for row in data["requirements"]]
    raise ValueError("Unknown faction source renderer: " + kind)
