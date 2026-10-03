"""Copy live records into disposable Cancel candidate databases."""
import subprocess

names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
def container(suffix):
    matches=[name for name in names if name.endswith(suffix)]
    if len(matches)!=1:raise RuntimeError('Expected one Mongo container: '+suffix)
    return matches[0]
orders=container('train-ticket-ts-order-mongo-1')
other=container('train-ticket-ts-order-other-mongo-1')
wallet=container('train-ticket-ts-inside-payment-mongo-1')
payment=container('train-ticket-ts-payment-mongo-1')
def run(name,*args):subprocess.run(['docker','exec',name,*args],check=True,capture_output=True)
def seed(name,database,collections):
    run(name,'mongo','--quiet','--eval',f"db.getSiblingDB('{database}').dropDatabase()")
    for collection in collections:
        archive=f'/tmp/cancel-{database}-{collection}.archive'
        run(name,'mongodump','--db','ts','--collection',collection,'--archive='+archive)
        run(name,'mongorestore','--archive='+archive,
            '--nsFrom=ts.'+collection,'--nsTo='+database+'.'+collection)
seed(orders,'cancel_orders_test',('orders',))
seed(other,'cancel_other_test',('orders',))
seed(wallet,'cancel_wallet_test',('payment','addMoney'))
seed(payment,'cancel_payment_test',('payment',))
print('Cancel candidate databases seeded from live collections')
