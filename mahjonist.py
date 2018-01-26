from flask import Flask, request
from flask_restful import Resource, Api
import logging, traceback
import uuid
import json
import os
from time import strftime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(os.getcwd())

app = Flask(__name__)
api = Api(app)
apiRoot = '/api'

errors = {
    1000: 'Unspecified error',
    1001: 'Authentication failure',
    1002: 'Wrong request format',
    1003: 'Wrong game ID',
    1004: 'Wrong player number, Mahjong requires 4 players',
    1005: 'Player does not exist',
    1006: 'Wrong round, only 1 player can win a round',
    1007: 'Wrong faans, faan must be equal to or greater than 4',
    1008: 'Wrong round, a round must have a winner',
    1009: 'Game is already finished',
    1010: 'Import error, a player\'s score is lower than the minimum',
    1011: 'Import error, sum of all 4 scores is not 0'
}

games = {}
maxLoss = 50
maxGameLoss = 200

@app.route("/")
def index():
   return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
  # send_static_file will guess the correct MIME type
  return app.send_static_file(path)

def loadGames():
    global games
    try:
        with open('games.json', 'r') as f:
            savedGames = f.read()
            if savedGames:
                games = json.loads(savedGames)
            f.close()
    except FileNotFoundError:
        games = {}
    except Exception as e:
        logging.error(traceback.format_exc())
        return False
    return True

def saveGames():
    try:
        with open('games.json', 'w') as f:
            f.write(json.dumps(games))
            f.close()
    except Exception as e:
        logging.error(traceback.format_exc())
        return False
    return True

def buildError(code, extra=None):
    res = {
        'success': False,
        'error': {
            'code': code,
            'text': errors[code]
        }
    }
    if extra:
        res['error']['text'] += ': ' + extra
    else:
        res['error']['text'] += '.'
    return res

def faanToScore(faan):
    if faan < 4:
        return 0
    else:
        score = -pow(2, faan - 4)
        if score < -maxLoss:
            score = -maxLoss
        return score

def getSumScores(gameID):
    if gameID not in games:
        return False
    game = games[gameID]
    sumScores = {}
    for player, scores in game['players'].items():
        sumScores[player] = sum(scores)
    return sumScores

class Games(Resource):
    def get(self):
        listGames = {}
        for gameID in games:
            listGame = {}
            listGame['startTime'] = games[gameID]['startTime']
            listGame['finished'] = games[gameID]['finished']
            listGames[gameID] = listGame
        return listGames

    def post(self):
        if not request.json or 'players' not in request.json:
            return buildError(1002)
        players = request.json['players']
        if len(players) != 4:
            return buildError(1004)
        gameID = str(uuid.uuid4())
        game = {
            'players': {},
            'finished': False,
            'startTime': strftime("%Y-%m-%d %H:%M:%S")
        }
        for player in players:
            game['players'][player] = []
        games[gameID] = game
        saveGames()
        return {
            'success': True,
            'gameID': gameID
        }

api.add_resource(Games, apiRoot + '/game')


class NewRound(Resource):
    def post(self, gameID):
        if gameID not in games:
            return buildError(1003, gameID)
        if not request.json or 'faans' not in request.json:
            return buildError(1002)
        game = games[gameID]
        if game['finished']:
            return buildError(1009)
        sumScores = getSumScores(gameID)
        faans = request.json['faans']
        winner = None
        scores = {}
        for player, faan in faans.items():
            if player not in game['players']:
                return buildError(1005, player)
            if faan == 0:
                if not winner:
                    winner = player
                else:
                    return buildError(1006)
            else:
                score = faanToScore(faan)
                if not score:
                    return buildError(1007)
                if sumScores[player] + score <= -maxGameLoss:
                    score = -maxGameLoss - sumScores[player]
                    game['finished'] = True
                scores[player] = score
        if not winner:
            return buildError(1008)
        scores[winner] = -sum(scores.values())
        for player, playerScores in game['players'].items():
            playerScores.append(scores[player])
        games[gameID] = game
        saveGames()
        return {
            'success': True,
            'scores': getSumScores(gameID)
        }

api.add_resource(NewRound, apiRoot + '/game/<string:gameID>/newround')

class SingleGame(Resource):
    def get(self, gameID):
        if gameID not in games:
            return buildError(1003, gameID)
        return games[gameID]

    def delete(self, gameID):
        if gameID not in games:
            return buildError(1003, gameID)
        games.pop(gameID, None)
        saveGames()
        return {
            'success': True
        }

api.add_resource(SingleGame, apiRoot + '/game/<string:gameID>')

class GameScores(Resource):
    def get(self, gameID):
        if gameID not in games:
            return buildError(1003, gameID)
        game = games[gameID].copy()
        game.pop('players', None)
        game['scores'] = getSumScores(gameID)
        return game

    def post(self, gameID):
        if gameID not in games:
            return buildError(1003, gameID)
        if not request.json or 'scores' not in request.json:
            return buildError(1002)
        if sum(request.json['scores'].values()) != 0:
            return buildError(1011)
        game = games[gameID]
        players = game['players'].copy()
        finished = False
        for player in players:
            if player not in request.json['scores']:
                return buildError(1005, player)
            if request.json['scores'][player] < -maxGameLoss:
                return buildError(1010, player)
            if request.json['scores'][player] == -maxGameLoss:
                finished = True
            players[player] = [request.json['scores'][player]]
        game['finished'] = finished
        game['players'] = players
        saveGames()
        return {
            'success': True
        }

api.add_resource(GameScores, apiRoot + '/game/<string:gameID>/scores')

if __name__ == '__main__':
    if loadGames():
        # app.run(debug=True)
        app.run(host='0.0.0.0', port=233)
