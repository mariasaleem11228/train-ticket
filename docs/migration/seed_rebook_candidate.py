"""Copy live order and wallet collections into disposable Rebook candidate DBs."""
import subprocess

names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
def container(suffix):
    matches=[name for name in names if name.endswith(suffix)]
    if len(matches)!=1:raise RuntimeError('Expected one Mongo container: '+suffix)
    return matches[0]
def run(name,*args):subprocess.run(['docker','exec',name,*args],check=True,capture_output=True)
def seed(name,database,collections):
    run(name,'mongo','--quiet','--eval',f"db.getSiblingDB('{database}').dropDatabase()")
    for collection in collections:
        archive=f'/tmp/rebook-{database}-{collection}.archive'
        run(name,'mongodump','--db','ts','--collection',collection,'--archive='+archive)
        run(name,'mongorestore','--archive='+archive,
            '--nsFrom=ts.'+collection,'--nsTo='+database+'.'+collection)
seed(container('train-ticket-ts-order-mongo-1'),'rebook_orders_test',('orders',))
seed(container('train-ticket-ts-order-other-mongo-1'),'rebook_other_test',('orders',))
seed(container('train-ticket-ts-inside-payment-mongo-1'),'rebook_wallet_test',('payment','addMoney'))
print('Rebook candidate databases seeded from live collections')
