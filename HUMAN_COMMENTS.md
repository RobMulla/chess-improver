# Human feedback - AI should never edit this file. Only human comments should be in this file.

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
