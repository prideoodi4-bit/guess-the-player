"""Rebuild the editable case bank and its inventory."""
import collections
import json
from pathlib import Path
from engine import Bank, SPECIALTIES, normalize

ROOT = Path(__file__).resolve().parent

def build():
    cases = []
    for specialty in SPECIALTIES:
        for n, line in enumerate((ROOT / 'data' / f'{specialty}.txt').read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.startswith('#'):
                continue
            fields = line.split('|')
            if len(fields) != 9:
                raise ValueError(f'{specialty}:{n}: expected 9 fields, got {len(fields)}')
            section, answer, alias, *facts = fields
            cases.append({'id': f'{specialty}_{n:03}', 'specialty': specialty, 'section': section,
                'diagnosis': answer, 'diagnosis_key': normalize(answer),
                'aliases': list(dict.fromkeys([answer] + [a.strip() for a in alias.split(';') if a.strip()])),
                'facts': facts, 'source_scope': 'Educational scenario derived from a topic in the website checklist',
                'review_status': 'Author-generated; not independently clinician-reviewed'})
    path = ROOT / 'data' / 'cases.json'
    path.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding='utf-8')
    bank = Bank(path)
    counts = collections.Counter(c['specialty'] for c in cases)
    report = ['# Case bank inventory', '', f'Base clinical scenarios: {len(cases)}',
        f'Unique diagnosis names across specialties: {len({c["diagnosis_key"] for c in cases})}',
        f'Difficulty presentations: {len(cases)*3} (three disclosure sequences of each base case, not separate patients)', '',
        'All cases contain six facts converted into exactly four progressive clues.',
        'Each clue gives 25 seconds. Reveal at 100 seconds if nobody answers.', '',
        '| Specialty | Base cases | Difficulty presentations |', '|---|---:|---:|']
    for specialty, name in SPECIALTIES.items():
        report.append(f'| {name} | {counts[specialty]} | {counts[specialty]*3} |')
    report += ['', '## Cases by blueprint section', '']
    for specialty, name in SPECIALTIES.items():
        report += [f'### {name}', '', '| Section | Base cases |', '|---|---:|']
        section_counts = collections.Counter(c['section'] for c in cases if c['specialty'] == specialty)
        for section, count in section_counts.items():
            report.append(f'| {section} | {count} |')
        report.append('')
    report += ['## Coverage boundaries', '',
        'The website contains broad curricular headings; it does not enumerate every possible disease under them. This bank is a broad selection, not a certified exhaustive ministerial database.',
        'Anatomy, investigations, procedures, prevention schedules, developmental milestones, and ethics are not standalone diagnoses and are not converted into diagnosis questions.',
        'Radiology is represented through imaging clues in the disease and fracture cases rather than a separate radiology diagnosis pool.',
        'Rare-disease prevalence is not used to assign difficulty: Easy gives more clinical detail initially; Hard withholds discriminating findings until later.',
        'No case is an official exam question. Added diagnoses are educational interpretations of the relevant broad heading.', '',
        '## Full editable inventory', '', '| Specialty | Section | Diagnosis |', '|---|---|---|']
    for c in cases:
        report.append(f'| {SPECIALTIES[c["specialty"]]} | {c["section"]} | {c["diagnosis"]} |')
    (ROOT / 'BANK_INVENTORY.md').write_text('\n'.join(report)+'\n', encoding='utf-8')
    print(json.dumps({'base_cases': len(cases), 'presentations': len(cases)*3, 'by_specialty': counts}, indent=2))

if __name__ == '__main__':
    build()
    from audit_blueprint import audit
    audit()
