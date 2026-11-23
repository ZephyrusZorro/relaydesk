"""Real website/API → durable worker → n8n → review ticket integration."""
import argparse
import json
import time
from pathlib import Path
from uuid import uuid4
import httpx


def run(base, live):
    with httpx.Client(base_url=base, timeout=30) as client:
        health = client.post('/api/integrations/check', json={})
        health.raise_for_status()
        system = health.json()
        assert system['n8n'] and system['handshake']['protocol'] == 'relaydesk-v2'
        assert system['jobs']['worker_online']
        records=[]
        for mode in (['demo','live'] if live else ['demo']):
            start=time.perf_counter()
            response=client.post('/api/jobs', json={'text':'My VPN tunnel disconnects every five minutes. The approved VPN client shows a connection error.','requester':'Version 2 verification','location':'Verification office','request_id':'v2-check-'+uuid4().hex,'mode':mode})
            assert response.status_code == 202,response.text
            job=response.json()
            accept_ms=(time.perf_counter()-start)*1000
            deadline=time.monotonic()+270
            while time.monotonic()<deadline:
                job=client.get('/api/jobs/'+job['id']).json()
                if job['state'] in {'failed','completed'}:break
                time.sleep(.5)
            assert job['state']=='completed',job
            stages=[event['stage'] for event in job['events']]
            assert all(stage in stages for stage in ['queued','dispatching','classifying','retrieving','drafting','persisting','completed']),stages
            ticket=client.get('/api/tickets/'+job['ticket_id']).json()
            assert ticket['category']=='vpn' and ticket['execution_id']
            records.append({'mode':mode,'job_id':job['id'],'ticket_id':ticket['id'],'accept_ms':round(accept_ms,2),'total_seconds':round(time.perf_counter()-start,2),'mode_used':ticket['mode_used'],'flags':ticket['flags'],'stages':stages,'n8n_execution_id':ticket['execution_id']})
        first=client.post('/api/knowledge/search',json={'query':'VPN tunnel disconnects','category':'vpn'}).json()
        second=client.post('/api/knowledge/search',json={'query':'VPN tunnel disconnects','category':'vpn'}).json()
        assert second['diagnostics']['cache_hit']
        return {'authenticated_n8n_handshake':system['handshake'],'worker_verified':True,'configured_workflows':len(system['workflows']),'jobs':records,'retrieval_cache_verified':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://localhost:18080');parser.add_argument('--live',action='store_true')
    args=parser.parse_args();result=run(args.base,args.live)
    Path('docs/v2-integration-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
