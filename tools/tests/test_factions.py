"""Authored-source and SQLite conformance tests; no Unreal or connected clients."""
from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validate_factions import load_sources, validate
from faction_model import FactionModel, OutcomeUnknown, Principal, Rejected, npc_access, relationship


def request_id(label: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'briarwake-faction-test:' + label))


def configure_synthetic_campaign(catalog: dict, campaign: dict, fixtures: list[dict]) -> None:
    for fixture in fixtures:
        faction = next(row for row in catalog['factions'] if row['id'] == fixture['id'])
        faction['selection']['selectable_for_new_character'] = True
        faction['start'].update(map_id=fixture['map_id'], spawn_id=fixture['spawn_id'])
        faction['story'].update(root_quest_id=fixture['root_quest_id'], mentor_id=fixture['mentor_id'], cast_ids=[fixture['mentor_id']], authored=True)
        faction['readiness'].update(authored_specification=True, blocking_content=[])
        campaign['spawns'].append({'id': fixture['spawn_id'], 'zone_id': faction['start']['zone_id'], 'map_id': fixture['map_id'], 'tile': [1, 1], 'authored': True, 'safe': True, 'allowed_factions': [fixture['id']]})
        campaign['npcs'].append({'id': fixture['mentor_id'], 'faction_id': fixture['id'], 'organization_id': None, 'authored': True, 'map_id': fixture['map_id']})
        quest = copy.deepcopy(campaign['quests'][0])
        quest.update(id=fixture['root_quest_id'], faction_id=fixture['id'], map_id=fixture['map_id'], quest_giver_id=fixture['mentor_id'], turn_in_npc_id=fixture['mentor_id'], prerequisites=[], next_quest_ids=[], branches=[])
        objective_id = fixture['root_quest_id'] + '.objective'
        quest['objectives'] = [{'id': objective_id, 'source_id': fixture['root_quest_id'] + '.source', 'required_units': 1}]
        quest['reward'] = {'source_id': fixture['root_quest_id'] + '.reward', 'combat_xp': 5, 'copper': 0, 'vocation_xp': 0, 'items': [], 'faction_reputation': {fixture['id']: 1}, 'organization_reputation': {}, 'claim_generation': 1}
        quest['dialogue'] = [{'id': fixture['root_quest_id'] + '.dialogue', 'text_key': fixture['root_quest_id'] + '.line', 'text': 'Synthetic test witness; not authored production story.', 'choices': []}]
        campaign['quests'].append(quest)
        campaign['objective_rules'].append({'quest_id': quest['id'], 'expression': 'One trusted synthetic mentor interaction.'})


class FactionSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.campaign = load_sources(ROOT.parent)

    def test_authored_catalog_and_campaign(self) -> None:
        self.assertEqual([], validate(self.catalog, self.campaign))

    def test_only_hearthward_selectable(self) -> None:
        enabled = [row['id'] for row in self.catalog['factions'] if row['selection']['selectable_for_new_character']]
        self.assertEqual(['faction.hearthward-league'], enabled)
        self.assertEqual(4, len(self.catalog['factions']))

    def test_duplicate_faction_id_rejected(self) -> None:
        self.catalog['factions'].append(copy.deepcopy(self.catalog['factions'][0]))
        self.assertTrue(any('duplicate ID' in error for error in validate(self.catalog, self.campaign)))

    def test_taxonomy_has_three_independent_organizations(self) -> None:
        self.assertEqual({'organization.roadward-accord', 'organization.hearth-assembly', 'organization.veil-survey'}, {row['id'] for row in self.catalog['organizations']})
        self.assertEqual('enemy.hollow-covenant', self.catalog['enemies'][0]['id'])
        self.catalog['factions'][0]['kind'] = 'independent_organization'
        self.assertTrue(any('Taxonomy' in error for error in validate(self.catalog, self.campaign)))

    def test_base_relations_are_symmetric_and_complete(self) -> None:
        for first, second in itertools.product([row['id'] for row in self.catalog['factions']], repeat=2):
            self.assertEqual(relationship(self.catalog, first, second), relationship(self.catalog, second, first))
        self.catalog['relations']['pairs'].pop()
        self.assertTrue(any('matrix is incomplete' in error for error in validate(self.catalog, self.campaign)))

    def test_reverse_duplicate_relation_rejected(self) -> None:
        row = copy.deepcopy(self.catalog['relations']['pairs'][0])
        row['factions'].reverse()
        row['score'] = 80
        self.catalog['relations']['pairs'].append(row)
        self.assertTrue(any('Duplicate/asymmetric' in error for error in validate(self.catalog, self.campaign)))

    def test_future_faction_cannot_be_enabled_without_content(self) -> None:
        for index in [1,2,3]:
            changed = copy.deepcopy(self.catalog)
            changed['factions'][index]['selection']['selectable_for_new_character'] = True
            errors = validate(changed, self.campaign)
            self.assertTrue(any('root quest' in error for error in errors))
            self.assertTrue(any('NPC cast' in error for error in errors))
            self.assertTrue(any('safe spawn' in error for error in errors))

    def test_continuation_is_independent_of_new_selection(self) -> None:
        self.catalog['factions'][0]['selection']['selectable_for_new_character'] = False
        self.catalog['factions'][0]['selection']['locked_reason_key'] = 'Faction.PauseNewCharacters'
        self.assertEqual([], validate(self.catalog, self.campaign))
        self.catalog['factions'][0]['selection']['existing_character_continuation'] = 'deny'
        self.assertTrue(any('continuity' in error for error in validate(self.catalog, self.campaign)))

    def test_missing_spawn_npc_recipe_reward_and_travel_rejected(self) -> None:
        for collection in ['spawns','npcs','recipes','items']:
            campaign = copy.deepcopy(self.campaign)
            campaign[collection] = []
            self.assertTrue(validate(self.catalog, campaign), collection)
        self.campaign['quests'][-1]['follow_up']['travel_spawn_id'] = 'spawn.missing.destination'
        self.assertTrue(any('onward travel' in error for error in validate(self.catalog, self.campaign)))

    def test_quest_dag_cycle_and_orphan_rejected(self) -> None:
        self.campaign['quests'][-1]['next_quest_ids'].append(self.campaign['root_quest_id'])
        self.campaign['quests'][0]['prerequisites'].append(self.campaign['quests'][-1]['id'])
        self.assertTrue(any('Quest cycle' in error for error in validate(self.catalog, self.campaign)))
        self.campaign['root_quest_id'] = self.campaign['quests'][-1]['id']
        self.campaign['quests'][-1]['next_quest_ids'] = []
        self.campaign['quests'][0]['prerequisites'] = []
        self.campaign['quests'][0]['next_quest_ids'] = []
        self.campaign['quests'][1]['prerequisites'] = []
        self.assertTrue(any('unreachable' in error for error in validate(self.catalog, self.campaign)))

    def test_content_version_mismatch_rejected(self) -> None:
        self.campaign['quests'][2]['content_version'] = 2
        self.assertTrue(any('Content-version mismatch' in error for error in validate(self.catalog, self.campaign)))

    def test_branch_advancement_parity(self) -> None:
        branches = self.campaign['quests'][4]['branches']
        self.assertEqual(2, len(branches))
        self.assertEqual({1}, {branch['mechanical_reward_tier'] for branch in branches})
        branches[1]['next_quest_id'] = 'quest.missing.branch'
        self.assertTrue(any('parity' in error for error in validate(self.catalog, self.campaign)))

    def test_no_mandatory_pvp_or_group(self) -> None:
        for field, value in [('pvp_required',True),('party_required',True),('minimum_humans',2)]:
            campaign = copy.deepcopy(self.campaign)
            campaign['quests'][0][field] = value
            self.assertTrue(any('PvP/group' in error for error in validate(self.catalog, campaign)))
        self.catalog['policy']['open_world_player_damage'] = True
        self.assertTrue(any('player damage' in error for error in validate(self.catalog, self.campaign)))

    def test_neutral_services_and_no_player_damage(self) -> None:
        first, second = [row['id'] for row in self.catalog['factions'][:2]]
        decision = npc_access(self.catalog, first, second, standing=-1000, pressure=-100, neutral=True, hostility_zone=True)
        self.assertTrue(decision['service_allowed'])
        self.assertFalse(decision['guard_can_attack'])
        hostile = npc_access(self.catalog, first, second, standing=-1000, pressure=-100, hostility_zone=True)
        self.assertTrue(hostile['guard_can_attack'])
        guest = npc_access(self.catalog, first, second, standing=-1000, pressure=-100, guest=True, hostility_zone=True)
        self.assertFalse(guest['guard_can_attack'])
        self.assertTrue(guest['service_allowed'])
        self.assertFalse(self.catalog['policy']['open_world_player_damage'])

    def test_headquarters_restriction_and_override_symmetry(self) -> None:
        first, second = [row['id'] for row in self.catalog['factions'][:2]]
        key = tuple(sorted((first, second)))
        overrides = {key:80}
        self.assertEqual(80, relationship(self.catalog, second, first, overrides))
        self.assertFalse(npc_access(self.catalog, first, second, guest=True, service='faction-only:armory', overrides=overrides)['service_allowed'])
        with self.assertRaises(Rejected):
            relationship(self.catalog, first, second, {key:101})
        with self.assertRaises(Rejected):
            npc_access(self.catalog, 'faction.unknown', None, neutral=True)

    def test_four_facing_and_deployment_evidence_gate(self) -> None:
        self.assertTrue(any('Deployment blocked' in error for error in validate(self.catalog, self.campaign, deployment=True)))
        self.catalog['factions'][0]['starter']['facing_count'] = 8
        self.assertTrue(any('art requirement' in error for error in validate(self.catalog, self.campaign)))

    def test_region_permanence_and_free_solo_contract(self) -> None:
        self.assertEqual(12, self.campaign['project']['essential_target'])
        self.catalog['policy']['resolution']['essential_progress_requires_winner'] = True
        self.assertTrue(any('core progress' in error for error in validate(self.catalog, self.campaign)))
        for quest in self.campaign['quests']:
            quest['contribution_routes'] = [route for route in quest.get('contribution_routes',[]) if route.get('vocation_id')]
        self.assertTrue(any('profession-neutral' in error for error in validate(self.catalog, self.campaign)))

    def test_missing_recipe_input_and_invalid_standing_subject(self) -> None:
        self.campaign['recipes'][0]['inputs'][0]['id'] = 'item.unknown'
        self.assertTrue(any('recipe input' in error for error in validate(self.catalog, self.campaign)))
        self.campaign['quests'][0]['reward']['faction_reputation']['organization.hearth-assembly'] = 10
        self.assertTrue(any('reputation reward' in error for error in validate(self.catalog, self.campaign)))

    def test_missing_objective_rule_and_broken_dialogue(self) -> None:
        self.campaign['objective_rules'].pop()
        self.campaign['quests'][0]['dialogue'][0]['continue_to'] = 'dialogue.missing'
        errors = validate(self.catalog, self.campaign)
        self.assertTrue(any('objective rule' in error for error in errors))
        self.assertTrue(any('dialogue continuation' in error for error in errors))

    def test_neutral_zone_does_not_bypass_faction_only_service(self) -> None:
        decision = npc_access(self.catalog, self.catalog['factions'][0]['id'], self.catalog['factions'][1]['id'], neutral=True, service='faction-only:headquarters')
        self.assertFalse(decision['service_allowed'])
        self.assertFalse(decision['guard_can_attack'])

    def test_asset_rewards_are_generated_from_canonical_campaign(self) -> None:
        from faction_manual import faction_properties
        manifest = json.loads((ROOT.parent / 'sources/current-asset-manifest.json').read_text())
        asset = next(row for row in manifest['assets'] if row['name'] == 'DA_Quest_OathRoad')
        with tempfile.TemporaryDirectory() as directory:
            source_directory = Path(directory) / 'sources'
            source_directory.mkdir()
            self.campaign['quests'][0]['reward']['copper'] = 37
            (source_directory / 'hearthward-campaign.json').write_text(json.dumps(self.campaign))
            rows = faction_properties(asset, Path(directory))
            reward = next(row[2] for row in rows if row[0] == 'Reward / source guard')
            self.assertEqual(37, json.loads(reward.strip('`'))['copper'])

    def test_traceability_targets_and_phase_assignments_exist(self) -> None:
        trace = json.loads((ROOT.parent / 'sources/faction-traceability.json').read_text())
        manifest = json.loads((ROOT.parent / 'sources/current-asset-manifest.json').read_text())
        assets = {asset['name'] for asset in manifest['assets']}
        pages = {page['path'] for page in json.loads((ROOT.parent / 'sources/manual-pages.json').read_text())['pages']}
        self.assertEqual(72, len(trace['requirements']))
        self.assertEqual(72, len({row['id'] for row in trace['requirements']}))
        for requirement in trace['requirements']:
            self.assertTrue(set(requirement['assets']) <= assets, requirement['id'])
            self.assertTrue(set(requirement['pages']) <= pages, requirement['id'])
            self.assertTrue(all(0 <= phase <= 31 for phase in requirement['phases']))
            self.assertEqual('not_run', requirement['runtime_status'])
            for source in requirement['sources']:
                filename, separator, pointer = source.partition('#')
                path = ROOT.parent / filename
                self.assertTrue(path.is_file(), source)
                if separator:
                    value = json.loads(path.read_text())
                    for part in pointer.strip('/').split('/'):
                        part = part.replace('~1', '/').replace('~0', '~')
                        value = value[int(part)] if isinstance(value, list) else value[part]


class FactionTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.campaign = load_sources(ROOT.parent)
        self.directory = tempfile.TemporaryDirectory()
        self.database = str(Path(self.directory.name) / 'conformance.sqlite')
        self.now = 1000
        self.store = FactionModel(self.database, self.catalog, self.campaign, lambda:self.now)
        self.store.add_account('account.test')
        self.counter = 0

    def tearDown(self) -> None:
        self.store.close()
        self.directory.cleanup()

    def request(self) -> str:
        self.counter += 1
        return request_id(f'{self.id()}:{self.counter}')

    def payload(self, name: str = 'Maren Test', faction_id: str = 'faction.hearthward-league') -> dict:
        return {'name':name,'faction_id':faction_id,'class_id':'discipline.vanguard','vocation_id':'vocation.hearthkeeper','appearance_id':'appearance.starter.common-four-facing','catalog_version':1,'availability_revision':1}

    def create(self, name: str = 'Maren Test', account_id: str = 'account.test') -> Principal:
        result = self.store.create_character(Principal(account_id), self.request(), self.payload(name))
        principal = Principal(account_id,result['character_id'])
        lease = self.store.login(principal,self.request())
        return Principal(account_id,result['character_id'],epoch=lease['epoch'])

    def revision(self, principal: Principal) -> int:
        return self.store.character(principal.character_id)['revision']

    def give_evidence(self, principal: Principal, quest: dict) -> None:
        for objective in quest['objectives']:
            if objective['id'] in {'objective.hearthward.contribution','objective.hearthward.road-ready','objective.hearthward.choice'}:
                continue
            self.store.evidence(principal,self.request(),quest['id'],objective['id'],f"source-occurrence:{quest['id']}:{objective['id']}",self.revision(principal),source_id=objective['source_id'])

    def work(self, principal: Principal) -> str:
        result = self.store.open_work_order(principal,self.request(),self.revision(principal))
        order_id = result['work_order_id']
        for marker in range(3):
            self.store.visit_work_marker(principal,self.request(),order_id,marker,self.revision(principal))
        return order_id

    def contribute(self, principal: Principal, order_id: str, **kwargs) -> dict:
        region_revision = self.store.connection.execute("SELECT revision FROM regions WHERE id='elderwood'").fetchone()[0]
        return self.store.contribute(principal,self.request(),order_id,self.revision(principal),region_revision,**kwargs)

    def progress(self, principal: Principal, through: int = 6, branch_id: str = 'shared-passage') -> None:
        for index, quest in enumerate(self.campaign['quests'][:through]):
            if self.store.connection.execute('SELECT 1 FROM quest_completion WHERE character_id=? AND quest_id=?',(principal.character_id,quest['id'])).fetchone():
                continue
            self.give_evidence(principal,quest)
            if index == 3:
                # One personal work order remains required even after public completion.
                self.contribute(principal,self.work(principal))
                while not self.store.connection.execute("SELECT completed FROM regions WHERE id='elderwood'").fetchone()[0]:
                    self.contribute(principal,self.work(principal))
            self.store.complete_quest(principal,self.request(),quest['id'],self.revision(principal),branch_id=branch_id if quest['branches'] else None)

    def test_atomic_creation_replay_and_starter_once(self) -> None:
        identity = self.request()
        payload = self.payload()
        result = self.store.create_character(Principal('account.test'),identity,payload)
        self.assertEqual(result,self.store.create_character(Principal('account.test'),identity,payload))
        self.assertEqual(1,self.store.connection.execute('SELECT COUNT(*) FROM characters').fetchone()[0])
        self.assertEqual(1,self.store.connection.execute('SELECT SUM(quantity) FROM inventory').fetchone()[0])
        self.assertEqual(1,self.store.connection.execute('SELECT COUNT(*) FROM vocation_history').fetchone()[0])
        self.assertEqual(0,self.store.connection.execute('SELECT xp FROM vocation_history').fetchone()[0])
        payload['name']='Different Name'
        with self.assertRaisesRegex(Rejected,'RequestIdentityConflict'):
            self.store.create_character(Principal('account.test'),identity,payload)

    def test_creation_forgery_and_disabled_factions_leave_no_mutation(self) -> None:
        for identifier in [None,'faction.fake','organization.hearth-assembly','enemy.hollow-covenant'] + [row['id'] for row in self.catalog['factions'][1:]]:
            with self.assertRaises(Rejected):
                self.store.create_character(Principal('account.test'),self.request(),self.payload(faction_id=identifier))
        payload=self.payload(); payload['spawn_id']='spawn.elderwood.briarbound-sanctuary'
        with self.assertRaises(Rejected):
            self.store.create_character(Principal('account.test'),self.request(),payload)
        self.assertEqual(0,self.store.connection.execute('SELECT COUNT(*) FROM characters').fetchone()[0])
        self.assertEqual(0,self.store.connection.execute('SELECT COUNT(*) FROM receipts').fetchone()[0])

    def test_creation_validation_name_class_vocation_appearance_and_versions(self) -> None:
        for key,value in [('name','a'),('name','Admin'),('class_id',None),('vocation_id',None),('appearance_id','unapproved'),('catalog_version',2),('availability_revision',2)]:
            payload=self.payload(); payload[key]=value
            with self.assertRaises(Rejected,msg=key):
                self.store.create_character(Principal('account.test'),self.request(),payload)
        self.create()
        with self.assertRaisesRegex(Rejected,'NameUnavailable'):
            self.store.create_character(Principal('account.test'),self.request(),self.payload('MAREN TEST'))

    def test_slot_constraint(self) -> None:
        self.store.connection.execute("UPDATE accounts SET slots=1 WHERE id='account.test'")
        self.create()
        with self.assertRaisesRegex(Rejected,'CharacterLimit'):
            self.store.create_character(Principal('account.test'),self.request(),self.payload('Another Name'))

    def test_create_fault_before_and_after_commit(self) -> None:
        identity=self.request(); payload=self.payload()
        with self.assertRaisesRegex(Rejected,'InjectedBeforeCommit'):
            self.store.create_character(Principal('account.test'),identity,payload,fault='before_commit')
        self.assertEqual(0,self.store.connection.execute('SELECT COUNT(*) FROM characters').fetchone()[0])
        with self.assertRaises(OutcomeUnknown):
            self.store.create_character(Principal('account.test'),identity,payload,fault='after_commit')
        result=self.store.create_character(Principal('account.test'),identity,payload)
        self.assertEqual(1,self.store.connection.execute('SELECT COUNT(*) FROM characters').fetchone()[0])
        self.assertEqual(result['character_id'],self.store.connection.execute('SELECT id FROM characters').fetchone()[0])

    def test_disable_new_selection_keeps_original_receipt_and_character_login(self) -> None:
        identity=self.request(); payload=self.payload()
        created=self.store.create_character(Principal('account.test'),identity,payload)
        self.catalog['factions'][0]['selection']['selectable_for_new_character']=False
        self.assertEqual(created,self.store.create_character(Principal('account.test'),identity,payload))
        self.assertEqual('Active',self.store.login(Principal('account.test',created['character_id']),self.request())['state'])
        with self.assertRaisesRegex(Rejected,'FactionUnavailable'):
            self.store.create_character(Principal('account.test'),self.request(),self.payload('Another Name'))

    def test_private_public_fields_do_not_leak(self) -> None:
        principal=self.create(); snapshot=self.store.public_snapshot(principal.character_id)
        self.assertIn('faction_id',snapshot)
        for key in ['account_id','standings','combat_xp','copper','quests','ticket','epoch']:
            self.assertNotIn(key,snapshot)

    def test_stale_lease_and_untrusted_client_rejected(self) -> None:
        principal=self.create(); quest=self.campaign['quests'][0]
        self.store.login(Principal(principal.account_id,principal.character_id,server_id='zone-server.replacement'),self.request())
        with self.assertRaisesRegex(Rejected,'StaleLease'):
            self.give_evidence(principal,quest)
        forged=Principal(principal.account_id,principal.character_id,epoch=2,trusted_server=False)
        with self.assertRaisesRegex(Rejected,'UntrustedCommandOrigin'):
            self.give_evidence(forged,quest)

    def test_cross_character_ownership_and_no_reputation_leak(self) -> None:
        first=self.create(); second=self.create('Second Hero')
        before=list(self.store.connection.execute('SELECT axis,subject_id,value FROM standings WHERE character_id=?',(second.character_id,)))
        self.progress(first,1)
        after=list(self.store.connection.execute('SELECT axis,subject_id,value FROM standings WHERE character_id=?',(second.character_id,)))
        self.assertEqual([tuple(row) for row in before],[tuple(row) for row in after])
        self.store.add_account('account.attacker')
        forged=Principal('account.attacker',first.character_id,epoch=first.epoch)
        with self.assertRaisesRegex(Rejected,'PermissionDenied'):
            self.give_evidence(forged,self.campaign['quests'][1])

    def test_quest_prerequisite_version_and_bad_evidence_rejected(self) -> None:
        principal=self.create()
        with self.assertRaisesRegex(Rejected,'QuestPrerequisiteMissing'):
            self.give_evidence(principal,self.campaign['quests'][1])
        quest=self.campaign['quests'][0]; objective=quest['objectives'][0]
        for changes in [{'version':2},{'trusted_objective_receipt':False},{'source_id':'source.forged'}]:
            arguments={'source_id':objective['source_id']}; arguments.update(changes)
            with self.assertRaises(Rejected):
                self.store.evidence(principal,self.request(),quest['id'],objective['id'],'occurrence',self.revision(principal),**arguments)
        with self.assertRaisesRegex(Rejected,'ObjectiveIncomplete'):
            self.store.complete_quest(principal,self.request(),quest['id'],self.revision(principal))

    def test_duplicate_objective_source_and_quest_rewards_once(self) -> None:
        principal=self.create(); quest=self.campaign['quests'][0]
        self.give_evidence(principal,quest)
        objective=quest['objectives'][0]
        result=self.store.evidence(principal,self.request(),quest['id'],objective['id'],f"source-occurrence:{quest['id']}:{objective['id']}",self.revision(principal),source_id=objective['source_id'])
        self.assertTrue(result['duplicate_source'])
        self.store.complete_quest(principal,self.request(),quest['id'],self.revision(principal))
        copper=self.store.character(principal.character_id)['copper']
        self.store.complete_quest(principal,self.request(),quest['id'],self.revision(principal))
        self.assertEqual(copper,self.store.character(principal.character_id)['copper'])

    def test_quest_reward_fault_and_reputation_clamping(self) -> None:
        principal=self.create(); quest=self.campaign['quests'][0]
        self.give_evidence(principal,quest)
        self.store.connection.execute("UPDATE standings SET value=999 WHERE character_id=? AND subject_id='faction.hearthward-league'",(principal.character_id,))
        identity=self.request(); revision=self.revision(principal)
        with self.assertRaises(OutcomeUnknown):
            self.store.complete_quest(principal,identity,quest['id'],revision,fault='after_commit')
        self.store.complete_quest(principal,identity,quest['id'],revision)
        self.assertEqual(1000,self.store.connection.execute("SELECT value FROM standings WHERE character_id=? AND subject_id='faction.hearthward-league'",(principal.character_id,)).fetchone()[0])
        self.assertEqual(0,self.store.connection.execute('SELECT xp FROM vocation_history WHERE character_id=?',(principal.character_id,)).fetchone()[0])

    def test_solo_full_campaign_branches_and_restart(self) -> None:
        first=self.create(); self.progress(first,branch_id='shared-passage')
        second=self.create('Second Hero'); self.progress(second,branch_id='fortified-crossing')
        self.assertEqual(12,self.store.connection.execute('SELECT units FROM regions').fetchone()[0])
        self.assertEqual(12,self.store.connection.execute('SELECT COUNT(*) FROM quest_completion').fetchone()[0])
        self.assertEqual(self.store.character(first.character_id)['combat_xp'],self.store.character(second.character_id)['combat_xp'])
        identity=first.character_id; expected=self.store.character(identity)
        self.store.close(); self.store=FactionModel(self.database,self.catalog,self.campaign,lambda:self.now)
        self.assertEqual(expected,self.store.character(identity))
        self.assertEqual(1,self.store.connection.execute('SELECT completed FROM regions').fetchone()[0])

    def test_personal_choice_is_immutable(self) -> None:
        principal=self.create(); self.progress(principal,5)
        quest=self.campaign['quests'][4]
        with self.assertRaisesRegex(Rejected,'CampaignChoiceImmutable'):
            self.store.complete_quest(principal,self.request(),quest['id'],self.revision(principal),branch_id='fortified-crossing')
        with self.assertRaisesRegex(Rejected,'FactionImmutable'):
            self.store.migrate_legacy(principal,self.request(),'faction.briarbound-clans',self.revision(principal),explicit_confirmation=True)

    def test_work_requires_owned_complete_evidence_and_replay_protection(self) -> None:
        principal=self.create(); self.progress(principal,3)
        order=self.store.open_work_order(principal,self.request(),self.revision(principal))['work_order_id']
        with self.assertRaisesRegex(Rejected,'InvalidWorkOrder'):
            self.contribute(principal,order)
        for marker in range(3):
            self.store.visit_work_marker(principal,self.request(),order,marker,self.revision(principal))
        self.contribute(principal,order)
        with self.assertRaisesRegex(Rejected,'InvalidWorkOrder'):
            self.contribute(principal,order)
        self.assertEqual(3,self.store.connection.execute('SELECT units FROM regions').fetchone()[0])

    def test_stale_region_and_after_commit_contribution_recovery(self) -> None:
        first=self.create(); second=self.create('Second Hero')
        self.progress(first,3); self.progress(second,3)
        first_order=self.work(first); second_order=self.work(second)
        self.contribute(first,first_order)
        with self.assertRaisesRegex(Rejected,'StaleRegionRevision'):
            self.store.contribute(second,self.request(),second_order,self.revision(second),0)
        identity=self.request(); revision=self.revision(second)
        with self.assertRaises(OutcomeUnknown):
            self.store.contribute(second,identity,second_order,revision,1,fault='after_commit')
        self.store.contribute(second,identity,second_order,revision,1)
        self.assertEqual(6,self.store.connection.execute('SELECT units FROM regions').fetchone()[0])

    def test_two_accounts_tied_ballots_ignore_submission_order_and_preserve_history(self) -> None:
        first=self.create(); self.store.add_account('account.other'); second=self.create('Second Hero','account.other')
        self.progress(first,5); self.progress(second,5,branch_id='fortified-crossing')
        self.store.open_round('round.first')
        self.store.cast_ballot(second,self.request(),'round.first','fortified-crossing',self.revision(second))
        self.store.cast_ballot(first,self.request(),'round.first','shared-passage',self.revision(first))
        self.now+=1800
        self.assertEqual('shared-passage',self.store.resolve_round('round.first'))
        before=dict(self.store.connection.execute('SELECT * FROM regions').fetchone())
        self.assertEqual('shared-passage',self.store.resolve_round('round.first'))
        self.assertEqual(before,dict(self.store.connection.execute('SELECT * FROM regions').fetchone()))
        self.assertEqual('fortified-crossing',self.store.connection.execute("SELECT branch_id FROM quest_completion WHERE character_id=? AND quest_id='quest.hearthward.crossing-choice'",(second.character_id,)).fetchone()[0])
        self.assertEqual(12,before['units'])

    def test_same_account_cannot_cast_multiple_character_ballots(self) -> None:
        first=self.create(); second=self.create('Second Hero'); self.progress(first,5); self.progress(second,5)
        self.store.open_round('round.account')
        self.store.cast_ballot(first,self.request(),'round.account','shared-passage',self.revision(first))
        with self.assertRaisesRegex(Rejected,'AccountAlreadyVoted'):
            self.store.cast_ballot(second,self.request(),'round.account','fortified-crossing',self.revision(second))

    def test_transfer_fences_source_replays_and_keeps_identity(self) -> None:
        principal=self.create(); self.progress(principal)
        transfer=self.store.begin_transfer(principal,self.request(),self.revision(principal))
        with self.assertRaisesRegex(Rejected,'StaleLease'):
            self.store.complete_quest(principal,self.request(),self.campaign['quests'][0]['id'],self.revision(principal))
        destination=Principal(principal.account_id,principal.character_id,server_id='zone-server.elderwood')
        identity=self.request()
        activated=self.store.activate_transfer(destination,identity,transfer['transfer_id'],transfer['ticket'])
        self.assertEqual(activated,self.store.activate_transfer(destination,identity,transfer['transfer_id'],transfer['ticket']))
        with self.assertRaisesRegex(Rejected,'TransferTerminal'):
            self.store.activate_transfer(destination,self.request(),transfer['transfer_id'],transfer['ticket'])
        self.assertEqual('zone.elderwood',self.store.character(principal.character_id)['zone_id'])
        self.assertEqual('faction.hearthward-league',self.store.character(principal.character_id)['faction_id'])
        self.assertEqual(1,self.store.connection.execute("SELECT COUNT(*) FROM leases WHERE state='Active'").fetchone()[0])
        self.assertNotIn(transfer['ticket'],' '.join(row[0] for row in self.store.connection.execute('SELECT result FROM receipts')))

    def test_transfer_expiry_and_admission_race_has_one_terminal_winner(self) -> None:
        principal=self.create(); self.progress(principal)
        transfer=self.store.begin_transfer(principal,self.request(),self.revision(principal))
        self.now+=60
        recovered=self.store.expire_transfer(principal,self.request(),transfer['transfer_id'])
        self.assertGreater(recovered['epoch'],transfer['epoch'])
        with self.assertRaises(Rejected):
            self.store.activate_transfer(Principal(principal.account_id,principal.character_id,server_id='zone-server.elderwood'),self.request(),transfer['transfer_id'],transfer['ticket'])
        self.assertEqual('spawn.thornmere.neutral-infirmary',self.store.character(principal.character_id)['spawn_id'])

    def test_disconnect_after_destination_commit_and_resnapshot(self) -> None:
        principal=self.create(); self.progress(principal)
        transfer=self.store.begin_transfer(principal,self.request(),self.revision(principal))
        destination=Principal(principal.account_id,principal.character_id,server_id='zone-server.elderwood')
        identity=self.request()
        with self.assertRaises(OutcomeUnknown):
            self.store.activate_transfer(destination,identity,transfer['transfer_id'],transfer['ticket'],fault='after_commit')
        result=self.store.activate_transfer(destination,identity,transfer['transfer_id'],transfer['ticket'])
        self.assertEqual(transfer['epoch'],result['epoch'])
        self.assertEqual('spawn.elderwood.bellroot-guest',self.store.character(principal.character_id)['spawn_id'])

    def test_invalid_destination_and_relationship_version_rejected(self) -> None:
        principal=self.create(); self.progress(principal)
        transfer=self.store.begin_transfer(principal,self.request(),self.revision(principal))
        self.catalog['policy']['version']=2
        with self.assertRaisesRegex(Rejected,'TransferVersionOrEpochMismatch'):
            self.store.activate_transfer(Principal(principal.account_id,principal.character_id,server_id='zone-server.elderwood'),self.request(),transfer['transfer_id'],transfer['ticket'])
        self.assertEqual('InTransit',self.store.connection.execute('SELECT state FROM leases').fetchone()[0])

    def test_legacy_confirmation_preserves_class_vocation_inventory_and_xp(self) -> None:
        principal=self.create(); self.progress(principal,1)
        self.store.connection.execute("UPDATE characters SET faction_id=NULL,schema_version=2,migration_state='NeedsSelection' WHERE id=?",(principal.character_id,))
        before=self.store.character(principal.character_id)
        inventory=[tuple(row) for row in self.store.connection.execute('SELECT * FROM inventory')]
        self.assertEqual('FactionMigrationRequired',self.store.login(principal,self.request())['state'])
        with self.assertRaisesRegex(Rejected,'ExplicitLegacySelection'):
            self.store.migrate_legacy(principal,self.request(),'faction.hearthward-league',self.revision(principal),explicit_confirmation=False)
        self.store.migrate_legacy(principal,self.request(),'faction.hearthward-league',self.revision(principal),explicit_confirmation=True)
        after=self.store.character(principal.character_id)
        for field in ['class_id','vocation_id','appearance_id','copper','combat_xp']:
            self.assertEqual(before[field],after[field])
        self.assertEqual(inventory,[tuple(row) for row in self.store.connection.execute('SELECT * FROM inventory')])
        self.assertEqual(3,after['schema_version'])

    def test_corrupt_identity_needs_review_not_silent_assignment(self) -> None:
        principal=self.create()
        self.store.connection.execute("UPDATE characters SET faction_id='faction.corrupt' WHERE id=?",(principal.character_id,))
        self.assertEqual('ReviewedRecoveryRequired',self.store.login(principal,self.request())['state'])
        self.assertEqual('faction.corrupt',self.store.character(principal.character_id)['faction_id'])

    def test_four_faction_synthetic_creation_without_core_switches(self) -> None:
        synthetic = json.loads((Path(__file__).parent / 'fixtures/faction-synthetic.json').read_text())
        self.assertTrue(synthetic['synthetic'])
        configure_synthetic_campaign(self.catalog, self.campaign, synthetic['factions'])
        self.assertEqual([], validate(self.catalog, self.campaign))
        self.store.close()
        self.store = FactionModel(self.database, self.catalog, self.campaign, lambda: self.now)
        for index, fixture in enumerate(synthetic['factions']):
            result = self.store.create_character(Principal('account.test'), self.request(), self.payload('Test Hero ' + chr(65 + index), fixture['id']))
            principal = Principal('account.test', result['character_id'])
            lease = self.store.login(principal, self.request())
            principal = Principal(principal.account_id, principal.character_id, epoch=lease['epoch'])
            quest = self.store.quests[fixture['root_quest_id']]
            self.give_evidence(principal, quest)
            self.store.complete_quest(principal, self.request(), quest['id'], self.revision(principal))
            self.assertEqual(fixture['id'], self.store.character(principal.character_id)['faction_id'])
            self.assertEqual(fixture['spawn_id'], self.store.character(principal.character_id)['spawn_id'])
            self.assertEqual(5, self.store.character(principal.character_id)['combat_xp'])
        self.assertEqual(4, self.store.connection.execute('SELECT COUNT(DISTINCT faction_id) FROM characters').fetchone()[0])
        self.assertEqual(4, self.store.connection.execute('SELECT COUNT(*) FROM quest_completion').fetchone()[0])
        production, _ = load_sources(ROOT.parent)
        self.assertEqual(1, sum(row['selection']['selectable_for_new_character'] for row in production['factions']))

    def test_fifth_faction_is_only_validated_content(self) -> None:
        faction = copy.deepcopy(self.catalog['factions'][1])
        faction['id'] = 'faction.synthetic-fifth'
        faction['display_name'] = 'Synthetic Fifth Faction'
        faction['display_key'] = 'Test.Fifth.Name'
        for existing in self.catalog['factions']:
            existing['initial_reputation']['factions'][faction['id']] = 0
            faction['initial_reputation']['factions'][existing['id']] = 0
            self.catalog['relations']['pairs'].append({'factions': [existing['id'], faction['id']], 'score': 0, 'motive': 'Synthetic validation only.'})
        faction['initial_reputation']['factions'][faction['id']] = 100
        self.catalog['factions'].append(faction)
        fallback = next(row for row in self.campaign['spawns'] if row['id'] == faction['start']['fallback_spawn_id'])
        fallback['allowed_factions'].append(faction['id'])
        fixture = {'id': faction['id'], 'map_id': 'test.map.fifth', 'spawn_id': 'test.spawn.fifth', 'root_quest_id': 'test.quest.fifth', 'mentor_id': 'test.npc.fifth'}
        configure_synthetic_campaign(self.catalog, self.campaign, [fixture])
        self.assertEqual([], validate(self.catalog, self.campaign))
        self.store.close()
        self.store = FactionModel(self.database, self.catalog, self.campaign, lambda: self.now)
        result = self.store.create_character(Principal('account.test'), self.request(), self.payload('Fifth Hero', faction['id']))
        self.assertEqual(faction['id'], self.store.character(result['character_id'])['faction_id'])

    def test_malformed_creation_types_are_rejected_without_mutation(self) -> None:
        for field, value in [('name', None), ('faction_id', []), ('class_id', {}), ('catalog_version', True), ('name', 'Bad--Name'), ('name', 'Bad -Name')]:
            payload = self.payload()
            payload[field] = value
            with self.assertRaises(Rejected):
                self.store.create_character(Principal('account.test'), self.request(), payload)
        self.assertEqual(0, self.store.connection.execute('SELECT COUNT(*) FROM characters').fetchone()[0])

    def test_five_ten_thirty_sqlite_writers_create_consistent_unique_characters(self) -> None:
        # This is SQLite concurrency evidence only, not client/server load evidence.
        for population in [5,10,30]:
            with self.subTest(population=population):
                def create_one(index: int) -> str:
                    model=FactionModel(self.database,self.catalog,self.campaign,lambda:self.now)
                    account=f'account.load.{population}.{index}'
                    try:
                        model.add_account(account,1)
                        letters=chr(65+(index//26))+chr(65+(index%26))
                        payload=self.payload(f'Hero {chr(65+population//5)} {letters}')
                        return model.create_character(Principal(account),request_id(account),payload)['character_id']
                    finally:
                        model.close()
                with ThreadPoolExecutor(max_workers=min(population,10)) as executor:
                    results=list(executor.map(create_one,range(population)))
                self.assertEqual(population,len(set(results)))
        self.assertEqual(45,self.store.connection.execute('SELECT COUNT(*) FROM characters').fetchone()[0])
        self.assertEqual(45,self.store.connection.execute('SELECT COUNT(*) FROM domain_outcomes').fetchone()[0])


if __name__ == '__main__':
    unittest.main()
