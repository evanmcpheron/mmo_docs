"""SQLite conformance fixture for the documented transaction rules.

This is not the Briarwake backend, authentication, networking or Unreal runtime.
Principals and evidence are explicitly trusted test inputs. Production adapters
must prove their provenance before applying the corresponding documented rules.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import sqlite3
import time
import unicodedata
import uuid
from typing import Callable


class Rejected(Exception):
    """A confirmed rejection with no domain mutation."""


class OutcomeUnknown(Exception):
    """Test fault after commit, before the caller observes the result."""


@dataclass(frozen=True)
class Principal:
    account_id: str
    character_id: str | None = None
    server_id: str = "zone-server.thornmere"
    epoch: int = 0
    trusted_server: bool = True


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def relationship(catalog: dict, first: str, second: str,
                 overrides: dict[tuple[str, str], int] | None = None) -> int:
    identifiers = {row["id"] for row in catalog["factions"]}
    if first not in identifiers or second not in identifiers:
        raise Rejected("UnknownFaction")
    if first == second:
        return catalog["relations"]["self_score"]
    key = tuple(sorted((first, second)))
    if overrides and key in overrides:
        value = overrides[key]
        if type(value) is not int or not -100 <= value <= 100:
            raise Rejected("InvalidRelationshipOverride")
        return value
    return next(row["score"] for row in catalog["relations"]["pairs"] if tuple(sorted(row["factions"])) == key)


def npc_access(catalog: dict, faction_id: str, npc_faction_id: str | None,
               *, standing: int = 0, pressure: int = 0, neutral: bool = False,
               guest: bool = False, hostility_zone: bool = False,
               service: str = "basic-trade", overrides: dict | None = None) -> dict:
    policy = catalog["policy"]
    if faction_id not in {row["id"] for row in catalog["factions"]}:
        raise Rejected("UnknownFaction")
    if neutral or npc_faction_id is None:
        return {"attitude": "neutral", "guard_can_attack": False, "service_allowed": not service.startswith("faction-only:") or faction_id == npc_faction_id}
    base = relationship(catalog, faction_id, npc_faction_id, overrides)
    personal = clamp(int(standing / policy["personal_modifier_divisor"]), -policy["personal_modifier_cap"], policy["personal_modifier_cap"])
    regional = clamp(int(pressure / policy["pressure_modifier_divisor"]), -policy["pressure_modifier_cap"], policy["pressure_modifier_cap"])
    score = clamp(base + personal + regional, -100, 100)
    attitude = "hostile"
    for label in ("friendly", "neutral", "wary"):
        if score >= policy["attitude_thresholds"][label]:
            attitude = label
            break
    can_attack = attitude == "hostile" and hostility_zone and not guest
    allowed = attitude != "hostile" or guest
    if service.startswith("faction-only:"):
        allowed = faction_id == npc_faction_id and not can_attack
    return {"attitude": attitude, "guard_can_attack": can_attack, "service_allowed": allowed}


class FactionModel:
    def __init__(self, database: str, catalog: dict, campaign: dict,
                 clock: Callable[[], int] | None = None) -> None:
        self.connection = sqlite3.connect(database, isolation_level=None, timeout=10)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.catalog = catalog
        self.campaign = campaign
        self.clock = clock or (lambda: int(time.time()))
        self.factions = {row["id"]: row for row in catalog["factions"]}
        self.quests = {row["id"]: row for row in campaign["quests"]}
        self.spawns = {row["id"]: row for row in campaign["spawns"]}
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY, slots INTEGER NOT NULL CHECK(slots>0));
        CREATE TABLE IF NOT EXISTS characters(
          id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
          name TEXT UNIQUE NOT NULL, faction_id TEXT, faction_version INTEGER NOT NULL,
          class_id TEXT NOT NULL, vocation_id TEXT NOT NULL, appearance_id TEXT NOT NULL,
          copper INTEGER NOT NULL CHECK(copper>=0), combat_xp INTEGER NOT NULL CHECK(combat_xp>=0),
          revision INTEGER NOT NULL CHECK(revision>=0), schema_version INTEGER NOT NULL,
          migration_state TEXT NOT NULL, zone_id TEXT NOT NULL, spawn_id TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS vocation_history(character_id TEXT REFERENCES characters(id), vocation_id TEXT,
          xp INTEGER NOT NULL, mastery INTEGER NOT NULL, PRIMARY KEY(character_id,vocation_id));
        CREATE TABLE IF NOT EXISTS inventory(character_id TEXT REFERENCES characters(id), item_id TEXT,
          quantity INTEGER NOT NULL CHECK(quantity>=0), PRIMARY KEY(character_id,item_id));
        CREATE TABLE IF NOT EXISTS standings(character_id TEXT REFERENCES characters(id), axis TEXT,
          subject_id TEXT, value INTEGER NOT NULL CHECK(value BETWEEN -1000 AND 1000),
          PRIMARY KEY(character_id,axis,subject_id));
        CREATE TABLE IF NOT EXISTS receipts(scope TEXT, operation TEXT, request_id TEXT,
          digest TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(scope,operation,request_id));
        CREATE TABLE IF NOT EXISTS domain_outcomes(character_id TEXT REFERENCES characters(id), source_id TEXT,
          generation INTEGER NOT NULL, PRIMARY KEY(character_id,source_id,generation));
        CREATE TABLE IF NOT EXISTS evidence(character_id TEXT REFERENCES characters(id), quest_id TEXT,
          objective_id TEXT, occurrence_id TEXT, units INTEGER NOT NULL CHECK(units>0),
          PRIMARY KEY(character_id,quest_id,objective_id,occurrence_id));
        CREATE TABLE IF NOT EXISTS quest_completion(character_id TEXT REFERENCES characters(id), quest_id TEXT,
          version INTEGER NOT NULL, branch_id TEXT, result TEXT NOT NULL,
          PRIMARY KEY(character_id,quest_id));
        CREATE TABLE IF NOT EXISTS leases(character_id TEXT PRIMARY KEY REFERENCES characters(id),
          server_id TEXT NOT NULL, epoch INTEGER NOT NULL, state TEXT NOT NULL, expires_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS work_orders(id TEXT PRIMARY KEY, character_id TEXT NOT NULL REFERENCES characters(id),
          marker_mask INTEGER NOT NULL DEFAULT 0, consumed INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS regions(id TEXT PRIMARY KEY, units INTEGER NOT NULL CHECK(units BETWEEN 0 AND 12),
          completed INTEGER NOT NULL, revision INTEGER NOT NULL, winner TEXT, pressure INTEGER NOT NULL DEFAULT 0);
        INSERT OR IGNORE INTO regions VALUES('elderwood',0,0,0,NULL,0);
        CREATE TABLE IF NOT EXISTS rounds(id TEXT PRIMARY KEY, version INTEGER NOT NULL, closes_at INTEGER NOT NULL,
          state TEXT NOT NULL, winner TEXT);
        CREATE TABLE IF NOT EXISTS ballots(round_id TEXT REFERENCES rounds(id), account_id TEXT REFERENCES accounts(id),
          character_id TEXT REFERENCES characters(id), option_id TEXT NOT NULL, PRIMARY KEY(round_id,account_id));
        CREATE TABLE IF NOT EXISTS transfers(id TEXT PRIMARY KEY, character_id TEXT REFERENCES characters(id),
          destination_zone TEXT NOT NULL, spawn_id TEXT NOT NULL, epoch INTEGER NOT NULL,
          token_hash TEXT UNIQUE NOT NULL, expires_at INTEGER NOT NULL, state TEXT NOT NULL,
          faction_version INTEGER NOT NULL, policy_version INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS outbox(sequence INTEGER PRIMARY KEY AUTOINCREMENT, aggregate_id TEXT NOT NULL,
          revision INTEGER NOT NULL, event_type TEXT NOT NULL, payload TEXT NOT NULL);
        """)

    def close(self) -> None:
        self.connection.close()

    def add_account(self, account_id: str, slots: int = 8) -> None:
        self.connection.execute("INSERT INTO accounts VALUES(?,?)", (account_id, slots))

    def character(self, character_id: str) -> dict:
        row = self.connection.execute("SELECT * FROM characters WHERE id=?", (character_id,)).fetchone()
        if row is None:
            raise Rejected("CharacterNotFound")
        return dict(row)

    def _owner(self, principal: Principal) -> dict | None:
        if not principal.trusted_server:
            raise Rejected("UntrustedCommandOrigin")
        if not self.connection.execute("SELECT 1 FROM accounts WHERE id=?", (principal.account_id,)).fetchone():
            raise Rejected("Unauthenticated")
        if principal.character_id is None:
            return None
        character = self.character(principal.character_id)
        if character["account_id"] != principal.account_id:
            raise Rejected("PermissionDenied")
        return character

    def _lease(self, principal: Principal) -> None:
        row = self.connection.execute("SELECT * FROM leases WHERE character_id=?", (principal.character_id,)).fetchone()
        if row is None or row["epoch"] != principal.epoch or row["state"] != "Active" or row["server_id"] != principal.server_id or row["expires_at"] <= self.clock():
            raise Rejected("StaleLease")

    def _execute(self, principal: Principal, operation: str, request_id: str,
                 payload: dict, effect: Callable[[], dict], *, require_lease: bool = True,
                 expected_revision: int | None = None, fault: str | None = None) -> dict:
        try:
            uuid.UUID(request_id)
        except (ValueError, TypeError, AttributeError) as exception:
            raise Rejected("InvalidRequestId") from exception
        scope = principal.character_id or principal.account_id
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            character = self._owner(principal)
            receipt = self.connection.execute("SELECT digest,result FROM receipts WHERE scope=? AND operation=? AND request_id=?", (scope, operation, request_id)).fetchone()
            if receipt is not None:
                if receipt["digest"] != digest:
                    raise Rejected("RequestIdentityConflict")
                self.connection.execute("COMMIT")
                return json.loads(receipt["result"])
            if require_lease:
                self._lease(principal)
            if expected_revision is not None and (character is None or character["revision"] != expected_revision):
                raise Rejected("StaleRevision")
            result = effect()
            self.connection.execute("INSERT INTO receipts VALUES(?,?,?,?,?)", (scope, operation, request_id, digest, json.dumps(result, sort_keys=True)))
            if fault == "before_commit":
                raise Rejected("InjectedBeforeCommit")
            self.connection.execute("COMMIT")
        except BaseException:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
            raise
        if fault == "after_commit":
            raise OutcomeUnknown("InjectedAfterCommit")
        return result

    def _changed(self, character_id: str, event_type: str) -> int:
        self.connection.execute("UPDATE characters SET revision=revision+1 WHERE id=?", (character_id,))
        revision = self.character(character_id)["revision"]
        self.connection.execute("INSERT INTO outbox(aggregate_id,revision,event_type,payload) VALUES(?,?,?,?)", (character_id, revision, event_type, json.dumps({"character_id": character_id, "revision": revision})))
        return revision

    def selectable_catalog(self) -> list[str]:
        return [row["id"] for row in self.catalog["factions"] if row["selection"]["selectable_for_new_character"]]

    def create_character(self, principal: Principal, request_id: str, payload: dict,
                         *, fault: str | None = None) -> dict:
        def effect() -> dict:
            allowed = {"name", "faction_id", "class_id", "vocation_id", "appearance_id", "catalog_version", "availability_revision"}
            if set(payload) != allowed:
                raise Rejected("InvalidCreationPayload")
            if payload["catalog_version"] != self.catalog["catalog_version"]:
                raise Rejected("ContentVersionMismatch")
            if payload["availability_revision"] != self.catalog["availability_revision"]:
                raise Rejected("AvailabilityChanged")
            for field in ["name", "faction_id", "class_id", "vocation_id", "appearance_id"]:
                if not isinstance(payload[field], str):
                    raise Rejected("InvalidCreationPayload")
            if type(payload["catalog_version"]) is not int or type(payload["availability_revision"]) is not int:
                raise Rejected("InvalidCreationPayload")
            faction = self.factions.get(payload["faction_id"])
            if faction is None:
                raise Rejected("FactionRequired" if not payload["faction_id"] else "UnknownFaction")
            if not faction["selection"]["selectable_for_new_character"]:
                raise Rejected("FactionUnavailable")
            if payload["class_id"] not in {"discipline.vanguard", "discipline.ranger", "discipline.arcanist", "discipline.warden"}:
                raise Rejected("CombatDisciplineUnavailable")
            if payload["vocation_id"] not in {"vocation.forgekeeper", "vocation.hearthkeeper", "vocation.wayfinder", "vocation.woodwright", "vocation.apothecary"}:
                raise Rejected("VocationUnavailable")
            if payload["appearance_id"] != faction["starter"]["outfit_id"]:
                raise Rejected("AppearanceUnavailable")
            name = unicodedata.normalize("NFKC", payload["name"]).strip()
            if not re.fullmatch(r"[A-Za-z][A-Za-z -]{1,22}[A-Za-z]", name) or name.casefold() in {"admin", "moderator"} or re.search(r"[ -]{2}", name):
                raise Rejected("InvalidName")
            name = name.casefold()
            if self.connection.execute("SELECT 1 FROM characters WHERE name=?", (name,)).fetchone():
                raise Rejected("NameUnavailable")
            count = self.connection.execute("SELECT COUNT(*) FROM characters WHERE account_id=?", (principal.account_id,)).fetchone()[0]
            slots = self.connection.execute("SELECT slots FROM accounts WHERE id=?", (principal.account_id,)).fetchone()[0]
            if count >= slots:
                raise Rejected("CharacterLimit")
            start = faction["start"]
            spawn = self.spawns.get(start["spawn_id"])
            if not spawn or not spawn["authored"] or not spawn["safe"] or faction["id"] not in spawn["allowed_factions"]:
                raise Rejected("StartingSpawnUnavailable")
            character_id = str(uuid.uuid4())
            self.connection.execute("INSERT INTO characters VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (character_id, principal.account_id, name, faction["id"], faction["content_version"], payload["class_id"], payload["vocation_id"], payload["appearance_id"], faction["starter"]["copper"], 0, 1, 3, "Ready", start["zone_id"], start["spawn_id"]))
            self.connection.execute("INSERT INTO vocation_history VALUES(?,?,0,0)", (character_id, payload["vocation_id"]))
            self.connection.execute("INSERT INTO inventory VALUES(?,?,1)", (character_id, faction["starter"]["item_id"]))
            self.connection.execute("INSERT INTO domain_outcomes VALUES(?,?,1)", (character_id, faction["starter"]["grant_source_id"]))
            for axis, values in faction["initial_reputation"].items():
                for subject_id, value in values.items():
                    self.connection.execute("INSERT INTO standings VALUES(?,?,?,?)", (character_id, axis, subject_id, value))
            self.connection.execute("INSERT INTO outbox(aggregate_id,revision,event_type,payload) VALUES(?,1,'CharacterCreated',?)", (character_id, json.dumps({"character_id": character_id})))
            return {"character_id": character_id, "faction_id": faction["id"], "spawn_id": start["spawn_id"], "revision": 1}
        if principal.character_id is not None:
            raise Rejected("CreationRequiresAccountScope")
        return self._execute(principal, "CreateCharacter", request_id, payload, effect, require_lease=False, fault=fault)

    def login(self, principal: Principal, request_id: str) -> dict:
        def effect() -> dict:
            character = self.character(principal.character_id)
            if character["schema_version"] < 3 or not character["faction_id"]:
                return {"state": "FactionMigrationRequired", "character_id": principal.character_id}
            faction = self.factions.get(character["faction_id"])
            if faction is None or faction["content_version"] != character["faction_version"]:
                return {"state": "ReviewedRecoveryRequired", "character_id": principal.character_id}
            prior = self.connection.execute("SELECT * FROM leases WHERE character_id=?", (principal.character_id,)).fetchone()
            if prior and prior["state"] == "InTransit":
                return {"state": "ResumeTransfer", "character_id": principal.character_id}
            epoch = prior["epoch"] + 1 if prior else 1
            spawn = self.spawns.get(character["spawn_id"])
            if not spawn or not spawn.get("authored") or not spawn.get("safe") or faction["id"] not in spawn.get("allowed_factions", []):
                fallback = self.spawns[faction["start"]["fallback_spawn_id"]]
                self.connection.execute("UPDATE characters SET zone_id=?,spawn_id=? WHERE id=?", (fallback["zone_id"], fallback["id"], principal.character_id))
                self._changed(principal.character_id, "SafePlacementRecovered")
            self.connection.execute("INSERT INTO leases VALUES(?,?,?,'Active',?) ON CONFLICT(character_id) DO UPDATE SET server_id=excluded.server_id,epoch=excluded.epoch,state=excluded.state,expires_at=excluded.expires_at", (principal.character_id, principal.server_id, epoch, self.clock()+300))
            return {"state": "Active", "epoch": epoch, "character_id": principal.character_id, "faction_id": faction["id"]}
        return self._execute(principal, "Login", request_id, {"server_id": principal.server_id}, effect, require_lease=False)

    def _quest(self, character_id: str, quest_id: str, version: int) -> dict:
        quest = self.quests.get(quest_id)
        if quest is None or quest["content_version"] != version:
            raise Rejected("ContentVersionMismatch")
        if self.character(character_id)["faction_id"] != quest["faction_id"]:
            raise Rejected("QuestFactionRestricted")
        for prerequisite in quest["prerequisites"]:
            if not self.connection.execute("SELECT 1 FROM quest_completion WHERE character_id=? AND quest_id=?", (character_id, prerequisite)).fetchone():
                raise Rejected("QuestPrerequisiteMissing")
        return quest

    def evidence(self, principal: Principal, request_id: str, quest_id: str,
                 objective_id: str, occurrence_id: str, expected_revision: int,
                 *, version: int = 1, source_id: str | None = None,
                 trusted_objective_receipt: bool = True) -> dict:
        """Consume a complete objective receipt, not raw UI clicks or enemy hits."""
        payload = {"quest_id": quest_id, "objective_id": objective_id, "occurrence_id": occurrence_id, "revision": expected_revision, "version": version, "source_id": source_id}
        def effect() -> dict:
            quest = self._quest(principal.character_id, quest_id, version)
            objective = next((row for row in quest["objectives"] if row["id"] == objective_id), None)
            if objective is None or not trusted_objective_receipt or source_id != objective["source_id"]:
                raise Rejected("InvalidObjectiveEvidence")
            if objective_id in {"objective.hearthward.contribution", "objective.hearthward.road-ready", "objective.hearthward.choice"}:
                raise Rejected("ObjectiveRequiresDomainCommand")
            existing = self.connection.execute("SELECT 1 FROM evidence WHERE character_id=? AND quest_id=? AND objective_id=? AND occurrence_id=?", (principal.character_id, quest_id, objective_id, occurrence_id)).fetchone()
            if existing:
                return {"duplicate_source": True, "revision": self.character(principal.character_id)["revision"]}
            self.connection.execute("INSERT INTO evidence VALUES(?,?,?,?,1)", (principal.character_id, quest_id, objective_id, occurrence_id))
            return {"revision": self._changed(principal.character_id, "ObjectiveEvidenceAccepted")}
        return self._execute(principal, "AcceptObjectiveReceipt", request_id, payload, effect, expected_revision=expected_revision)

    def _standing(self, character_id: str, axis: str, subject_id: str, delta: int) -> None:
        if type(delta) is not int:
            raise Rejected("InvalidReputationDelta")
        row = self.connection.execute("SELECT value FROM standings WHERE character_id=? AND axis=? AND subject_id=?", (character_id, axis, subject_id)).fetchone()
        if row is None:
            raise Rejected("UnknownReputationSubject")
        value = clamp(row["value"]+delta, self.catalog["policy"]["reputation_min"], self.catalog["policy"]["reputation_max"])
        self.connection.execute("UPDATE standings SET value=? WHERE character_id=? AND axis=? AND subject_id=?", (value, character_id, axis, subject_id))

    def complete_quest(self, principal: Principal, request_id: str, quest_id: str,
                       expected_revision: int, *, branch_id: str | None = None,
                       version: int = 1, in_interaction_range: bool = True,
                       fault: str | None = None) -> dict:
        payload = {"quest_id": quest_id, "branch_id": branch_id, "revision": expected_revision, "version": version}
        def effect() -> dict:
            quest = self._quest(principal.character_id, quest_id, version)
            if not in_interaction_range:
                raise Rejected("InteractionOutOfRange")
            completed = self.connection.execute("SELECT result,branch_id FROM quest_completion WHERE character_id=? AND quest_id=?", (principal.character_id, quest_id)).fetchone()
            if completed:
                if completed["branch_id"] != branch_id:
                    raise Rejected("CampaignChoiceImmutable")
                return json.loads(completed["result"])
            branch = None
            if quest["branches"]:
                branch = next((row for row in quest["branches"] if row["id"] == branch_id), None)
                if branch is None:
                    raise Rejected("BranchRequired")
            elif branch_id is not None:
                raise Rejected("UnexpectedBranch")
            for objective in quest["objectives"]:
                if objective["id"] == "objective.hearthward.choice" and branch:
                    continue
                if objective["id"] == "objective.hearthward.road-ready":
                    if not self.connection.execute("SELECT completed FROM regions WHERE id='elderwood'").fetchone()[0]:
                        raise Rejected("ProjectNotReady")
                    continue
                count = self.connection.execute("SELECT COALESCE(SUM(units),0) FROM evidence WHERE character_id=? AND quest_id=? AND objective_id=?", (principal.character_id, quest_id, objective["id"])).fetchone()[0]
                if count < objective["required_units"]:
                    raise Rejected("ObjectiveIncomplete")
            reward = quest["reward"]
            self.connection.execute("INSERT INTO domain_outcomes VALUES(?,?,?)", (principal.character_id, reward["source_id"], reward["claim_generation"]))
            self.connection.execute("UPDATE characters SET copper=copper+?,combat_xp=combat_xp+? WHERE id=?", (reward["copper"], reward["combat_xp"], principal.character_id))
            for item in reward["items"]:
                self.connection.execute("INSERT INTO inventory VALUES(?,?,?) ON CONFLICT(character_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (principal.character_id, item["item_id"], item["quantity"]))
            for changes in [reward] + ([branch] if branch else []):
                for axis, field in [("factions", "faction_reputation"), ("organizations", "organization_reputation")]:
                    for subject_id, delta in changes.get(field, {}).items():
                        self._standing(principal.character_id, axis, subject_id, delta)
            result = {"quest_id": quest_id, "branch_id": branch_id, "reward_source_id": reward["source_id"], "revision": self._changed(principal.character_id, "QuestCommitted")}
            self.connection.execute("INSERT INTO quest_completion VALUES(?,?,?,?,?)", (principal.character_id, quest_id, version, branch_id, json.dumps(result)))
            return result
        return self._execute(principal, "CompleteQuest", request_id, payload, effect, expected_revision=expected_revision, fault=fault)

    def open_work_order(self, principal: Principal, request_id: str, expected_revision: int) -> dict:
        def effect() -> dict:
            self._quest(principal.character_id, "quest.hearthward.north-road-compact", 1)
            if self.connection.execute("SELECT 1 FROM work_orders WHERE character_id=? AND consumed=0", (principal.character_id,)).fetchone():
                raise Rejected("WorkOrderAlreadyOpen")
            order_id = str(uuid.uuid4())
            self.connection.execute("INSERT INTO work_orders(id,character_id) VALUES(?,?)", (order_id, principal.character_id))
            return {"work_order_id": order_id, "revision": self._changed(principal.character_id, "WorkOrderOpened")}
        return self._execute(principal, "OpenWorkOrder", request_id, {"revision": expected_revision}, effect, expected_revision=expected_revision)

    def visit_work_marker(self, principal: Principal, request_id: str, order_id: str,
                          marker_index: int, expected_revision: int, *, in_range: bool = True) -> dict:
        def effect() -> dict:
            order = self.connection.execute("SELECT * FROM work_orders WHERE id=?", (order_id,)).fetchone()
            if order is None or order["character_id"] != principal.character_id or order["consumed"] or marker_index not in (0,1,2) or not in_range:
                raise Rejected("InvalidWorkEvidence")
            self.connection.execute("UPDATE work_orders SET marker_mask=marker_mask|? WHERE id=?", (1 << marker_index, order_id))
            return {"revision": self._changed(principal.character_id, "WorkMarkerRecorded")}
        return self._execute(principal, "VisitWorkMarker", request_id, {"order_id": order_id, "marker_index": marker_index, "revision": expected_revision}, effect, expected_revision=expected_revision)

    def contribute(self, principal: Principal, request_id: str, order_id: str,
                   expected_revision: int, expected_region_revision: int,
                   *, fault: str | None = None) -> dict:
        def effect() -> dict:
            self._quest(principal.character_id, "quest.hearthward.north-road-compact", 1)
            order = self.connection.execute("SELECT * FROM work_orders WHERE id=?", (order_id,)).fetchone()
            if order is None or order["character_id"] != principal.character_id or order["consumed"] or order["marker_mask"] != 7:
                raise Rejected("InvalidWorkOrder")
            region = self.connection.execute("SELECT * FROM regions WHERE id='elderwood'").fetchone()
            if region["revision"] != expected_region_revision:
                raise Rejected("StaleRegionRevision")
            units = min(12, region["units"]+3)
            self.connection.execute("UPDATE work_orders SET consumed=1 WHERE id=?", (order_id,))
            self.connection.execute("INSERT INTO evidence VALUES(?,?,?, ?,3)", (principal.character_id, "quest.hearthward.north-road-compact", "objective.hearthward.contribution", order_id))
            self.connection.execute("UPDATE regions SET units=?,completed=?,revision=revision+1 WHERE id='elderwood'", (units, int(units == 12)))
            self.connection.execute("INSERT INTO outbox(aggregate_id,revision,event_type,payload) VALUES('elderwood',?,'RegionContributionCommitted',?)", (region["revision"]+1, json.dumps({"units": units, "completed": units == 12})))
            return {"units": 3, "maintenance": bool(region["completed"]), "region_revision": region["revision"]+1, "revision": self._changed(principal.character_id, "ProjectContributionCommitted")}
        return self._execute(principal, "ContributeWorkOrder", request_id, {"order_id": order_id, "revision": expected_revision, "region_revision": expected_region_revision}, effect, expected_revision=expected_revision, fault=fault)

    def open_round(self, round_id: str) -> None:
        policy = self.catalog["policy"]["resolution"]
        self.connection.execute("INSERT INTO rounds VALUES(?,?,?,'Open',NULL)", (round_id, self.catalog["policy"]["version"], self.clock()+policy["round_duration_seconds"]))

    def cast_ballot(self, principal: Principal, request_id: str, round_id: str,
                    option_id: str, expected_revision: int) -> dict:
        def effect() -> dict:
            row = self.connection.execute("SELECT * FROM rounds WHERE id=?", (round_id,)).fetchone()
            if row is None or row["state"] != "Open" or row["closes_at"] <= self.clock():
                raise Rejected("RoundClosed")
            if row["version"] != self.catalog["policy"]["version"]:
                raise Rejected("PolicyVersionMismatch")
            if option_id not in self.catalog["policy"]["resolution"]["options"]:
                raise Rejected("InvalidPolicyOption")
            if not self.connection.execute("SELECT 1 FROM quest_completion WHERE character_id=? AND quest_id='quest.hearthward.crossing-choice'", (principal.character_id,)).fetchone():
                raise Rejected("BallotNotEligible")
            if self.connection.execute("SELECT 1 FROM ballots WHERE round_id=? AND account_id=?", (round_id, principal.account_id)).fetchone():
                raise Rejected("AccountAlreadyVoted")
            self.connection.execute("INSERT INTO ballots VALUES(?,?,?,?)", (round_id, principal.account_id, principal.character_id, option_id))
            return {"option_id": option_id, "revision": self._changed(principal.character_id, "BallotAccepted")}
        return self._execute(principal, "CastBallot", request_id, {"round_id": round_id, "option_id": option_id, "revision": expected_revision}, effect, expected_revision=expected_revision)

    def resolve_round(self, round_id: str) -> str:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute("SELECT * FROM rounds WHERE id=?", (round_id,)).fetchone()
            if row is None or row["closes_at"] > self.clock():
                raise Rejected("RoundStillOpen")
            if row["state"] == "Resolved":
                self.connection.execute("COMMIT")
                return row["winner"]
            if row["version"] != self.catalog["policy"]["version"]:
                raise Rejected("PolicyVersionMismatch")
            counts = dict(self.connection.execute("SELECT option_id,COUNT(*) FROM ballots WHERE round_id=? GROUP BY option_id", (round_id,)).fetchall())
            options = self.catalog["policy"]["resolution"]["options"]
            maximum = max((counts.get(option, 0) for option in options), default=0)
            winners = [option for option in options if counts.get(option, 0) == maximum]
            winner = winners[0] if len(winners) == 1 else self.catalog["policy"]["resolution"]["tie_break"]
            self.connection.execute("UPDATE rounds SET state='Resolved',winner=? WHERE id=?", (winner, round_id))
            pressure = 10 if winner == "fortified-crossing" else -10
            self.connection.execute("UPDATE regions SET winner=?,pressure=MAX(-100,MIN(100,pressure+?)),revision=revision+1 WHERE id='elderwood'", (winner, pressure))
            region_revision = self.connection.execute("SELECT revision FROM regions WHERE id='elderwood'").fetchone()[0]
            self.connection.execute("INSERT INTO outbox(aggregate_id,revision,event_type,payload) VALUES('elderwood',?,'PolicyRoundResolved',?)", (region_revision, json.dumps({"round_id": round_id, "winner": winner})))
            self.connection.execute("COMMIT")
            return winner
        except BaseException:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
            raise

    def begin_transfer(self, principal: Principal, request_id: str, expected_revision: int,
                       *, fault: str | None = None) -> dict:
        issued_ticket = None
        def effect() -> dict:
            nonlocal issued_ticket
            final_quest = self.campaign["quests"][-1]["id"]
            if not self.connection.execute("SELECT 1 FROM quest_completion WHERE character_id=? AND quest_id=?", (principal.character_id, final_quest)).fetchone():
                raise Rejected("TravelNotUnlocked")
            spawn_id = self.campaign["quests"][-1]["follow_up"]["travel_spawn_id"]
            spawn = self.spawns.get(spawn_id)
            character = self.character(principal.character_id)
            if not spawn or not spawn["safe"] or character["faction_id"] not in spawn["allowed_factions"]:
                raise Rejected("DestinationUnavailable")
            transfer_id, ticket = str(uuid.uuid4()), str(uuid.uuid4())
            issued_ticket = ticket
            epoch = principal.epoch+1
            self.connection.execute("INSERT INTO transfers VALUES(?,?,?,?,?,?,?,'Fenced',?,?)", (transfer_id, principal.character_id, spawn["zone_id"], spawn_id, epoch, hashlib.sha256(ticket.encode()).hexdigest(), self.clock()+60, character["faction_version"], self.catalog["policy"]["version"]))
            self.connection.execute("UPDATE leases SET epoch=?,state='InTransit' WHERE character_id=?", (epoch, principal.character_id))
            return {"transfer_id": transfer_id, "epoch": epoch}
        result = self._execute(principal, "BeginTransfer", request_id, {"revision": expected_revision, "destination": "elderwood-common"}, effect, expected_revision=expected_revision, fault=fault)
        return dict(result, ticket=issued_ticket) if issued_ticket else result

    def activate_transfer(self, principal: Principal, request_id: str, transfer_id: str,
                          ticket: str, *, fault: str | None = None) -> dict:
        def effect() -> dict:
            row = self.connection.execute("SELECT * FROM transfers WHERE id=?", (transfer_id,)).fetchone()
            if row is None or row["character_id"] != principal.character_id or row["token_hash"] != hashlib.sha256(ticket.encode()).hexdigest():
                raise Rejected("InvalidTransferTicket")
            if row["state"] != "Fenced" or row["expires_at"] <= self.clock():
                raise Rejected("TransferTerminalOrExpired")
            if principal.server_id != "zone-server.elderwood":
                raise Rejected("WrongDestinationServer")
            character = self.character(principal.character_id)
            lease = self.connection.execute("SELECT * FROM leases WHERE character_id=?", (principal.character_id,)).fetchone()
            if lease["epoch"] != row["epoch"] or lease["state"] != "InTransit" or character["faction_version"] != row["faction_version"] or self.catalog["policy"]["version"] != row["policy_version"]:
                raise Rejected("TransferVersionOrEpochMismatch")
            spawn = self.spawns.get(row["spawn_id"])
            if not spawn or not spawn["safe"] or not spawn["authored"] or character["faction_id"] not in spawn["allowed_factions"]:
                raise Rejected("DestinationUnavailable")
            self.connection.execute("UPDATE transfers SET state='Activated' WHERE id=?", (transfer_id,))
            self.connection.execute("UPDATE leases SET state='Active',server_id=?,expires_at=? WHERE character_id=?", (principal.server_id, self.clock()+300, principal.character_id))
            self.connection.execute("UPDATE characters SET zone_id=?,spawn_id=? WHERE id=?", (row["destination_zone"], row["spawn_id"], principal.character_id))
            return {"epoch": row["epoch"], "spawn_id": row["spawn_id"], "revision": self._changed(principal.character_id, "TransferActivated")}
        return self._execute(principal, "ActivateTransfer", request_id, {"transfer_id": transfer_id, "ticket_hash": hashlib.sha256(ticket.encode()).hexdigest()}, effect, require_lease=False, fault=fault)

    def expire_transfer(self, principal: Principal, request_id: str, transfer_id: str) -> dict:
        def effect() -> dict:
            row = self.connection.execute("SELECT * FROM transfers WHERE id=?", (transfer_id,)).fetchone()
            if row is None or row["character_id"] != principal.character_id:
                raise Rejected("InvalidTransfer")
            if row["state"] != "Fenced" or row["expires_at"] > self.clock():
                raise Rejected("TransferCannotExpire")
            lease = self.connection.execute("SELECT * FROM leases WHERE character_id=?", (principal.character_id,)).fetchone()
            if lease["epoch"] != row["epoch"] or lease["state"] != "InTransit":
                raise Rejected("StaleTransferEpoch")
            character = self.character(principal.character_id)
            spawn = self.spawns[self.factions[character["faction_id"]]["start"]["fallback_spawn_id"]]
            epoch = row["epoch"]+1
            self.connection.execute("UPDATE transfers SET state='Expired' WHERE id=?", (transfer_id,))
            self.connection.execute("UPDATE leases SET epoch=?,state='Active',server_id='zone-server.thornmere',expires_at=? WHERE character_id=?", (epoch, self.clock()+300, principal.character_id))
            self.connection.execute("UPDATE characters SET zone_id=?,spawn_id=? WHERE id=?", (spawn["zone_id"], spawn["id"], principal.character_id))
            return {"epoch": epoch, "revision": self._changed(principal.character_id, "TransferRecovered")}
        return self._execute(principal, "ExpireTransfer", request_id, {"transfer_id": transfer_id}, effect, require_lease=False)

    def migrate_legacy(self, principal: Principal, request_id: str, selected_faction_id: str,
                       expected_revision: int, *, explicit_confirmation: bool) -> dict:
        def effect() -> dict:
            character = self.character(principal.character_id)
            if character["faction_id"] is not None:
                raise Rejected("FactionImmutableOrNeedsAdminReview")
            if character["schema_version"] != 2 or not explicit_confirmation:
                raise Rejected("ExplicitLegacySelectionRequired")
            faction = self.factions.get(selected_faction_id)
            if faction is None or not faction["selection"]["selectable_for_new_character"]:
                raise Rejected("FactionUnavailable")
            fallback = self.spawns[faction["start"]["fallback_spawn_id"]]
            self.connection.execute("UPDATE characters SET faction_id=?,faction_version=?,schema_version=3,migration_state='Ready',zone_id=?,spawn_id=? WHERE id=?", (selected_faction_id, faction["content_version"], fallback["zone_id"], fallback["id"], principal.character_id))
            for axis, values in faction["initial_reputation"].items():
                for subject_id, value in values.items():
                    self.connection.execute("INSERT OR IGNORE INTO standings VALUES(?,?,?,?)", (principal.character_id, axis, subject_id, value))
            return {"faction_id": selected_faction_id, "revision": self._changed(principal.character_id, "LegacyFactionConfirmed")}
        return self._execute(principal, "ConfirmLegacyFaction", request_id, {"faction_id": selected_faction_id, "revision": expected_revision, "explicit_confirmation": explicit_confirmation}, effect, require_lease=False, expected_revision=expected_revision)

    def public_snapshot(self, character_id: str) -> dict:
        character = self.character(character_id)
        return {key: character[key] for key in ["id", "name", "faction_id", "class_id", "vocation_id", "appearance_id", "revision"]}
