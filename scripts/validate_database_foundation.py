"""Run only in an explicitly selected disposable remote PostgreSQL container."""
from pathlib import Path
import subprocess,time,datetime,json,hashlib,uuid,argparse,re
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ssh-host',required=True);args=ap.parse_args()
 name='codex-docdb-'+uuid.uuid4().hex[:12]
 def remote(command,data=None):
  return subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',args.ssh_host,command],input=data,text=True,encoding='utf-8',capture_output=True,timeout=60)
 r={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'isolated_database_constraints_not_production','container':name,'host':args.ssh_host,'checks':[]};created=False
 try:
  # Use an existing local image; do not download or change host business volumes.
  p=remote('docker image inspect postgres:16 --format "{{.Id}}"');assert p.returncode==0,p.stderr
  digest=p.stdout.strip();assert re.fullmatch('sha256:[a-f0-9]{64}',digest)
  r['image_id']=digest
  cmd=f'docker run --pull never --detach --name {name} --network none --memory 512m --cpus 2 --pids-limit 128 --user 999:999 --cap-drop ALL --security-opt no-new-privileges --tmpfs /var/lib/postgresql/data:rw,size=512m,uid=999,gid=999,mode=0700 --tmpfs /var/run/postgresql:rw,size=16m,uid=999,gid=999,mode=0770 -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=input_validation {digest}'
  p=remote(cmd);assert p.returncode==0,p.stderr;created=True
  for _ in range(25):
   if remote(f'docker exec {name} pg_isready -U postgres -d input_validation').returncode==0:break
   time.sleep(1)
  else:raise RuntimeError('database not ready')
  def sql(s):return remote(f'docker exec -i {name} psql -X -U postgres -d input_validation -v ON_ERROR_STOP=1', '\\set VERBOSITY verbose\n'+s)
  for label,path in [('DDL','docs/04-database/initial-schema.sql'),('existing-25-tests','tests/sql/integrity-tests.sql'),('ranking-fixtures','tests/sql/ranking-fixtures.sql')]:
   raw=(ROOT/path).read_text(encoding='utf-8');p=sql(raw)
   entry={'name':label,'status':'PASS' if p.returncode==0 else 'FAIL','sha256':hashlib.sha256(raw.encode()).hexdigest(),'stderr':p.stderr[-8000:]};r['checks'].append(entry)
   if p.returncode:raise RuntimeError(label+': '+p.stderr[-4000:])
  for case in json.loads((ROOT/'tests/sql/first-source-cases.json').read_text(encoding='utf-8'))['cases']:
   p=sql(case['sql']);expected=case['expected_sqlstate']
   ok=(p.returncode==0) if expected is None else p.returncode!=0 and re.search(r'ERROR:\s+'+expected+r':',p.stderr) is not None
   r['checks'].append({'name':case['name'],'status':'PASS' if ok else 'FAIL','expected_sqlstate':expected,'stderr':p.stderr[-1200:]})
   if not ok:raise RuntimeError(case['name']+': '+p.stderr[-1200:])
  r['status']='PASS'
 except Exception as e:r['status']='FAIL';r['error']=str(e)
 finally:
  if created:
   p=remote('docker rm -f '+name);r['cleanup_exit_code']=p.returncode
   if p.returncode:r['status']='FAIL'
  r['ended_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  (ROOT/'docs/00-project/validation/database-foundation-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':r['status'],'checks':len(r['checks']),'error':r.get('error'),'cleanup':r.get('cleanup_exit_code')},ensure_ascii=True))
 return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
