import requests
import csv
import datetime
import bs4
import teamNameValidator
import re
import sys

def createRow(team1, team2):
	#the team with the S+P spread listed in its cell is the S+P favorite to cover, so figure out which team is which here
	#look up the regex syntax for the stuff between the parenthesis and use that
	#list indices:
	#0 - favorite team
	#1 - favorite team score
	#2 - underdog
	#3 - underdog score
	#4 - vegas spread
	#5 - S+P spread
	mat = re.search(r'\([\-|\+]\d+\.*\d*\)', team1)
	if mat is not None:
		spread = mat.group(0)
		t1Name, t1Score = team1.split(spread)
		spread = float(spread.replace('(','').replace(')',''))
		t2 = team2.strip().split(' ') 
		t2Score = t2[len(t2)-1]
		t2.remove(t2Score)
		t2Name = ' '.join(t2)
		try:
			t1Score = int(t1Score)
			t2Score = int(t2Score) 
			t1Name = t1Name.strip()
			t2Name = t2Name.strip()
			#we always want the vegas spread to show as positive
			#so if necessary we flip it here and then subtract the S+P prediction to show as negative
			if t1Score - t2Score > 0 and spread > 0:
				thisRow = [t1Name, t1Score, t2Name, t2Score, abs(float(spread)), t2Score-t1Score, 0]
			elif t1Score - t2Score > 0 and spread < 0:
				thisRow = [t1Name, t1Score, t2Name, t2Score, abs(float(spread)), t1Score-t2Score, 0]
			#might need to include more cases here
			else:
				thisRow = [t2Name, t2Score, t1Name, t1Score, abs(float(spread)), t2Score-t1Score, 0]
			thisRow[6] = abs(thisRow[5]-thisRow[4])
			return thisRow
		except ValueError:
			print 'Error evaluating scores for line: ' + team1 + ', ' + team2
			return None
	else:
		return None

def getFileName(url):
	fName = ''
	mat = re.search(r'week-\d+', url)
	if mat:
		fName = mat.group(0).replace('-','_')
	else:
		fName = 'week_?'
	now = datetime.datetime.now()
	fName = fName + '_'+str(now.hour)+str(now.minute)+str(now.second)+str(now.microsecond)+'.csv'
	return fName

requests.packages.urllib3.disable_warnings()

if len(sys.argv) < 2:
	print "Pass URL to evaluate as an argument"
	sys.exit()

fName = getFileName(sys.argv[1])

teams = teamNameValidator.getTeamList()
ses = requests.session()
page = ses.get(sys.argv[1])
soup = bs4.BeautifulSoup(page.content, 'html.parser')
liToParse = []
allRows = []
for li in soup.findAll('li'):
	for team in teams:
		if li.text.upper().find(team.upper()) != -1 and li.find('a') is None:
			liToParse.append(li.text.encode("utf-8").strip())
			break

for li in liToParse:
	finSeg = li
	while finSeg.find('(') != finSeg.rfind('('):
		finSeg = finSeg[:finSeg.rfind('(')]
	try:
		team1 = finSeg.split(',')[0]
		team2 = finSeg.split(',')[1].split('\xe2')[0] if finSeg.split(',')[1].find('\xe2') != -1 else finSeg.split(',')[1]
	except ValueError:
		print 'Error while parsing row: ' + finSeg
	nextRow = createRow(team1, team2)
	if nextRow:
		allRows.append(nextRow)
	else:
		nextRow = createRow(team2, team1)
		if nextRow:
			allRows.append(nextRow)

headers = ['S&P+ Favorite','Favorite Score','Underdog Score','S&P+ Dog','Vegas Spread','S&P+ Spread','Difference']
with open(fName, 'w') as csvFile:
	writer = csv.writer(csvFile, delimiter=',')
	writer.writerow(headers)
	for row in allRows:
		writer.writerow(row)

