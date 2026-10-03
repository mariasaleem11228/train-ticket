"""Recover fixed-IP migration proxies after Docker restarts legacy containers first."""
import json
import hybrid_routing as routing

def recover():
    states={name:json.loads(d['file'].read_text()) for name,d in routing.DEFS.items()
            if d['file'].exists() and json.loads(d['file'].read_text())['mode'] in ('module','legacy')}
    missing={name:state for name,state in states.items()
             if not routing.inspect(routing.DEFS[name]['proxy'])['State']['Running']}
    reserved={state['ip'] for state in missing.values()}
    all_proxies={d['proxy'] for d in routing.DEFS.values()}
    stopped={}
    try:
        network=json.loads(routing.docker('network','inspect','train-ticket_my-network'))[0]['Containers']
        occupants={value['Name'] for value in network.values()
                   if value['IPv4Address'].split('/')[0] in reserved}
        for occupant in sorted(occupants):
            if occupant in all_proxies or occupant==routing.station.MODULE:
                raise RuntimeError('Reserved IP held by another migration component: '+occupant)
            details=routing.inspect(occupant)
            stopped[occupant]=details['HostConfig']['RestartPolicy']['Name']
            routing.docker('update','--restart=no',occupant)
            routing.docker('stop',occupant)
            print('Temporarily stopped',occupant,flush=True)
        for name in missing:
            routing.docker('start',routing.DEFS[name]['proxy'])
            print('Recovered',name,'proxy',flush=True)
    finally:
        for occupant,policy in stopped.items():
            routing.docker('update','--restart='+policy,occupant)
            routing.docker('start',occupant)
            print('Restarted',occupant,flush=True)

if __name__=="__main__":recover()
