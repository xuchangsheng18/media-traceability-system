"""Offline development-input validation. Does not run business services or train models."""
from pathlib import Path
import sys,os,json,re,hashlib,argparse,datetime,platform,importlib.metadata
if os.environ.get('INPUT_VALIDATION_LIBS'):sys.path.insert(0,os.environ['INPUT_VALIDATION_LIBS'])
import yaml
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource
from openapi_spec_validator import validate_spec
from pglast import parse_sql
ROOT=Path(__file__).resolve().parents[1]
def json_read(p):
    return json.loads(p.read_text(encoding='utf-8'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON '+x)))
class UniqueLoader(yaml.SafeLoader):pass
def unique_mapping(loader,node,deep=False):
    result={}
    for key,value in node.value:
        k=loader.construct_object(key,deep=deep)
        if k in result:raise ValueError('duplicate YAML key '+str(k))
        result[k]=loader.construct_object(value,deep=deep)
    return result
UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,unique_mapping)
def yread(p):return yaml.load(p.read_text(encoding='utf-8'),Loader=UniqueLoader)
def semantics(v,path='root',duration=None):
    errors=[]
    if isinstance(v,dict):
        if 'cluster_id' in v and isinstance(v.get('candidates'),list) and 'coverage_note' in v and 'model_version' in v and 'status' in v:
            candidates=v['candidates']
            ranks=[c.get('rank') for c in candidates if isinstance(c,dict)]
            assets=[c.get('asset_id') for c in candidates if isinstance(c,dict)]
            if len(candidates)>3:errors.append(path+':more than three origin candidates')
            if ranks!=list(range(1,len(candidates)+1)):errors.append(path+':origin ranks must be ordered and consecutive')
            if any(not isinstance(a,str) for a in assets):errors.append(path+':origin asset must be a UUID string')
            elif len(assets)!=len({a.lower() for a in assets}):errors.append(path+':duplicate origin asset')
            if 'candidate_count' in v and v['candidate_count']!=len(candidates):errors.append(path+':origin candidate_count mismatch')
            if not candidates and v.get('status')!='insufficient':errors.append(path+':empty origin result must be insufficient')
            for i,candidate in enumerate(candidates):
                if not isinstance(candidate,dict):continue
                for key in ['evidence_ids','counter_evidence_ids']:
                    values=candidate.get(key)
                    if isinstance(values,list) and all(isinstance(x,str) for x in values):
                        if len(values)!=len({x.lower() for x in values}):errors.append(path+f':duplicate {key} in candidate {i}')
        if isinstance(v.get('duration_ms'),int):duration=v['duration_ms']
        if isinstance(v.get('start_ms'),int) and isinstance(v.get('end_ms'),int) and v['end_ms']<=v['start_ms']:errors.append(path+':end_ms<=start_ms')
        if duration is not None and isinstance(v.get('end_ms'),int) and v['end_ms']>duration:errors.append(path+':time interval exceeds declared duration')
        if all(isinstance(v.get(k),(int,float)) for k in ['x','y','width','height']):
            if v['x']+v['width']>1+1e-12 or v['y']+v['height']>1+1e-12:errors.append(path+':bbox exceeds original bounds')
        if isinstance(v.get('failure_count'),int) and isinstance(v.get('sample_count'),int) and v['failure_count']>v['sample_count']:errors.append(path+':failure_count exceeds sample_count')
        if v.get('status') in ['FAILED','SKIPPED','DEFERRED','NOT_SUPPORTED'] and 'findings' in v and v['findings']:errors.append(path+':non-success includes findings')
        if 'records' in v and 'purposes_disjoint' in v:
            seen={};samples=set();splits={}
            for row in v['records']:
                if row['sample_id'] in samples:errors.append(path+':duplicate sample_id')
                samples.add(row['sample_id']);splits[row['sample_id']]=row['split']
                for field in ['source_group_ids','person_group_ids','event_group_ids']:
                    for group in row[field]:
                        key=(field,group)
                        if key in seen and seen[key]!=row['split']:errors.append(path+':cross-split '+field+':'+group)
                        seen[key]=row['split']
            for row in v['records']:
                for parent in row['parent_sample_ids']:
                    if parent in splits and splits[parent]!=row['split']:errors.append(path+':parent crosses split')
            if v['status']=='frozen' and v['holdout_access']!='acceptance_only':errors.append(path+':frozen holdout access not restricted')
        for k,x in v.items():errors+=semantics(x,path+'.'+k,duration)
    elif isinstance(v,list):
        for i,x in enumerate(v):errors+=semantics(x,path+f'[{i}]',duration)
    return errors
def walkrefs(v):
    if isinstance(v,dict):
        if '$ref' in v:yield v['$ref']
        for x in v.values():yield from walkrefs(x)
    if isinstance(v,list):
        for x in v:yield from walkrefs(x)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--task');args=ap.parse_args()
    errors=[];checks=[];examples=[];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    def check(name,fn):
        try:
            result=fn();checks.append({'name':name,'status':'PASS','detail':result})
        except Exception as e:errors.append({'check':name,'error':str(e)});checks.append({'name':name,'status':'FAIL','detail':str(e)})
    def syntax():
        counts={'json':0,'yaml':0,'utf8':0}
        for p in ROOT.rglob('*'):
            if not p.is_file() or any(x in p.parts for x in ['.venv','node_modules','.git','__pycache__','dist','build']) or p.name.startswith('~$'):continue
            if p.suffix in ['.json','.yaml','.yml','.md','.sql','.txt','.py','.csv']:
                text=p.read_text(encoding='utf-8')
                if '\ufffd' in text:raise ValueError('replacement glyph '+str(p))
                counts['utf8']+=1
                if p.suffix=='.json':json_read(p);counts['json']+=1
                if p.suffix in ['.yaml','.yml']:yread(p);counts['yaml']+=1
        return counts
    check('UTF8_JSON_YAML_no_duplicate_keys',syntax)
    schemas={}
    for p in (ROOT/'schemas').rglob('*.schema.json'):
        s=json_read(p);schemas[s['$id']]=s
    registry=Registry().with_resources((i,Resource.from_contents(s)) for i,s in schemas.items())
    def meta():
        for s in schemas.values():Draft202012Validator.check_schema(s)
        for s in schemas.values():
            for ref in walkrefs(s):
                if ref.startswith('urn:') and ref.split('#')[0] not in schemas:raise ValueError('unknown local schema '+ref)
                if ref.startswith('http'):raise ValueError('network reference not allowed '+ref)
        return {'standalone_schemas':len(schemas),'offline_registry':True,'format_assertion':True}
    check('JSON_Schema_2020_12_meta_and_local_refs',meta)
    def api():
        specs={}
        for p in [ROOT/'docs/03-api/openapi.yaml',ROOT/'docs/03-api/inference-openapi.yaml']:
            s=yread(p);validate_spec(s)
            count=0;ids=[]
            for path,methods in s['paths'].items():
                for method,operation in methods.items():
                    if method not in ['get','post','put','delete','patch']:continue
                    count+=1;ids.append(operation['operationId'])
                    actual={p['name'] for p in operation.get('parameters',[]) if p['in']=='path'}
                    assert actual==set(re.findall(r'{([^}]+)}',path)),path
            assert len(ids)==len(set(ids))
            specs[p.name]={'operations':count,'components':len(s.get('components',{}).get('schemas',{}))}
        return specs
    check('OpenAPI_3_1_documents',api)
    def fixtures():
        idx=json_read(ROOT/'tests/fixtures/fixture-index.json')['fixtures'];mismatch=[]
        for entry in idx:
            data=json_read(ROOT/entry['path']);s=schemas[entry['schema_id']]
            if entry.get('fragment'):s={'$schema':s['$schema'],'$ref':entry['schema_id']+entry['fragment']}
            v=Draft202012Validator(s,registry=registry,format_checker=FormatChecker())
            structural=[str(e.message) for e in v.iter_errors(data)];semantic=semantics(data)
            expected=entry['expected']
            good=(not structural and not semantic) if expected=='valid' else bool(structural) if expected=='invalid' else not structural and bool(semantic)
            examples.append({'id':entry['id'],'expected':expected,'matched':good,'structural_errors':structural[:3],'semantic_errors':semantic[:3]})
            if not good:mismatch.append(entry['id'])
        assert not mismatch,'fixture expectations mismatched '+','.join(mismatch)
        return {'count':len(idx),'valid':sum(x['expected']=='valid' for x in idx),'invalid':sum(x['expected']=='invalid' for x in idx),'semantic_invalid':sum(x['expected']=='semantic_invalid' for x in idx)}
    check('positive_negative_semantic_fixtures',fixtures)
    def catalogs():
        s=schemas['urn:media-trace:dataset:catalog:0.1.0'];v=Draft202012Validator(s,registry=registry,format_checker=FormatChecker());cs=list((ROOT/'datasets/catalog').glob('*.yaml'))
        for p in cs:v.validate(yread(p))
        assert len(cs)==15
        for p in cs:
            bad=yread(p);bad['status']='frozen'
            assert not v.is_valid(bad),'pending catalog can freeze'
        return {'catalogs':len(cs),'pending_to_frozen_rejected':15}
    check('dataset_catalogs_and_no_false_release',catalogs)
    tables=json_read(ROOT/'docs/04-database/table-catalog.json')
    def sql():
        s=(ROOT/'docs/04-database/initial-schema.sql').read_text(encoding='utf-8');nodes=parse_sql(s)
        assert len(re.findall(r'CREATE TABLE mt\.',s))==len(tables)
        core=['content_item','media_asset','analysis_task','task_node_run','keyframe','text_segment','risk_finding','tamper_finding','source_match','evidence_item','review_record','model_registry']
        assert set(core)<=set(tables)
        return {'statements':len(nodes),'tables':len(tables),'core_tables_preserved':len(core),'parser_only_not_engine_execution':True}
    check('SQL_parser_and_core_tables',sql)
    def mapping():
        rows=json_read(ROOT/'docs/04-database/api-field-mapping.json')['mapping']
        for r in rows:
            for col in r['targets']:
                t,c=col.split('.');assert t in tables and c in tables[t]['columns'],col
        spec=yread(ROOT/'docs/03-api/openapi.yaml');expected=set()
        def fieldpaths(s,prefix=''):
            if '$ref' in s:return fieldpaths(spec['components']['schemas'][s['$ref'].split('/')[-1]],prefix)
            if 'anyOf' in s:return fieldpaths(s['anyOf'][0],prefix)
            if s.get('type')=='object':
                result=set()
                for k,v in s.get('properties',{}).items():
                    full=prefix+'.'+k if prefix else k
                    result.add(full);result|=fieldpaths(v,full)
                return result
            if s.get('type')=='array':return fieldpaths(s['items'],prefix+'[]')
            return set()
        for path,ops in spec['paths'].items():
            for method,o in ops.items():
                if method not in ['get','post','put','patch','delete']:continue
                for direction,holder in [('request',o.get('requestBody',{})),('response',next((x for k,x in o['responses'].items() if k.startswith('2')),{}))]:
                    schema=holder.get('content',{}).get('application/json',{}).get('schema',{})
                    if '$ref' in schema:
                        name=schema['$ref'].split('/')[-1]
                        expected|={(o['operationId'],direction,k) for k in fieldpaths(spec['components']['schemas'][name])}
        actual={(r['operation_id'],r['direction'],r['field']) for r in rows}
        assert actual==expected,{'missing':list(expected-actual),'extra':list(actual-expected)}
        return {'nested_field_rows':len(rows),'unknown_sql_columns':0,'coverage':len(actual)}
    check('API_SQL_field_mapping',mapping)
    backlog=yread(ROOT/'tasks/backlog.yaml')['tasks'];trace=yread(ROOT/'docs/00-project/requirement-traceability.yaml')['requirements']
    cases=yread(ROOT/'docs/09-testing/test-scenarios.yaml')['scenarios']+yread(ROOT/'docs/09-testing/task-test-scenarios.yaml')['scenarios']
    def tasks():
        src=json_read(ROOT/'tasks/source-task-cards.json');deps=json_read(ROOT/'tasks/execution-dependencies-candidate.json')
        ids={t['id'] for t in backlog};assert ids==set(src)=={f'T{i:03}' for i in range(1,171)}
        gray=set();black=set()
        def visit(t):
            assert t not in gray,'dependency cycle '+t
            if t in black:return
            gray.add(t)
            for parent in deps[t]:assert parent in ids;visit(parent)
            gray.remove(t);black.add(t)
        for t in ids:visit(t)
        for row in backlog:
            f=src[row['id']]['fields'];assert row['name']==src[row['id']]['name'];assert row['source_role']==f['责任角色'];assert row['source_effort']==f['建议工作量'];assert row['source_dependencies']==f['源前置依赖']
            assert row['execution_dependencies_candidate']==deps[row['id']]
            for p in row['input_refs']+[row['doc_file']]:assert (ROOT/p).is_file(),p
        return {'tasks':170,'original_fields_preserved':True,'unknown_dependencies':0,'cycles':0,'task_argument':args.task,'implementation_not_tested':True}
    check('170_tasks_source_integrity_refs_and_DAG',tasks)
    def tracing():
        tids={t['id'] for t in backlog};cids={c['id'] for c in cases};rids={r['requirement_id'] for r in trace}
        assert len(cids)==len(cases);assert len(rids)==len(trace)
        models=yread(ROOT/'docs/06-algorithms/model-catalog.yaml')['models'];mids={m['id'] for m in models};dids={p.stem for p in (ROOT/'datasets/catalog').glob('*.yaml')}
        ops=json_read(ROOT/'docs/03-api/operation-index.json');oids={o['id'] for o in ops};covered=set()
        for r in trace:
            assert r['task_ids'] and set(r['task_ids'])<=tids
            assert r['test_ids'] and set(r['test_ids'])<=cids
            assert set(r['operation_ids'])<=oids
            assert set(r['table_names'])<=set(tables)
            assert set(r['model_ids'])<=mids and set(r['dataset_ids'])<=dids
            for u in r['usecase_ids']:assert (ROOT/f'docs/01-requirements/use-cases/{u}.md').exists()
            covered|=set(r['task_ids'])
        assert covered==tids
        for m in models:
            assert m['task_ids'] and set(m['task_ids'])<=tids
            assert m['dataset_ids'] and set(m['dataset_ids'])<=dids
            for kind in ['request','response']:assert (ROOT/f'schemas/model/{m["id"]}.{kind}.schema.json').exists()
        for o in ops:assert set(o['tasks'])<=tids and set(o['tables'])<=set(tables)
        return {'requirements':len(trace),'scenarios':len(cases),'tasks_covered':len(covered),'models':len(models),'orphan_refs':0}
    check('requirements_usecases_API_tables_models_datasets_tasks_tests',tracing)
    def sources():
        inv=json_read(ROOT/'docs/00-project/source-inventory.json')
        for item in inv:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
        assert 'NOT_FROZEN' in (ROOT/'docs/00-project/baseline-1.0.md').read_text(encoding='utf-8')
        assert yread(ROOT/'docs/00-project/review-decisions.yaml')['decisions']==[]
        return {'source_files':len(inv),'hashes_unchanged':True,'freeze_state':'NOT_FROZEN'}
    check('source_snapshots_and_no_false_approval',sources)
    if args.task and args.task not in {t['id'] for t in backlog}:errors.append({'check':'task_argument','error':'unknown task '+args.task})
    result={'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':sys.version,'platform':platform.platform(),'tools':{n:importlib.metadata.version(n) for n in ['PyYAML','jsonschema','openapi-spec-validator','pglast']}},'checks':checks,'fixture_results':examples,'errors':errors,'status':'PASS' if not errors else 'FAIL','scope':'input_artifact_validation_not_implementation','freeze_state':'NOT_FROZEN','task':args.task}
    folder=ROOT/'docs/00-project/validation';folder.mkdir(parents=True,exist_ok=True);(folder/'local-validation-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'errors':errors,'fixtures':len(examples),'freeze':'NOT_FROZEN'},ensure_ascii=True))
    return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
