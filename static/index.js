$(document).ready(function(){

    let config = {
        //TODO retrieve from server
        lastGame: "demo",
        maxLoss: 50,
        maxGameLoss: 200
    };

    Game = Backbone.Model.extend({
        defaults: {
            players: [
                {
                    "name": "a",
                    "scores": [-5, -4]
                },
                {
                    "name": "b",
                    "scores": [7, -8]
                },
                {
                    "name": "c",
                    "scores": [9, 10]
                },
                {
                    "name": "d",
                    "scores": [-11, 2]
                }
            ],
            finished: false,
            startTime: new Date().toLocaleString()
        },
        urlRoot: "/api/game/demo",
        id: "demo"
    });

    Round = Backbone.Model.extend({
        defaults: {
            faans: {
                "a": 4,
                "b": 0,
                "c": 4,
                "d": 4
            }
        },
        urlRoot: "/api/game/demo/newround"
    });

    Scores = Backbone.Model.extend({
        defaults: {
            players: [
                {
                    "name": "a",
                    "scores": 1
                },
                {
                    "name": "b",
                    "scores": 1
                },
                {
                    "name": "c",
                    "scores": -3
                },
                {
                    "name": "d",
                    "scores": 1
                }
            ]
        },
        urlRoot: "/api/game/demo/scores"
    });

    let gameModel = new Game;

    function updateGame(){
        let gameStatus = "The game is ongoing.";
        if (gameModel.get("finished")) {
            gameStatus = "The game is already finished."
        }
        let playerStatus = "<table class=\"table table-striped table-condensed\"><tr>";
        let players = gameModel.get("players");

        playerStatus += "<th scope=\"col\">Round</th>";
        for (let i = 1; i <= players[0]["scores"].length; i++) {
            playerStatus += "<th scope=\"col\">" + i + "</th>";
        }
        
        playerStatus += "<th scope=\"col\">Total</th></tr>";
        players.forEach(player => {
            playerStatus += "<tr><th scope=\"row\">" + player["name"] + "</th>";
            player["scores"].forEach(score => {
                playerStatus += "<td>" + score + "</td>";
            });
            if (player["scores"].length > 0) {
                playerStatus += "<td>" + player["scores"].reduce((sum, i) => sum + i) + "</td>";
            }
            else {
                playerStatus += "<td>0</td>";
            }
            playerStatus += "</tr>";
        });
        playerStatus += "</table>";

        $(this.el).html(
            "<h5>" + gameStatus + "</h5>"
            + "<h5>Start time: " + gameModel.get("startTime") + "</h5>"
            + playerStatus
        );

        for (let i = 1; i <= 4; i++) {
            $("label[id=player" + i + "Name]").html(players[i-1]["name"]);
            $(".importPlayers" + i + ".playerName").val(players[i-1]["name"]);
        }
        $('#errorText').html("");
    }

    let winner = 0;

    function setFinalFaans() {
        let winnerID = +winner + 1;
        let winnerFaan = +$("input[id=playerFaan" + winnerID + "]").val();
        for (let i=1; i<=4; i++) {
            let playerFaan = +$("input[id=playerFaan" + i + "]").val();
            if (i === winnerID) {
                $("label[id=player" + i + "FinalFaan]").html("");
            }
            else {
                let finalFaanStr = " = " + +(playerFaan + winnerFaan);
                let maxFaan = Math.ceil(Math.log2(config.maxLoss) + 4);
                if (playerFaan + winnerFaan >= maxFaan) {
                    finalFaanStr = " ≥ " + +maxFaan;
                }
                $("label[id=player" + i + "FinalFaan]").html("&nbsp;(= " + playerFaan + " + " + winnerFaan + finalFaanStr + ")");
            }
        }
    }

    function clearFaans () {
        for (let i = 1; i <= 4; i++) {
            $("input[id=playerFaan" + i + "]").val("");
        }
        setFinalFaans();
    }

    $("input:radio[name=winner]").change(function () {
        winner = $("input:radio[name=winner]:checked").val();
        let winnerID = +winner + 1;
        let winnerInput = $("input[id=playerFaan" + winnerID + "]");
        setFinalFaans();
    });

    $("input[name=faan]").on('change keyup paste mouseup', setFinalFaans);

    $('#newGame').click(function(){
        $.post("/api/game/demo/reset", null, res => {
            if (res["success"]) {
                gameModel.fetch();
            }
        });
    });

    GameView = Backbone.View.extend({
        el: '#game',
        initialize: function(){
            gameModel.fetch();
            this.listenTo(gameModel, "sync", this.render);
            this.listenTo(gameModel, "change", this.render);
            setFinalFaans();
        },

        render: updateGame
    });

    let gameView = new GameView;

    $('#newRound').click(function(){
        let newRound = new Round;
        let faans = {};
        let cnt = 1;
        gameModel.get("players").forEach(player => {
            faans[player["name"]] = +$("input[id=playerFaan" + cnt + "]").val();
            //console.log(faans[player]);
            cnt++;
        });
        newRound.set("faans", faans);
        newRound.set("winner", gameModel.get("players")[winner]["name"]);
        newRound.save(null, {
            success: res => {
                if (res.get("success")) {
                    gameModel.fetch();
                    clearFaans();
                }
                else {
                    $('#errorText').html(res.get("error").text);
                }
            },
            error: err => {
                $('#errorText').html(err);
            }
        });
    });

    $('#importPlayersSubmit').click(function(){
        let newScores = new Scores;
        let players = [];
        for (let i = 1; i <= 4; i++) {
            let player = {
                name: $(".importPlayers" + i + ".playerName").val(),
                score: +$(".importPlayers" + i + ".playerScore").val()
            };
            players.push(player);
        }
        newScores.set("players", players);
        newScores.save(null, {
            success: res => {
                if (res.get("success")) {
                    gameModel.fetch();
                    clearFaans();
                }
                else {
                    $('#errorText').html(res.get("error").text);
                }
            },
            error: err => {
                $('#errorText').html(err);
            }
        });
    });

    $('#clearFaans').click(clearFaans);

    $('#undoLastRoundSubmit').click(function(){
        $.post("/api/game/demo/undo", null, res => {
            if (res["success"]) {
                gameModel.fetch();
            }
        });
    });
});
