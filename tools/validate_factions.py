#!/usr/bin/env python3
"""Validate authored faction contracts, not cooked Unreal assets or live gameplay."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")


def load_sources(root: Path = ROOT) -> tuple[dict, dict]:
    return tuple(json.loads((root / path).read_text(encoding="utf-8")) for path in (
        "sources/factions.json", "sources/hearthward-campaign.json"
    ))


def unique_records(records: list[dict], label: str, errors: list[str]) -> dict[str, dict]:
    result = {}
    for record in records:
        identifier = record.get("id", "")
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier) or len(identifier) > 96:
            errors.append(f"{label}: invalid stable ID {identifier!r}")
        if identifier in result:
            errors.append(f"{label}: duplicate ID {identifier}")
        result[identifier] = record
    return result


def validate(catalog: dict, campaign: dict, *, deployment: bool = False,
             asset_names: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    if catalog.get("schema_version") != 1 or campaign.get("schema_version") != 1:
        errors.append("Unsupported faction/campaign schema version")
    if type(catalog.get("catalog_version")) is not int or catalog["catalog_version"] < 1:
        errors.append("Invalid catalog version")
    if type(catalog.get("availability_revision")) is not int or catalog["availability_revision"] < 1:
        errors.append("Invalid availability revision")
    factions = unique_records(catalog.get("factions", []), "Faction", errors)
    organizations = unique_records(catalog.get("organizations", []), "Organization", errors)
    enemies = unique_records(catalog.get("enemies", []), "Enemy", errors)
    for collection, namespace, kind in [(factions, "faction.", "playable_allegiance"),
                                        (organizations, "organization.", "independent_organization"),
                                        (enemies, "enemy.", "nonplayable_hostile")]:
        for identifier, record in collection.items():
            if not identifier.startswith(namespace) or record.get("kind") != kind:
                errors.append(f"Taxonomy mismatch: {identifier}")
    if not factions or not organizations:
        errors.append("Political allegiance and independent organizations are both required")
    if set(factions) & (set(organizations) | set(enemies)):
        errors.append("Political, civic and antagonist namespaces overlap")
    policy = catalog.get("policy", {})
    if type(policy.get("version")) is not int or policy["version"] < 1:
        errors.append("Invalid policy version")
    for field in ["personal_modifier_cap", "pressure_modifier_cap"]:
        if type(policy.get(field)) is not int or not 0 <= policy[field] <= 100:
            errors.append(f"Invalid {field}")
    if policy.get("open_world_player_damage") is not False:
        errors.append("Mandatory baseline player damage must remain disabled")
    for prefix in ["reputation", "relationship", "regional_pressure"]:
        low, high = policy.get(prefix + "_min"), policy.get(prefix + "_max")
        if type(low) is not int or type(high) is not int or low >= 0 or high <= 0 or low >= high:
            errors.append(f"Invalid {prefix} bounds")
    for field in ["personal_modifier_divisor", "pressure_modifier_divisor"]:
        if type(policy.get(field)) is not int or policy[field] <= 0:
            errors.append(f"Invalid {field}")
    thresholds = policy.get("attitude_thresholds", {})
    if set(thresholds) != {"friendly", "neutral", "wary", "hostile"} or not all(type(value) is int for value in thresholds.values()):
        errors.append("Invalid attitude thresholds")
    elif not thresholds["friendly"] > thresholds["neutral"] > thresholds["wary"] > thresholds["hostile"]:
        errors.append("Attitude thresholds must be strictly descending")
    if not policy.get("safe_route_ids") or not policy.get("neutral_zones"):
        errors.append("Neutral access and safe alternate routes are mandatory")
    resolution = policy.get("resolution", {})
    if resolution.get("essential_progress_requires_winner") is not False or resolution.get("immutable_construction") is not True:
        errors.append("Political outcomes cannot gate core progress or destroy construction")
    if resolution.get("tie_break") not in resolution.get("options", []):
        errors.append("Missing deterministic political tie-break")
    if resolution.get("votes_per_account_per_round") != 1 or resolution.get("round_duration_seconds", 0) <= 0:
        errors.append("Invalid bounded ballot policy")
    relation_policy = catalog.get("relations", {})
    if relation_policy.get("symmetry") != "symmetric_base_and_overrides; author one canonical unordered pair":
        errors.append("Unexpected relationship symmetry contract")
    pairs = set()
    for row in relation_policy.get("pairs", []):
        pair = tuple(sorted(row.get("factions", [])))
        if len(pair) != 2 or len(set(pair)) != 2 or not set(pair) <= set(factions):
            errors.append(f"Invalid relation pair {pair}")
        if pair in pairs:
            errors.append(f"Duplicate/asymmetric relation pair {pair}")
        pairs.add(pair)
        if type(row.get("score")) is not int or not -100 <= row["score"] <= 100:
            errors.append(f"Invalid relationship score {pair}")
        if not row.get("motive"):
            errors.append(f"Relationship motive missing {pair}")
    expected_pairs = {tuple(sorted((first, second))) for first in factions for second in factions if first != second}
    if pairs != expected_pairs:
        errors.append("Base relation matrix is incomplete")
    spawns = unique_records(campaign.get("spawns", []), "Spawn", errors)
    npcs = unique_records(campaign.get("npcs", []), "NPC", errors)
    items = unique_records(campaign.get("items", []), "Item", errors)
    recipes = unique_records(campaign.get("recipes", []), "Recipe", errors)
    quests = unique_records(campaign.get("quests", []), "Quest", errors)
    for record in list(npcs.values()) + list(items.values()) + list(recipes.values()) + list(quests.values()) + campaign.get("encounters", []):
        if asset_names is not None and record.get("asset") not in asset_names:
            errors.append(f"Missing asset contract: {record.get('asset')}")
    for spawn in spawns.values():
        if not set(spawn.get("allowed_factions", [])) <= set(factions):
            errors.append(f"Unknown faction in spawn {spawn['id']}")
        if spawn.get("authored"):
            if asset_names is not None and spawn.get("map_id") not in asset_names:
                errors.append(f"Missing authored spawn map contract {spawn['id']}")
            position = spawn.get("tile")
            if not isinstance(position, list) or len(position) != 2 or not all(type(value) is int and 0 <= value <= 4095 for value in position):
                errors.append(f"Invalid authored spawn coordinate {spawn['id']}")
    for npc in npcs.values():
        if npc.get("faction_id") is not None and npc["faction_id"] not in factions:
            errors.append(f"Unknown NPC allegiance {npc['id']}")
        if npc.get("organization_id") is not None and npc["organization_id"] not in organizations:
            errors.append(f"Unknown NPC civic organization {npc['id']}")
    for recipe in recipes.values():
        if items.get(recipe.get("output_id"), {}).get("authored") is not True or recipe.get("authored") is not True:
            errors.append(f"Missing recipe output {recipe['id']}")
        if type(recipe.get("output_quantity")) is not int or recipe["output_quantity"] <= 0:
            errors.append(f"Invalid recipe output quantity {recipe['id']}")
        for ingredient in recipe.get("inputs", []):
            if items.get(ingredient.get("id"), {}).get("authored") is not True or type(ingredient.get("quantity")) is not int or ingredient["quantity"] <= 0:
                errors.append(f"Missing or invalid recipe input {recipe['id']}")
    for identifier, faction in factions.items():
        required = {"id", "display_name", "display_key", "content_version", "kind", "ideology", "selection", "start", "story", "initial_reputation", "services", "starter", "readiness"}
        if set(faction) != required:
            errors.append(f"Faction field set mismatch {identifier}: {sorted(set(faction) ^ required)}")
            continue
        if type(faction["content_version"]) is not int or faction["content_version"] < 1:
            errors.append(f"Invalid content version {identifier}")
        selection = faction["selection"]
        if type(selection.get("selectable_for_new_character")) is not bool:
            errors.append(f"Invalid selection flag {identifier}")
        if selection.get("existing_character_continuation") != "retain_identity_and_recover":
            errors.append(f"Existing-character continuity must survive new-selection policy {identifier}")
        starter = faction["starter"]
        if starter.get("facing_count") != 4 or starter.get("unique_art_required") is not False:
            errors.append(f"Unsupported starter art requirement {identifier}")
        if items.get(starter.get("item_id"), {}).get("authored") is not True or starter.get("quantity") != 1:
            errors.append(f"Missing critical starter reward {identifier}")
        if not all(faction["story"].get(key) for key in ["root_quest_id", "mentor_id", "cast_ids", "initial_flags", "journal_key", "dialogue_key", "cutscene_key", "concept"]):
            errors.append(f"Incomplete future story entry contract {identifier}")
        for axis, definitions in [("factions", factions), ("organizations", organizations)]:
            standing = faction["initial_reputation"].get(axis, {})
            if set(standing) != set(definitions) or not all(type(value) is int and -1000 <= value <= 1000 for value in standing.values()):
                errors.append(f"Invalid initial {axis} standing {identifier}")
        start = faction["start"]
        fallback = spawns.get(start.get("fallback_spawn_id"))
        if not fallback or not fallback.get("authored") or not fallback.get("safe") or identifier not in fallback.get("allowed_factions", []):
            errors.append(f"Missing continuation fallback {identifier}")
        spawn = spawns.get(start.get("spawn_id"))
        if not spawn or spawn.get("map_id") != start.get("map_id") or spawn.get("zone_id") != start.get("zone_id"):
            errors.append(f"Starting map/zone/spawn mismatch {identifier}")
        if not selection.get("selectable_for_new_character"):
            if not selection.get("locked_reason_key"):
                errors.append(f"Locked faction requires a UI reason {identifier}")
            continue
        root_quest = quests.get(faction["story"]["root_quest_id"])
        if not root_quest or not root_quest.get("authored") or root_quest.get("faction_id") != identifier:
            errors.append(f"Selected faction lacks authored root quest {identifier}")
        if any(npc_id not in npcs or not npcs[npc_id].get("authored") for npc_id in faction["story"]["cast_ids"]):
            errors.append(f"Selected faction lacks authored NPC cast {identifier}")
        if not spawn or not spawn.get("authored") or not spawn.get("safe") or identifier not in spawn.get("allowed_factions", []):
            errors.append(f"Selected faction lacks authenticated safe spawn {identifier}")
        if not faction["readiness"].get("authored_specification") or faction["readiness"].get("blocking_content"):
            errors.append(f"Selected faction has unresolved authored dependencies {identifier}")
        if deployment and (not faction["readiness"].get("cooked_content_verified") or not faction["readiness"].get("solo_acceptance_verified")):
            errors.append(f"Deployment blocked: cooked content and solo gameplay are unverified for {identifier}")
    root_quest_id = campaign.get("root_quest_id")
    if root_quest_id not in quests:
        errors.append("Campaign root quest missing")
    reward_sources, objective_ids, localization = set(), set(), {}
    for quest in quests.values():
        if quest.get("content_version") != campaign.get("content_version"):
            errors.append(f"Content-version mismatch {quest['id']}")
        if quest.get("faction_id") not in factions:
            errors.append(f"Unknown quest allegiance {quest['id']}")
        if quest.get("minimum_humans") != 1 or quest.get("pvp_required") is not False or quest.get("party_required") is not False:
            errors.append(f"Mandatory PvP/group dependency {quest['id']}")
        if quest.get("authored") is not True or not quest.get("objectives") or not quest.get("dialogue") or not quest.get("why"):
            errors.append(f"Incomplete authored quest {quest['id']}")
        if quest.get("quest_giver_id") not in npcs or quest.get("turn_in_npc_id") not in npcs:
            errors.append(f"Missing quest NPC {quest['id']}")
        for prerequisite in quest.get("prerequisites", []):
            if prerequisite not in quests or quest["id"] not in quests[prerequisite].get("next_quest_ids", []):
                errors.append(f"Broken prerequisite edge {quest['id']}")
        for successor in quest.get("next_quest_ids", []):
            if successor not in quests or quest["id"] not in quests[successor].get("prerequisites", []):
                errors.append(f"Broken successor edge {quest['id']}")
        if not set(quest.get("required_recipe_ids", [])) <= set(recipes):
            errors.append(f"Missing recipe dependency {quest['id']}")
        reward = quest.get("reward", {})
        source = reward.get("source_id")
        if not source or source in reward_sources:
            errors.append(f"Missing or duplicate reward source {quest['id']}")
        reward_sources.add(source)
        for field in ["combat_xp", "copper", "vocation_xp"]:
            if type(reward.get(field)) is not int or not 0 <= reward[field] <= 1000000:
                errors.append(f"Invalid reward amount {quest['id']}/{field}")
        for item in reward.get("items", []):
            if items.get(item.get("item_id"), {}).get("authored") is not True or type(item.get("quantity")) is not int or not 1 <= item["quantity"] <= 100:
                errors.append(f"Missing critical reward {quest['id']}")
        for objective in quest.get("objectives", []):
            if objective.get("id") in objective_ids or type(objective.get("required_units")) is not int or objective["required_units"] <= 0:
                errors.append(f"Invalid or duplicate objective {quest['id']}")
            objective_ids.add(objective.get("id"))
        for axis, subject_definitions in [("faction_reputation", factions), ("organization_reputation", organizations)]:
            for changes in [reward] + quest.get("branches", []):
                for subject, delta in changes.get(axis, {}).items():
                    if subject not in subject_definitions or type(delta) is not int or not -1000 <= delta <= 1000:
                        errors.append(f"Invalid reputation reward {quest['id']}/{subject}")
        branches = quest.get("branches", [])
        if branches and (len({branch.get("mechanical_reward_tier") for branch in branches}) != 1 or len({branch.get("next_quest_id") for branch in branches}) != 1):
            errors.append(f"Branch progression parity violation {quest['id']}")
        for branch in branches:
            if branch.get("next_quest_id") not in quest.get("next_quest_ids", []):
                errors.append(f"Branch does not rejoin campaign {quest['id']}")
        for route in quest.get("contribution_routes", []):
            if route.get("recipe_id") is not None and route["recipe_id"] not in recipes:
                errors.append(f"Missing contribution recipe {route['id']}")
            if route.get("item_id") is not None and route["item_id"] not in items:
                errors.append(f"Missing contribution item {route['id']}")
        dialogue_ids = {node.get("id") for node in quest.get("dialogue", [])}
        if len(dialogue_ids) != len(quest.get("dialogue", [])):
            errors.append(f"Duplicate dialogue node {quest['id']}")
        for node in quest.get("dialogue", []):
            if node.get("continue_to") is not None and node["continue_to"] not in dialogue_ids:
                errors.append(f"Missing dialogue continuation {quest['id']}")
            for choice in node.get("choices", []):
                if choice.get("branch_id") is not None and choice["branch_id"] not in {branch["id"] for branch in branches}:
                    errors.append(f"Unknown dialogue branch {quest['id']}")
            pairs_to_check = [(node.get("text_key"), node.get("text"))]
            for choice in node.get("choices", []):
                pairs_to_check.extend([(choice.get("text_key"), choice.get("text")), (choice.get("response_key"), choice.get("response"))])
            for key, text in pairs_to_check:
                if not key or not text or (key in localization and localization[key] != text):
                    errors.append(f"Invalid/conflicting localization {key}")
                localization[key] = text
    rules = campaign.get("objective_rules", [])
    if {rule.get("quest_id") for rule in rules} != set(quests) or len(rules) != len(quests):
        errors.append("Each quest requires exactly one authored objective rule")
    for interaction in campaign.get("interactions", []):
        if interaction.get("objective_id") not in objective_ids or (interaction.get("npc_id") is not None and interaction["npc_id"] not in npcs):
            errors.append(f"Missing interaction objective/NPC {interaction.get('id')}")
    for resource in campaign.get("resource_routes", []):
        if resource.get("item_id") not in items or not resource.get("cells"):
            errors.append(f"Missing resource item/cells {resource.get('id')}")
        if not 1 <= resource.get("minimum_yield", 0) <= resource.get("maximum_yield", 0) <= 100:
            errors.append(f"Invalid resource yield {resource.get('id')}")
    visited, visiting = set(), set()
    def visit(identifier: str) -> None:
        if identifier in visiting:
            errors.append(f"Quest cycle at {identifier}")
            return
        if identifier in visited or identifier not in quests:
            return
        visiting.add(identifier)
        for successor in quests[identifier].get("next_quest_ids", []):
            visit(successor)
        visiting.remove(identifier)
        visited.add(identifier)
    visit(root_quest_id)
    for faction in factions.values():
        if faction["selection"]["selectable_for_new_character"]:
            visit(faction["story"]["root_quest_id"])
    if set(quests) != visited:
        errors.append("Campaign contains unreachable quests")
    project = campaign.get("project", {})
    if project.get("id") != "project.elderwood.north-road" or project.get("storage_key") != "NorthRoad" or project.get("required_humans") != 1 or project.get("essential_target") != 12:
        errors.append("Existing NorthRoad identity or solo essential target changed")
    free_routes = [route for quest in quests.values() for route in quest.get("contribution_routes", []) if route.get("vocation_id") is None and route.get("copper_cost") == 0]
    if not free_routes or any(not route.get("steps") for route in free_routes):
        errors.append("Missing attainable profession-neutral contribution path")
    for quest in quests.values():
        follow_up = quest.get("follow_up")
        if follow_up:
            destination = spawns.get(follow_up.get("travel_spawn_id"), {})
            if destination.get("authored") is not True or destination.get("safe") is not True or quest.get("faction_id") not in destination.get("allowed_factions", []):
                errors.append(f"Missing authored faction-safe onward travel dependency {quest['id']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--deployment", action="store_true", help="Also require recorded cooked-content and solo-runtime readiness; expected to fail for this documentation-only delivery.")
    arguments = parser.parse_args()
    try:
        catalog, campaign = load_sources(arguments.root)
        asset_names = {row["name"] for row in json.loads((arguments.root / "sources/current-asset-manifest.json").read_text())["assets"]}
        errors = validate(catalog, campaign, deployment=arguments.deployment, asset_names=asset_names)
    except (KeyError, TypeError, ValueError, OSError) as exception:
        errors = [f"Malformed faction source: {exception}"]
    report = {"status": "fail" if errors else "pass", "scope": "Authored schema/reference/graph invariants only", "deployment_gate": arguments.deployment, "errors": errors, "unreal_runtime": "not_run"}
    print(json.dumps(report, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
