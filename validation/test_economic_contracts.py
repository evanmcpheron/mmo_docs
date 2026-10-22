"""Contract samples and arithmetic only; economic admission remains native T06 work."""
import copy
import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from data_model import definitions, instance_errors


class EconomicContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = json.loads((ROOT / 'sources/data-inventory.json').read_text())
        cls.definitions = definitions(registry)
        cls.samples = json.loads((ROOT / 'validation/tickets/BW-002-T05/contract-samples.json').read_text())
        cls.catalogs = {}
        for name, records in cls.samples['valid'].items():
            identities = {record['id'] for record in records if 'id' in record}
            if identities:
                cls.catalogs[name] = identities
        cls.catalogs['ItemDefinition'].update(
            record['id'] for record in json.loads((ROOT / 'data/item_examples.json').read_text()))
        cls.catalogs['ProfessionDefinition'] = {
            record['id'] for record in json.loads((ROOT / 'data/professions.json').read_text())}

    def errors(self, name, record):
        return instance_errors(record, self.definitions[name], self.definitions,
                               catalogs=self.catalogs)

    def test_positive_samples_use_canonical_definitions_and_typed_references(self):
        for name, records in self.samples['valid'].items():
            for record in records:
                with self.subTest(type=name, record=record.get('id')):
                    self.assertEqual([], self.errors(name, record))

    def test_missing_invalid_and_unknown_inputs_are_structurally_rejected(self):
        for case in self.samples['structural_rejections']:
            with self.subTest(case=case['id']):
                errors = self.errors(case['type'], case['record'])
                self.assertTrue(any(case['expected_error'] in error for error in errors), errors)

    def test_semantic_expectations_are_shape_valid_and_do_not_claim_execution(self):
        for case in self.samples['semantic_admission_expectations']:
            with self.subTest(case=case['id']):
                self.assertEqual([], self.errors(case['type'], case['record']))
                self.assertEqual('Not Executed; T06/T07', case['execution'])

    def test_per_unit_example_arithmetic_does_not_round_a_whole_stack(self):
        for case in self.samples['arithmetic_review']:
            with self.subTest(case=case['label']):
                quarter_share = Fraction(case['eligible_consumed'], 4 * case['output_quantity'])
                per_unit = min(case['per_unit_cap'], quarter_share.numerator // quarter_share.denominator)
                self.assertEqual(case['expected_per_unit'], per_unit)
                self.assertEqual(case['expected_total'], per_unit * case['units_salvaged'])
                self.assertLessEqual(case['expected_total'], case['eligible_consumed'] / 4)

    def test_legacy_absence_null_and_complete_provenance_remain_distinct(self):
        lineage = copy.deepcopy(self.samples['valid']['ItemLineageRecord'][0])
        self.assertEqual([], self.errors('ItemLineageRecord', lineage))
        lineage['material_provenance'] = None
        self.assertEqual([], self.errors('ItemLineageRecord', lineage))
        lineage.pop('material_provenance')
        self.assertEqual([], self.errors('ItemLineageRecord', lineage))
        lineage['material_provenance'] = {}
        self.assertTrue(self.errors('ItemLineageRecord', lineage))

    def test_passive_material_does_not_require_a_fabricated_item_effect(self):
        material = copy.deepcopy(self.samples['valid']['ItemDefinition'][0])
        self.assertNotIn('effect', material)
        self.assertEqual([], self.errors('ItemDefinition', material))
        material['kind'] = 'consumable'
        self.assertTrue(self.errors('ItemDefinition', material))


if __name__ == '__main__':
    unittest.main()
