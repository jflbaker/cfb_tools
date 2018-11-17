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
	#5 - S+P spreada
	#6 - S+P/vegas difference
	#7 - actual favorite margin
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
				thisRow = [t1Name, t1Score, t2Name, t2Score, abs(float(spread)), t2Score-t1Score, 0, 0]
			elif t1Score - t2Score > 0 and spread < 0:
				thisRow = [t1Name, t1Score, t2Name, t2Score, abs(float(spread)), t1Score-t2Score, 0, 0]
			#might need to include more cases here
			else:
				thisRow = [t2Name, t2Score, t1Name, t1Score, abs(float(spread)), t2Score-t1Score, 0, 0]
			thisRow[6] = abs(thisRow[5]-thisRow[4])
			return thisRow
		except:
			print 'Error evaluating scores for line: ' + team1 + ', ' + team2
			return None
	else:
		return None

def getScores(week):
	#list indices
	#0 team 1 name
	#1 team 1 score
	#2 team 2 name
	#3 team 2 score
	#4 winning team (1,2)
	#There's definitely an API for getting this info but whatever
	allScores = []
	url = 'https://www.ncaa.com/scoreboard/football/fbs/2018/'+str(week)+'/all-conf'
	page = requests.get(url)
	soup = bs4.BeautifulSoup(page.content, 'html.parser')
	scoreboard = soup.find('div', id='scoreboardContent')
	for game in scoreboard.find_all('ul', class_='gamePod-game-teams'):
		w1, w2 = game.find_all('li')
		#only create a new row if the game is over (has a winner)
		if w1['class'][0] == 'winner' or w2['class'][0] == 'winner':
			team1, team2 = game.find_all('span', class_='gamePod-game-team-name')
			#Fix some of the notation here ex 'St.' -> 'State'
			team1 = team1.text.replace('St.', 'State')
			team2 = team2.text.replace('St.', 'State')
			team1Score, team2Score = game.find_all('span', class_='gamePod-game-team-score')
			allScores.append([team1, int(team1Score.text), team2, int(team2Score.text), 1 if w1['class'][0]=='winner' else 2])
	return allScores

def assignScore(game, allScores):
	#this would be easy if everyone used the same naming conventions, but they don't so the comparison is much largers
	#for an exact match we'll accept a match for either team, for a partial we'll only accept it if both match
	#need to figure out a way to handle the 'State' vs 'St.' difference
	for score in allScores:
		if score[0] == game[0] or score[2] == game[2] or (game[0].find(score[0]) != -1 and game[2].find(score[2]) != -1):
			game[7] = score[1] - score[3]
			return score
		if score[0] == game[2] or score[2] == game[0] or (game[2].find(score[0]) != -1 and game[0].find(score[2]) != -1):
			game[7] = score[3] - score[1]
			return score
	return None

def getFileName(url):
	fName = ''
	week = 0
	mat = re.search(r'week-\d+', url)
	if mat:
		fName = mat.group(0).replace('-','_')
		week = fName.split('_')[1]
	else:
		fName = 'week_?'
	now = datetime.datetime.now()
	fName = fName + '_'+str(now.hour)+str(now.minute)+str(now.second)+str(now.microsecond)+'.csv'
	return fName, week


requests.packages.urllib3.disable_warnings()

if len(sys.argv) < 2:
	print "Pass URL to evaluate as an argument"
	sys.exit()

fName, week = getFileName(sys.argv[1])

teams = teamNameValidator.getTeamList()
page = requests.get(sys.argv[1])
#Narrow down the portion of the page we're looking at, document structure makes this tough so this approach is no very elegant
try:
	soup = bs4.BeautifulSoup(page.content.split('Below are FBS picks')[1], 'html.parser')
except:
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

scores = getScores(week)
if len(scores) > 0:
	for row in allRows:
		sc = assignScore(row, scores)
		if sc is not None:
			scores.remove(sc)

headers = ['S&P+ Favorite','Favorite Score (predicted)','S&P+ Dog','Underdog Score (predicted)','Vegas Spread','S&P+ Spread','Difference','Favorite margin (actual)']
with open(fName, 'w') as csvFile:
	writer = csv.writer(csvFile, delimiter=',')
	writer.writerow(headers)
	for row in allRows:
		writer.writerow(row)
