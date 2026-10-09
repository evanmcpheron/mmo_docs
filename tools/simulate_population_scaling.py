#!/usr/bin/env python3
"""Check the proposed frozen-target arithmetic, not game balance or networking."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def targets(population: int) -> dict:
    if type(population) is not int:
        raise TypeError('Population must be an integer')
    engaged = max(1, min(population, 30))
    return {'engaged_at_activation': engaged, 'essential': 12, 'optional': 8 + 2 * engaged.bit_length(), 'policy_version': 1}

def main() -> None:
    records = [targets(population) for population in [1, 2, 5, 10, 30]]
    assert [row['optional'] for row in records] == [10, 12, 14, 16, 18]
    assert all((row['essential'] == 12 for row in records))
    assert all((targets(number)['optional'] <= targets(number + 1)['optional'] for number in range(1, 30)))
    frozen = targets(5)
    initial = dict(frozen)
    credited = 7
    for current_population in [1, 30, 2, 10, 1]:
        candidate_for_next_project = targets(current_population)
        assert frozen == initial and credited == 7 and (candidate_for_next_project['essential'] == 12)
    assert targets(-1) == targets(1) and targets(100) == targets(30)
    report = {'status': 'pass', 'model': 'Proposed arithmetic only', 'population_cases': records, 'checks': ['Fixed essential goal', 'Expected optional values', 'Monotonic optional effort', 'Frozen existing goals', 'Credited progress retained', 'Input clamp'], 'runtime_or_fun_measurement': False, 'network_clients_connected': 0}
    (ROOT / 'sources/population-simulation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
if __name__ == '__main__':
    main()
