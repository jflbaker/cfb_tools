def getTeamList():
	allTeams = {}
	readFile = open('teamNames.txt', 'r')
	for line in readFile:
		if line.find(':') == -1:
			#Storing all keys as upper to make the comparison easier
			allTeams[line.strip().upper()] = line.strip()
		else:
			allTeams[line.split(':')[0].strip().upper()] = line.split(':')[1].strip()
	return allTeams
	readFile.close()

def findTeam(teamList, teamAlias):
	if teamAlias.upper() in teamList.keys():
		teamName = teamList[teamAlias.upper()]
		#if team name and alias match then we have reached the endpoint (a valid team name)
		if teamName.upper() == teamAlias.upper():
			return [teamName]
		else:
			#single team alias
			if teamName.find(',') == -1:
				return findTeam(teamList, teamName.upper())
			#list of teams
			else:
				allTeams = teamName.split(',')
				teamsToReturn = []
				for t in allTeams:
					newTeam = findTeam(teamList, t.strip().upper())
					teamsToReturn = teamsToReturn + newTeam
				return teamsToReturn
	else:
		print 'Alias: ' + teamAlias + ' not found'
