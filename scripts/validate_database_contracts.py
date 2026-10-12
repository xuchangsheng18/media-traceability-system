"""Check dictionary completeness and origin API semantics independently of SQL execution."""
from pathlib import Path
import json,copy,re,datetime
from validate_inputs import semantics,yread,Draft202012Validator,FormatChecker,parse_sql
ROOT=Path(__file__).resolve().parents[1]
def main():
 checks=[]
 def check(name,fn):
  try:detail=fn();checks.append({'name':name,'status':'PASS','detail':detail})
  except Exception as e:checks.append({'name':name,'status':'FAIL','error':str(e)})
 catalog=json.loads((ROOT/'docs/04-database/table-catalog.json').read_text(encoding='utf-8'))
 sql=(ROOT/'docs/04-database/initial-schema.sql').read_text(encoding='utf-8')
 def fields():
  actual={}
  for stmt in parse_sql(sql):
   node=stmt.stmt
   if type(node).__name__=='CreateStmt':
    actual[node.relation.relname]={x.colname for x in node.tableElts if type(x).__name__=='ColumnDef'}
  expected={n:set(t['columns']) for n,t in catalog.items()}
  assert actual==expected,'catalog and CREATE TABLE columns differ'
  count=0
  for n,t in catalog.items():
   for k,v in t['columns'].items():
    assert v[2].strip() and '见来源契约' not in v[2],n+'.'+k
    comment="COMMENT ON COLUMN mt.%s.%s IS '%s';"%(n,k,v[2].replace("'","''"))
    assert comment in sql,n+'.'+k+' comment missing'
    count+=1
  d=(ROOT/'docs/04-database/data-dictionary.md').read_text(encoding='utf-8')
  assert '见来源契约' not in d
  provenance=json.loads((ROOT/'docs/04-database/field-provenance.json').read_text(encoding='utf-8'))['fields']
  assert {(x['table'],x['field']) for x in provenance}=={(n,k) for n,t in catalog.items() for k in t['columns']}
  sql_lines=sql.splitlines()
  for item in provenance:
   n,k=item['table'],item['field'];v=catalog[n]['columns'][k]
   assert item['definition']==v[2] and item['catalog_pointer']==f'/{n}/columns/{k}'
   assert item['nullable']==not_null_inverse(v[1]),n+'.'+k
   assert re.match(r'\s*'+re.escape(k)+r'\s+',sql_lines[item['sql_line']-1]),n+'.'+k+' stale SQL location'
   for fk in item['foreign_keys']:
    assert fk['target_table'] in catalog
    assert set(fk['target_columns'])<=set(catalog[fk['target_table']]['columns'])
    assert len(fk['local_columns'])==len(fk['target_columns'])
  return {'tables':len(catalog),'columns':count,'missing_descriptions':0,'missing_comments':0}
 def not_null_inverse(constraints):return not ('NOT NULL' in constraints or 'PRIMARY KEY' in constraints)
 check('dictionary_SQL_catalog_provenance',fields)
 spec=yread(ROOT/'docs/03-api/openapi.yaml');schema=spec['components']['schemas']['FirstSource']
 def pointers():
  records=json.loads((ROOT/'docs/04-database/field-provenance.json').read_text(encoding='utf-8'))['fields'];count=0
  for record in records:
   for ref in record['api_refs']:
    node=spec
    for token in ref['schema_pointer'].split('/')[1:]:
     token=token.replace('~1','/').replace('~0','~')
     node=node[int(token)] if isinstance(node,list) else node[token]
    assert isinstance(node,dict)
    count+=1
  return {'resolved_API_source_pointers':count}
 check('field_source_API_pointers_resolve',pointers)
 api=json.loads((ROOT/'schemas/api/common.schema.json').read_text(encoding='utf-8'))
 check('OpenAPI_generated_schema_identity',lambda: True if schema==api['$defs']['FirstSource'] else (_ for _ in ()).throw(AssertionError('generated schema stale')))
 v=Draft202012Validator(schema,format_checker=FormatChecker())
 base=json.loads((ROOT/'docs/03-api/examples/FirstSource.json').read_text(encoding='utf-8'))
 def result(n):
  x=copy.deepcopy(base);x['candidate_count']=n;x['candidates']=[]
  for i in range(n):
   item=copy.deepcopy(base['candidates'][0]);item['rank']=i+1;item['asset_id']=f'12345678-1234-4234-8234-{i:012d}';x['candidates'].append(item)
  x['status']='insufficient' if n==0 else 'candidate'
  return x
 def assertion(data,structure_ok,semantics_ok):
  a=not list(v.iter_errors(data));b=not semantics(data)
  assert (a,b)==(structure_ok,semantics_ok),{'structural':a,'semantic':b,'errors':semantics(data)}
  return {'structural_valid':a,'semantic_valid':b}
 for n in range(4):check('API_valid_'+str(n),lambda n=n:assertion(result(n),True,True))
 check('API_four_candidates',lambda:assertion(result(4),False,False))
 bad=result(2);bad['candidates'][1]['rank']=1
 check('API_duplicate_rank_different_element',lambda:assertion(bad,True,False))
 duplicate=result(2);duplicate['candidates'][1]['asset_id']=duplicate['candidates'][0]['asset_id']
 check('API_duplicate_asset_different_rank',lambda:assertion(duplicate,True,False))
 gap=result(2);gap['candidates'][1]['rank']=3
 check('API_rank_gap',lambda:assertion(gap,True,False))
 wrong=result(1);wrong['candidate_count']=2
 check('API_count_mismatch',lambda:assertion(wrong,True,False))
 empty=result(0);empty['status']='candidate'
 check('API_empty_wrong_status',lambda:assertion(empty,True,False))
 missing=result(1);del missing['ranking_id']
 check('API_missing_snapshot',lambda:assertion(missing,False,True))
 refs=result(1);refs['candidates'][0]['evidence_ids']*=2
 check('API_duplicate_support_evidence',lambda:assertion(refs,False,False))
 case_refs=result(1);e=case_refs['candidates'][0]['evidence_ids'][0];case_refs['candidates'][0]['evidence_ids']=[e,e.upper()]
 check('API_duplicate_evidence_case_insensitive',lambda:assertion(case_refs,True,False))
 raw=json.loads((ROOT/'tests/fixtures/dataset/D12.annotation.json').read_text(encoding='utf-8'))
 check('dataset_ground_truth_not_ranking_output',lambda: True if not semantics(raw) else (_ for _ in ()).throw(AssertionError('wrong contract applied')))
 report={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','checks':checks,'scope':'dictionary_and_origin_response_contract_not_business_approval'}
 (ROOT/'docs/00-project/validation/database-contract-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=True))
 return report['status']!='PASS'
if __name__=='__main__':raise SystemExit(main())
