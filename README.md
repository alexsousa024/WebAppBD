The database will be based on the game called TeamFight Tactics (TFT). The game involves eight participants, each tasked with forming various strategic combinations for each round. A player has a "board," which is essentially where they strategically collect and acquire "champions" to create combinations. The game revolves around pitting each player's board against another's. Essentially, each participant faces another in 1v1 matches. With every loss, a participant loses health points, and the rate of health loss increases as the game progresses. When a player's health reaches zero, they are eliminated. The player with the strongest board and the best combinations will ultimately defeat the other seven players.

Players do not have unique IDs, but their final game positions serve as a kind of identifier since each position is unique within a single game. The database contains information about the level each participant reaches at the end of the game and how long they remain in it. The level determines the number of champions a player can place on their board. For example, a player at level 6 can only have 6 champions.

The "champions" are characters in the game, each with different attributes, abilities, and memberships in one or more combinations. There are 52 champions. Their attributes include cost (in gold), health, defense value, attack value, attack range, attack speed, ability name, and ability cost. Additionally, three identical champions can be merged to create a stronger version of that champion with combined attributes. This is referred to as the "star level," where merging three champions results in a star level 2 champion, and merging three star level 2 champions results in a star level 3 champion.

The combinations provide benefits to champions, increasing their strength and helping the player defeat others. There are 22 combinations, which function as follows: if a player places 2 or 3 champions from the same combination (called a "trait"), those champions will gain benefits and become stronger. Naturally, the more combinations and champions a board has, the higher the chances of victory.

Each champion can have up to three items equipped. Items are acquired throughout the game and can be assigned to any champion. Generally, items fall into four subcategories, which are not included in the database but help explain their utility. For instance, an item that increases health would be better suited for a champion positioned at the front of the board to better protect the others.

The data used will pertain to games played by players on the Korean server ranked in the top 16%. Each game has a unique ID.

Here are some useful links:

Database and more information about TFT: https://www.kaggle.com/datasets/gyejr95/league-of-legends-tftteamfight-tacticschampion
Official TFT website: https://teamfighttactics.leagueoflegends.com/pt-br/
Link to items, champions, and their traits: https://www.kaggle.com/datasets/gyejr95/league-of-legends-tftteamfight-tacticschampion/data?select=TFT_Champion_CurrentVersion.csv
