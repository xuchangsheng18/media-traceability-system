"""Check repository planning documents without changing services or databases."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
errors, historical_links = [], []
checked_links = 0
for p in ROOT.rglob('*.md'):
    if any(x in p.parts for x in ['.venv', 'node_modules', '.git', '__pycache__', 'dist', 'build']):
        continue
    rel = p.relative_to(ROOT).as_posix()
    body = p.read_text(encoding='utf-8')
    if '\ufffd' in body:
        errors.append({'file': rel, 'error': 'replacement_character'})
    historical = rel.startswith('docs/_converted/')
    for match in re.finditer(r'!?\[[^\]\n]*\]\((<[^>\n]+>|[^)\n]+)\)', body):
        target = match.group(1).strip()
        if target.startswith('<'):
            target = target[1:target.find('>')]
        target = target.split(' "')[0]
        if target.startswith(('#', 'http:', 'https:', 'mailto:', 'codex:', 'app:')):
            continue
        target = unquote(target.split('#')[0])
        if not target:
            continue
        # This report is produced at the end of this very run.
        if (p.parent/target).resolve() == ROOT/'docs/00-project/validation/repository-docs-validation.json':
            continue
        checked_links += 1
        if not (p.parent/target).exists():
            entry = {'file':rel,'target':target}
            (historical_links if historical else errors).append(entry)
for item in json.loads((ROOT/'docs/00-project/source-inventory.json').read_text(encoding='utf-8')):
    p = ROOT/item['path']
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
        errors.append({'source':item['path'],'error':'source_hash_mismatch'})
for name in ['backend','frontend','ai-services','shared-contracts','schemas','datasets','docs','tasks','prompts','config','deploy','scripts','tests']:
    if not (ROOT/name).is_dir():
        errors.append({'directory':name,'error':'missing'})
for name in ['README.md','docs/README.md','docs/00-project/baseline-1.0.md']:
    if 'NOT_FROZEN' not in (ROOT/name).read_text(encoding='utf-8'):
        errors.append({'file':name,'error':'missing_planning_status'})
report = {'time_utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL' if errors else 'PASS',
          'scope':'document_paths_and_source_integrity_not_implementation',
          'links_checked':checked_links,'errors':errors,
          'historical_conversion_links_not_rewritten':historical_links,
          'external_urls_checked':False,'business_services_tested':False}
dest = ROOT/'docs/00-project/validation/repository-docs-validation.json'
dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'links_checked':checked_links,'errors':errors,'historical_links':len(historical_links)},ensure_ascii=True))
raise SystemExit(bool(errors))
