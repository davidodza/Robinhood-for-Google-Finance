from Robinhood import Robinhood
import getpass
import collections
import argparse
import ast

logged_in = False

# hard code your credentials here to avoid entering them each time you run the script
username = ""
password = ""

parser = argparse.ArgumentParser(description='Export Robinhood trades to a CSV file')
parser.add_argument('--debug', action='store_true', help='store raw JSON output to debug.json')
parser.add_argument('--username', default=username, help='your Robinhood username')
parser.add_argument('--password', default=password, help='your Robinhood password')
args = parser.parse_args()
username = args.username
password = args.password

robinhood = Robinhood();

# login to Robinhood
while not logged_in:
    if username == "":
        print("Robinhood username:")
        try: input = raw_input
        except NameError: pass
        username = input()
    if password == "":
        password = getpass.getpass()

    logged_in = robinhood.login(username=username, password=password)
    if logged_in == False:
        password = ""
        print ("Invalid username or password.  Try again.\n")

fields = collections.defaultdict(dict)
trade_count = 0
queued_count = 0

# fetch order history and related metadata from the Robinhood API
orders = robinhood.get_endpoint('orders')

# load a debug file
# raw_json = open('debug.txt','rU').read()
# orders = ast.literal_eval(raw_json)

# store debug 
if args.debug:
    # save the CSV
    try:
        with open("debug.txt", "w+") as outfile:
            outfile.write(str(orders))
            print("Debug infomation written to debug.txt")
    except IOError:
        print('Oops.  Unable to write file to debug.txt')

# do/while for pagination

#pagination
paginated = True
page = 0
n = 0

#cache instruments
cached_instruments = {} #{instrument:symbol}

while paginated:
    for i, order in enumerate(orders['results']):
        executions = order['executions']
        if len(executions) > 0:
            trade_count += 1
            # Iterate over all the different executions
            for execution in executions:
                # Get the Symbol of the order
                fields[n]['symbol'] = cached_instruments.get(order['instrument'], robinhood.get_custom_endpoint(order['instrument'])['symbol'])
                cached_instruments[order['instrument']] = fields[n]['symbol']

                # Get all the key,value from the order
                for key, value in enumerate(order):
                    if value != "executions":
                        fields[n][value] = order[value]

                # Get specific values from the execution of the order
                fields[n]['timestamp'] = execution['timestamp']
                fields[n]['quantity'] = execution['quantity']
                fields[n]['price'] = execution['price']
                n+=1
        # If the state is queued, we keep this to let the user know they are pending orders
        elif order['state'] == "queued":
            queued_count += 1

    # paginate, if out of ORDERS paginate is OVER
    if orders['next'] is not None:
        page = page + 1
        #get the next order, a page is essentially one order
        orders = robinhood.get_custom_endpoint(str(orders['next']))
    else:
        paginated = False

#for i in fields:
#     print fields[i]
#     print "-------"    
#Fields stores ALL relevant information

# check we have trade data to export
if trade_count > 0 or queued_count > 0:
    print("%d queued trade%s and %d executed trade%s found in your account." % (queued_count, "s"[queued_count==1:], trade_count, "s"[trade_count==1:]))
    # print str(queued_count) + " queded trade(s) and " + str(trade_count) + " executed trade(s) found in your account."
else:
    print("No trade history found in your account.")
    quit()

# CSV headers

desired = ("price", "timestamp", "fees", "quantity", "symbol", "side")

#need to filter out the offending headers

keys = fields[0].keys()
keys = sorted(keys)
newkeys = []
for key in keys:
    if key in desired:
        newkeys.append(key)

keys = list(newkeys)
for i in range(0, len(newkeys)):
    if newkeys[i] == "price":
        newkeys[i] = "Purchase price per share"
    if newkeys[i] == "timestamp":
        newkeys[i] = "Date purchased"
    if newkeys[i] == "fees":
        newkeys[i] = "Commission"
    if newkeys[i] == "quantity":
        newkeys[i] = "Shares"
    if newkeys[i] == "symbol":
        newkeys[i] = "Symbol"
    if newkeys[i] == "side":
        newkeys[i] = "Transaction type"

csv = ""
for key in newkeys:
    csv += key + ','
csv += "\n"

# CSV rows

line = ""
csvb = []

for row in fields:
    for key in keys:
        try:
            if key=="price" or key=="fees" or key=="quantity":
                fields[row][key] = round(float(fields[row][key]),2)
            line += str(fields[row][key]) + ","
        except:
            line += ","
    line += "\n"
    csvb.append(line)
    line = ""

#google finance seems to prefer dates in ascending order, so we must reverse the given order
for i in reversed(csvb):
    csv+=str(i)

# choose a filename to save to
print("Choose a filename or press enter to save to `robinhood.csv`:")
try: input = raw_input
except NameError: pass
filename = input().strip()
if filename == '':
    filename = "robinhood.csv"

# save the CSV
try:
    with open(filename, "w+") as outfile:
        outfile.write(csv)
except IOError:
    print("Oops.  Unable to write file to ",filename)
    print("(maybe it's already open)")

########## Following code added by https://github.com/davidodza to include Dividends #############

divs = robinhood.get_endpoint('dividends')
with open("testdivs.txt", "w+") as outfile:
    outfile.write(str(divs))
class dividendClass:
    rate = ""    
    shares = ""
    #paidAmt = int(rate)*int(shares) #needs work
    payDate = ""
    
    def __init__(self, rate, shares, payDate):
            self.rate = rate
            self.shares = shares
            self.payDate = payDate
    def csvOut(self):
            return str(self.payDate + "," + self.rate + "," + self.shares + "," + str(float(self.rate)*float(self.shares)) + "\n")

divs = str(divs).replace("'","").replace(",","")
divs = str(divs).replace("position","\nposition").replace("rate","\nrate").replace("payable_date","\npayable_date")
with open("testdivs.txt", "w+") as outfile:
    outfile.write(str(divs))

regexs=[':(.*) ',
':(.*)} {account',
':(.*)} {record_date',
':(.*)} {id:',
':(.*)} {url',
':(.*)} {amount',
':(.*)} {withholding',
':(.*)} {paid_at',
':(.*)} {instrument',
':(.*) ',
':(.*) account',
':(.*) record_date',
':(.*) id:',
':(.*) url',
':(.*) amount',
':(.*) withholding',
':(.*) paid_at',
':(.*) instrument',
':(.*)}] previous',
':(.*)}]}']

attributes=['rate','position','payable_date']

rates,ratesfinal,ratesfinalnodups = ([] for i in range(3))
positions, positionsfinal, positionsfinalnodups = ([] for i in range(3))
dates, datesfinal, datesfinalnodups = ([] for i in range(3))

f=open('testdivs.txt','r')
for line in f:
    for attr in attributes:
        for regex in regexs:
            value = re.compile(attr + regex)         
            for item in value.findall(line):
                if attr == 'rate':
                    rates.append(item)
                if attr == 'position':
                    positions.append(item)
                if attr == 'payable_date':
                    dates.append(item)

#Remove regex garbage from results
datesfinal = [s for s in dates if (len(str(s)) < 16 and len(str(s)) > 3)]
ratesfinal = [s for s in rates if (len(str(s)) < 17 and len(str(s)) > 10)]
positionsfinal = [s for s in positions if (len(str(s)) < 10 and len(str(s)) > 3)]

#Remove duplicates from rates if necessary
for item in ratesfinal:
    item = item.replace(" ", "")
    if item not in ratesfinalnodups:
        ratesfinalnodups.append(item)
    
#Remove duplicates from positions if necessary
for item in positionsfinal:
    item = item.replace(" ", "")
    if item not in positionsfinalnodups:
        positionsfinalnodups.append(item)

#Remove duplicates from dates if necessary
for item in datesfinal:
    item = item.replace(" ", "").replace("}", "")
    datesfinalnodups.append(item) 

if len(datesfinal) == len(ratesfinalnodups)*2:
    datesfinalnodups = [i for a, i in enumerate(datesfinal) if a%2 == 0]

    
print ("------------")
print (ratesfinalnodups)
print (positionsfinalnodups)
print (datesfinalnodups)

divList = []
for i in range(len(ratesfinalnodups)):
    newDiv = dividendClass(ratesfinalnodups[i],positionsfinalnodups[i],datesfinalnodups[i])
    divList.append(newDiv)
    
for div in divList:
    print(div.csvOut())
# save the CSV
try:
    with open("dividends.csv", "w+") as outfile:
        outfile.write("Date,Rate,Shares,Total Earned\n")
        for div in divList:
            outfile.write(div.csvOut())
except IOError:
    print("Oops.  Unable to write file to dividends.csv (maybe it's already open)")   



