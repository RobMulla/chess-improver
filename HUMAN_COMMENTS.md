# Human feedback - AI should never edit this file. Only human comments should be in this file.


Update (Jan 28, 2026):
- I think the user flow of the site could be:
  - Top right - a setting option where the user could add settings (add a list of accounts for chess.com and lichess) - in the landing page if thats not setup the first time it would prompt them to set it up (maybe a banner)
- After this on the menu there would be a data overview page. This could have each of the accounts linked. Show a "github" style data overview that shows all the dates where games were imported (heatmap for number of games) - this could also show some basic stats about the games (rating over time, etc) . And could show if there are dates with games that havent been imported yet (like a different color in the charts)
    - The data view should also have an easy way to select dates / accounts to import games for.
    - As easy as "import new games" button next to the account.
    - Also a deliniation between games that were imported AND analyzed vs just imported in the github overview (maybe bold the edge of the square if analyzed)
    - Could have option here to also analyze imported games for a selected account and date range (could be cool if we could select dates on the github graph and then import/analyze for selected dates)
    - Allow but add warning if user tries to analyze games that have already been analyzed.
    - Stats about imported dates % - analyzed %.
- Next could be a games overview page. What we have currently is a good start but I think  the feel of the page could be much better. The key here is to ahve a table that really encompasses the full area of the main pane of the page. Research different front end frameworks that might be good for this and are popular. I'd like it to feel more like a excel sheet - where the user can move left right, and scroll up and down a bit. The top should have the buttons for the page you are on and allowed to skip through pages. Filtering allowed for each row by clicking on the header. Also at the top a selector for number of games to show per page. The data we show here can expand (number of rows).
- Next is the signle game view page. What we have here is okay. But the UI could be improved. The page should fill up the entire page and NOT feel like the user can scroll down. The Moves list and other data should click into place and if they are scrollable (like the moves) it should scroll independently of the rest of the page.
- Next is the "blunder buster" page. The landing page is okay. It should allow the user to start a new blunder buster session - using selectors to choose what they want to practice (opening, middlegame, endgame, etc), playing as white or black, and the number of moves to practice. Also allow to select specific game ranges, time controls, etc.
    - This page would also show the results from past blunder buster sessions / stats etc.
- Next is the actual blunder buster game.
    - I think we have a great start. Some updates that will make this much more fun:
        - At the top it should show a bunch of boxes - one for each of the moves that will be played in the session - so the user can easily see where they are and how theyve been doing. At the start all the boxes will be grey. Once played it will change to green if correct or red if incorrect.
        - When the position loads its very important to have the board flipped so its from the perspective of the player.
        - It should animate the opponents last move.
        - The user should be able to move backwards through the game up until the point of the move that is being played (but not beyond)
        - If the user makes an incorrect move it should flash red. And green for correct.
        - User can keep trying if wrong - but counted as failed if they dont get it on the first attempt.
        - If the user makes an incorrect move it should show the opponents response to their move (the top stockfish response)
        - The hint button would show the piece that needs to be moved. It would make that move marked as failed.
        - If the user clicks show answer it would show an arrow of the correct move - and the user should still be able to make that move. After it would also show the stockfish response.
        - Regadlress of correct or incorrect it would not move onto the next position until the user clicked next position.
        - The game could have a clock at the top that shows how long theyve been playing the session and also how long theyve been on the current position (these stats could be stored after the session is over)
        - The overall stats could also show if the user stopped before the end of the session.

## Jan 27th Feedback

Id like to think through the story of this project and where we sit. Update the prd and other docs to map out a plan to achieve given these goals

After understaning our current state I think I want to focus this project a bit more. Before we had a number of ideas of what the project would be but my new focus is:

1) UI based app. Everything should be able to be done in the UI. After loading up.
2) Settings and data - these should be persistent. The user should be able to set some configs like their usernames for chess.com and lichess (could be multiple for each).
2) Data import - this is the process of pulling the user games from the sites and storing in the database.
3) Analysis - this is a critical step where we run the analysis on each of the games. This needs to be on par with how lichess and chess.com calculate accuracy, and move qualiy
- Along the same lines we need to ahve a unified way of labeling the opening type for later filtering and standardized way of storing this.
- Also need to classify each move as opening/middlegame/endgame in a smart way.

- Games view - this is central page for viewing all imported games.
- Game reivew page - where we can step through the game

After this I'd like to focus on one practice "game" - more could come in later but this is the main focus first....
1) "Blunder buster" - this takes all the blunder moves from past games. Randomly pulls a number of them and I practice making the moves again - trying not to blunder this time. Before I kick off a blunder buster game I should be able to set some configs like number of moves to practice - could filter just to openings / middlegame / endgame - able to select the types of moves I want to revisit (could select just blunders, blunders and mistakes, or more) - or filter to timestamps (past weeks games, past month, year, or specific dates) - time controls, etc.
- When I run a blunder blaster game is done it stores the settings and results as I go. There should be a page where I can review my past runs.

2) Next thing (don't worry about yet) is somethign where I can set the openings I want to practice and basically set my ideal opening tree. This could be built out slowly as I go and have a graph of all my "ideal" branches for openings - then show stats about my games vs

Lets focus the project given this feedback.
1) Remove any functionaliy from the site that doesnt fit into this plan.
2) Refactor current codebase if there is a better way to do things.
3) Similarly rethink how to structure the data and database.


Other ideas:
- Can we leverage the lichess api to get some of the analysis data?
- Or just use the lichess github repo to pull how they do it? https://github.com/lichess-org/lila
