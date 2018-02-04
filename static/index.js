$(document).ready(function(){

    Game = Backbone.Model.extend({
        //Create a model to hold name attribute
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
        //Create a model to hold name attribute
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
        //Create a model to hold name attribute
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

    let gameModel= new Game;
    //let nameModel= new Name({name: 'World'});

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


        //alert(nameModel.get("name"));
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
                $("label[id=player" + i + "FinalFaan]").html("&nbsp;(= " + playerFaan + " + " + winnerFaan + " = " + +(playerFaan + winnerFaan) + ")");
            }
        }
    }

    $("input:radio[name=winner]").change(function () {
        winner = $("input:radio[name=winner]:checked").val();
        // console.log(winner);
        let winnerID = +winner + 1;
        // for (let i=1; i<=4; i++) {
        //     let playerInput = $("input[id=playerFaan" + i + "]");
        //     if (playerInput.attr("disabled")) {
        //         playerInput.attr("disabled", false);
        //         playerInput.val("");
        //     }
        // }
        let winnerInput = $("input[id=playerFaan" + winnerID + "]");
        // winnerInput.attr("disabled", true);
        // winnerInput.val(0);
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
        // el - stands for element. Every view has an element associated in which HTML content will be rendered.
        el: '#game',
        // It's the first function called when this view it's instantiated.
        initialize: function(){
            gameModel.fetch();
            // this.render();
            this.listenTo(gameModel, "sync", this.render);
            this.listenTo(gameModel, "change", this.render);
            setFinalFaans();
        },

        render: updateGame
    });

    let gameView = new GameView;

    $('#newRound').click(function(){
        // let newGame = prompt("Please Enter Game:");
        // gameModel.set("game", newGame);
        //nameModel.set({"name": newName});
        // console.log(winner);

        // gameModel.set("startTime", new Date().toLocaleString());
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
        //let cnt = 1;
        // gameModel.get("players").forEach(player => {
        //     scores[player["name"]] = +$("input[id=playerImportScores" + cnt + "]").val();
        //     console.log(scores[player["name"]]);
        //     cnt++;
        // });
        newScores.set("players", players);
        newScores.save(null, {
            success: res => {
                if (res.get("success")) {
                    gameModel.fetch();
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

    $('#clearFaans').click(function(){
        for (let i = 1; i <= 4; i++) {
            $("input[id=playerFaan" + i + "]").val("");
        }
        setFinalFaans();
    });
});
