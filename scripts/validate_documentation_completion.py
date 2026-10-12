"""Verify docs navigation coverage and current field-provenance completeness."""
from pathlib import Path
import json,re,hashlib,datetime
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]
def main():
 errors=[];nav=(ROOT/'docs/README.md').read_text(encoding='utf-8');indexed=set()
 index=nav.split('## 当前文件完整索引',1)[1]
 for match in re.finditer(r'\[[^\]\n]*\]\((<[^>\n]+>|[^)\n]+)\)',index):
  path=match.group(1).strip().strip('<>');indexed.add(unquote(path))
 actual={p.relative_to(ROOT/'docs').as_posix() for p in (ROOT/'docs').rglob('*') if p.is_file() and p!=ROOT/'docs/README.md'}
 missing=sorted(actual-indexed);extra=sorted(indexed-actual)
 if missing or extra:errors.append({'navigation_missing':missing,'navigation_extra':extra})
 records=json.loads((ROOT/'docs/04-database/field-provenance.json').read_text(encoding='utf-8'))['fields']
 tables=json.loads((ROOT/'docs/04-database/table-catalog.json').read_text(encoding='utf-8'))
 fields={(n,k) for n,t in tables.items() for k in t['columns']}
 if fields!={(x['table'],x['field']) for x in records}:errors.append('field provenance coverage differs')
 for x in records:
  if not all(k in x for k in ['nullable','default_sql','foreign_keys','sql_line','catalog_pointer','api_refs','business_basis']):errors.append('incomplete '+x['table']+'.'+x['field'])
 inv=json.loads((ROOT/'docs/00-project/source-inventory.json').read_text(encoding='utf-8'))
 for x in inv:
  if hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()!=x['sha256']:errors.append('changed source '+x['path'])
 for folder in ['backend','frontend','ai-services','shared-contracts','schemas','docs','tasks','prompts','config','deploy','scripts','tests','datasets']:
  if not (ROOT/folder/'README.md').is_file():errors.append('missing README '+folder)
 report={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FAIL' if errors else 'PASS','scope':'navigation_coverage_and_field_source_completeness','docs_files_indexed':len(actual),'tables':len(tables),'fields':len(fields),'resolved_source_checks':'see database-contract-report.json','source_hashes_unchanged':not any(isinstance(e,str) and e.startswith('changed source') for e in errors),'errors':errors}
 (ROOT/'docs/00-project/validation/documentation-completion-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=True))
 return bool(errors)
if __name__=='__main__':raise SystemExit(main())
