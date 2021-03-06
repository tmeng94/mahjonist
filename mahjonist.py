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

gameData = {}


@app.route("/")
def index():
    return app.send_static_file('index.html')


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


def loadGames():
    global config
    global gameData
    try:
        with open('games.json', 'r') as f:
            savedGames = f.read()
            if savedGames:
                gameData = json.loads(savedGames)
            f.close()
    except FileNotFoundError:
        gameData = {"config": {"lastGame": "", "maxLoss": 50, "maxGameLoss": 200}, "games": {}}
    except Exception as e:
        logging.error(traceback.format_exc())
        return False
    return True


def saveGames():
    try:
        with open('games.json', 'w') as f:
            f.write(json.dumps(gameData))
            f.close()
    except Exception as e:
        logging.error(traceback.format_exc())
        return False
    return True


def getNames(game, name):
    return name in [p['name'] for p in game['players']]


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
        if score < -gameData["config"]["maxLoss"]:
            score = -gameData["config"]["maxLoss"]
        return score


def getSumScores(gameID):
    if gameID not in gameData["games"]:
        return False
    game = gameData["games"][gameID]
    sumScores = {}
    for player in game['players']:
        sumScores[player['name']] = sum(player['scores'])
    return sumScores


class Config(Resource):
    def get(self):
        return gameData["config"]


api.add_resource(Config, apiRoot + '/config')


class Games(Resource):
    def get(self):
        listGames = {}
        for gameID in gameData["games"]:
            listGame = {}
            listGame['startTime'] = gameData["games"][gameID]['startTime']
            listGame['finished'] = gameData["games"][gameID]['finished']
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
            'players': [],
            'finished': False,
            'startTime': strftime("%Y-%m-%d %H:%M:%S")
        }
        for player in players:
            game['players'].append({
                'name': player,
                'scores': []
            })
        gameData["games"][gameID] = game
        saveGames()
        return {
            'success': True,
            'gameID': gameID
        }


api.add_resource(Games, apiRoot + '/game')


class NewRound(Resource):
    def post(self, gameID):
        if gameID not in gameData["games"]:
            return buildError(1003, gameID)
        if not request.json or 'faans' not in request.json:
            return buildError(1002)
        game = gameData["games"][gameID]
        if game['finished']:
            return buildError(1009)
        sumScores = getSumScores(gameID)
        faans = request.json['faans']
        # winner = None
        winner = request.json['winner']
        winnerFaan = request.json['faans'][winner]
        scores = {}
        for player, faan in faans.items():
            if not getNames(game, player):
                return buildError(1005, player)
            if winner == player:
                continue
            score = faanToScore(faan + winnerFaan)
            if not score:
                return buildError(1007)
            if sumScores[player] + score <= -gameData["config"]["maxGameLoss"]:
                score = -gameData["config"]["maxGameLoss"] - sumScores[player]
                game['finished'] = True
            scores[player] = score
        if not winner:
            return buildError(1008)
        scores[winner] = -sum(scores.values())
        for player in game['players']:
            player['scores'].append(scores[player['name']])
        gameData["games"][gameID] = game
        saveGames()
        return {
            'success': True,
            'scores': getSumScores(gameID)
        }


api.add_resource(NewRound, apiRoot + '/game/<string:gameID>/newround')


class SingleGame(Resource):
    def get(self, gameID):
        if gameID not in gameData["games"]:
            return buildError(1003, gameID)
        return gameData["games"][gameID]

    def delete(self, gameID):
        if gameID not in gameData["games"]:
            return buildError(1003, gameID)
        gameData["games"].pop(gameID, None)
        saveGames()
        return {
            'success': True
        }


api.add_resource(SingleGame, apiRoot + '/game/<string:gameID>')


class ResetGame(Resource):
    def post(self, gameID):
        if gameID not in gameData["games"]:
            return buildError(1003, gameID)
        game = gameData["games"][gameID]
        for player in game['players']:
            player['scores'] = []
        game['startTime'] = strftime("%Y-%m-%d %H:%M:%S")
        game['finished'] = False
        saveGames()
        return {
            'success': True
        }


api.add_resource(ResetGame, apiRoot + '/game/<string:gameID>/reset')


class UndoLastRound(Resource):
    def post(self, gameID):
        if gameID not in gameData["games"]:
            return buildError(1003, gameID)
        game = gameData["games"][gameID]
        for player in game['players']:
            player['scores'].pop()
        game['finished'] = False
        saveGames()
        return {
            'success': True
        }


api.add_resource(UndoLastRound, apiRoot + '/game/<string:gameID>/undo')


class GameScores(Resource):
    def get(self, gameID):
        if gameID not in gameData["games"]:
            return buildError(1003, gameID)
        game = gameData["games"][gameID].copy()
        game.pop('players', None)
        game['scores'] = getSumScores(gameID)
        return game

    def post(self, gameID):
        if gameID not in gameData["games"]:
            return buildError(1003, gameID)
        if not request.json or 'players' not in request.json:
            return buildError(1002)
        playerScore = request.json['players']
        if sum([p['score'] for p in playerScore]) != 0:
            return buildError(1011)
        game = gameData["games"][gameID]
        newPlayers = []
        finished = False
        for p in playerScore:
            player = p['name']
            score = p['score']
            if score < -gameData["config"]["maxGameLoss"]:
                return buildError(1010, player)
            if score == -gameData["config"]["maxGameLoss"]:
                finished = True
            newPlayers.append({
                'name': player,
                'scores': [score]
            })
        if len(newPlayers) == 4:
            game['finished'] = finished
            game['players'] = newPlayers
            saveGames()
            return {
                'success': True
            }
        else:
            return buildError(1004)


api.add_resource(GameScores, apiRoot + '/game/<string:gameID>/scores')

if __name__ == '__main__':
    if loadGames():
        # app.run(debug=True)
        app.run(host='0.0.0.0', port=233)
