"""Fail-closed authored-content and NPC-policy regressions, not runtime tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from validate_factions import load_sources, validate
from faction_model import Rejected, npc_access


class FactionReadinessRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.campaign = load_sources()
        self.faction_id = self.catalog["factions"][0]["id"]

    def test_unknown_npc_faction_rejected_before_neutral_or_guest_policy(self) -> None:
        for neutral, guest in [(False, False), (True, False), (False, True), (True, True)]:
            with self.subTest(neutral=neutral, guest=guest):
                with self.assertRaisesRegex(Rejected, "UnknownNpcFaction"):
                    npc_access(self.catalog, self.faction_id, "faction.unknown",
                               neutral=neutral, guest=guest)

    def test_unauthored_starter_reward_rejected(self) -> None:
        starter_id = self.catalog["factions"][0]["starter"]["item_id"]
        next(item for item in self.campaign["items"] if item["id"] == starter_id)["authored"] = False
        self.assertTrue(any("starter reward" in error for error in validate(self.catalog, self.campaign)))

    def test_unauthored_quest_reward_rejected(self) -> None:
        reward_id = self.campaign["quests"][1]["reward"]["items"][0]["item_id"]
        next(item for item in self.campaign["items"] if item["id"] == reward_id)["authored"] = False
        self.assertTrue(any("critical reward" in error for error in validate(self.catalog, self.campaign)))

    def test_unauthored_recipe_output_rejected(self) -> None:
        output_id = self.campaign["recipes"][0]["output_id"]
        next(item for item in self.campaign["items"] if item["id"] == output_id)["authored"] = False
        self.assertTrue(any("recipe output" in error for error in validate(self.catalog, self.campaign)))

    def test_unauthored_recipe_input_rejected(self) -> None:
        input_id = self.campaign["recipes"][0]["inputs"][0]["id"]
        next(item for item in self.campaign["items"] if item["id"] == input_id)["authored"] = False
        self.assertTrue(any("recipe input" in error for error in validate(self.catalog, self.campaign)))

    def test_unauthored_nonroot_quest_rejected(self) -> None:
        self.campaign["quests"][1]["authored"] = False
        self.assertTrue(any("Incomplete authored quest" in error for error in validate(self.catalog, self.campaign)))

    def test_unauthored_onward_spawn_rejected(self) -> None:
        spawn_id = self.campaign["quests"][-1]["follow_up"]["travel_spawn_id"]
        next(spawn for spawn in self.campaign["spawns"] if spawn["id"] == spawn_id)["authored"] = False
        self.assertTrue(any("onward travel" in error for error in validate(self.catalog, self.campaign)))

    def test_onward_spawn_must_admit_the_quest_faction(self) -> None:
        spawn_id = self.campaign["quests"][-1]["follow_up"]["travel_spawn_id"]
        spawn = next(spawn for spawn in self.campaign["spawns"] if spawn["id"] == spawn_id)
        spawn["allowed_factions"].remove(self.faction_id)
        self.assertTrue(any("onward travel" in error for error in validate(self.catalog, self.campaign)))

    def test_authored_spawn_requires_a_registered_map_contract(self) -> None:
        manifest = json.loads((TOOLS.parent / "sources/current-asset-manifest.json").read_text())
        names = {asset["name"] for asset in manifest["assets"]}
        spawn_id = self.campaign["quests"][-1]["follow_up"]["travel_spawn_id"]
        next(spawn for spawn in self.campaign["spawns"] if spawn["id"] == spawn_id)["map_id"] = "L_MissingMap"
        errors = validate(self.catalog, self.campaign, asset_names=names)
        self.assertTrue(any("spawn map" in error for error in errors))

    def test_policy_versions_and_modifier_caps_reject_invalid_values(self) -> None:
        for field in ["version", "personal_modifier_cap", "pressure_modifier_cap"]:
            for value in [-1, True, "20", 1.5]:
                with self.subTest(field=field, value=value):
                    catalog, campaign = load_sources()
                    catalog["policy"][field] = value
                    self.assertTrue(any(field in error for error in validate(catalog, campaign)))


if __name__ == "__main__":
    unittest.main()
