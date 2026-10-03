"""Copy live wallet/payment records into disposable candidate Mongo databases."""
import subprocess

names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
def container(suffix):
    matches=[name for name in names if name.endswith(suffix)]
    if len(matches)!=1:raise RuntimeError('Expected one Mongo container: '+suffix)
    return matches[0]
wallet=container('train-ticket-ts-inside-payment-mongo-1')
payment=container('train-ticket-ts-payment-mongo-1')
orders=container('train-ticket-ts-order-mongo-1')
other=container('train-ticket-ts-order-other-mongo-1')
def run(name,*args):subprocess.run(['docker','exec',name,*args],check=True,capture_output=True)
def drop(name,database):
    run(name,'mongo','--quiet','--eval',f"db.getSiblingDB('{database}').dropDatabase()")
def copy(name,collection,database):
    archive=f'/tmp/inside-payment-{collection}.archive'
    run(name,'mongodump','--db','ts','--collection',collection,'--archive='+archive)
    run(name,'mongorestore','--archive='+archive,
        '--nsFrom=ts.'+collection,'--nsTo='+database+'.'+collection)
drop(wallet,'inside_payment_module_test')
drop(payment,'inside_payment_gateway_test')
drop(orders,'inside_payment_orders_test')
drop(other,'inside_payment_other_test')
for collection in ('payment','addMoney'):copy(wallet,collection,'inside_payment_module_test')
copy(payment,'payment','inside_payment_gateway_test')
print('Candidate wallet, outside Payment, and empty order databases prepared')
