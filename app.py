from flask import Flask, render_template, request, abort, redirect, url_for

import db

app = Flask(__name__)

@app.route('/')
def index():
    stats = db.execute('''
        SELECT 
            (SELECT COUNT(*) FROM games) AS n_games,
            (SELECT COUNT(*) FROM champions) AS n_champions,
            (SELECT COUNT(*) FROM items) AS n_items
        ''').fetchone()
    
    return render_template('index.html', stats=stats)

@app.route('/games/')
def list_games():
    games = db.execute('SELECT * FROM games').fetchall()
    return render_template('games-list.html', games=games)

@app.route('/champions/')
def list_champions():
    champions = db.execute('SELECT * FROM champions ORDER BY Cost,Name ').fetchall()
    return render_template('champions-list.html', champions=champions)

@app.route('/items/')
def list_items():
    items = db.execute('SELECT * FROM items').fetchall()
    return render_template('items-list.html', items=items)
    
@app.route('/participants/')
@app.route('/participants/page/<int:page>')
def list_participants(page=1):
    per_page = 50 
    offset = (page - 1) * per_page

    query = '''
    SELECT GameId, Placement, Level, LastRound, InGameDuration/60.0 as InGameDurationMinutes
    FROM Participants
    ORDER BY GameId, Placement
    LIMIT ? OFFSET ?'''
    participants_raw = db.execute(query, [per_page, offset]).fetchall()
    participants = [dict(participant) for participant in participants_raw]

    total_entries = db.execute('SELECT COUNT(*) FROM Participants').fetchone()[0]
    total_pages = (total_entries // per_page) + (1 if total_entries % per_page > 0 else 0)

    return render_template('participants-list.html', participants=participants, page=page, total_pages=total_pages)


@app.route('/search/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        search_type = request.form.get('search_type')

        if search_type == 'game':
            return redirect(url_for('search_game', game_id=search_query))
        elif search_type == 'champion':
            return redirect(url_for('search_champion', champion_name=search_query))
        elif search_type == 'item':
            return redirect(url_for('search_item', item_name=search_query))
        elif search_type == 'board':
            participant_id = request.form.get('participant_id')
            if participant_id and 1 <= int(participant_id) <= 8:
                return redirect(url_for('search_board', game_id=search_query, placement_id=participant_id))
            else:
                flash('Participant ID must be between 1 and 8.')
                return redirect(url_for('search'))
        elif search_type == 'participant':
            return redirect(url_for('search_participants', game_id=search_query))
    
    return render_template('search.html')


@app.route('/search/game/<string:game_id>/')
def search_game(game_id):
    game_row = db.execute('SELECT * FROM games WHERE GameId = ?', [game_id]).fetchone()
    if not game_row:
        abort(404)
    game = dict(game_row)
    game['GameDuration'] = round(game['GameDuration'] / 60, 2)
    participants_raw = db.execute('''
        SELECT p.Placement, p.Level, p.InGameDuration
        FROM participants p
        WHERE p.gameId = ?
        ORDER BY p.placement ASC
    ''', [game_id]).fetchall()

    participants = [dict(row) for row in participants_raw]  # Convert each Row to a dict
   
    for participant in participants:
        participant['board_url'] = url_for('search_board', game_id=game_id, placement_id=participant['Placement'])
        participant['InGameDuration'] = round(participant['InGameDuration'] / 60, 2)


    return render_template('game-details.html', game = game,  participants=participants)


    
@app.route('/search/champion/<string:champion_name>/')
def search_champion(champion_name):
    # Converte o nome do campeão para minúsculas para a pesquisa na tabela champions
    champion_name_lower = champion_name.lower()

    # Consulta o campeão na base de dados na tabela champions com todos os detalhes
    champion = db.execute('SELECT * FROM champions WHERE Name = ?', [champion_name_lower]).fetchone()
    if not champion:
        abort(404)  # Campeão não encontrado

    try:
        # Converte o nome do campeão para ter a primeira letra maiúscula para a pesquisa na tabela board
        champion_name_capitalize = champion_name.capitalize()

        # Conta o número total de entradas para campeões na tabela board
        total_champion_entries = db.execute('SELECT COUNT(*) FROM board').fetchone()[0]

        # Conta o número de vezes que o campeão específico aparece na tabela board
        champion_count = db.execute('SELECT COUNT(*) FROM board WHERE championName = ?', [champion_name_capitalize]).fetchone()[0]

        if total_champion_entries > 0:
            # Calcula a porcentagem baseando-se no número total de entradas de campeões
            champion_percentage = (champion_count / total_champion_entries) * 100
        else:
            champion_percentage = 0
    except Exception as e:
        print(f"Erro ao calcular a porcentagem: {e}")
        champion_percentage = None

    try:
        # Consulta SQL para encontrar os 4 itens mais populares para o campeão com ID maior que 9
        popular_items = db.execute('SELECT Items.NAME, COUNT(Items.NAME) as Popularity FROM Board JOIN Items ON Board.items LIKE "%" || Items.ID || "%" WHERE Board.championName = ? AND Items.ID > 9 GROUP BY Items.NAME ORDER BY Popularity DESC LIMIT 3', [champion_name_capitalize]).fetchall()
    except Exception as e:
        print(f"Erro: {e}")
        popular_items = None

    
    return render_template('champion-details.html', champion=champion, champion_percentage=champion_percentage, popular_items=popular_items)

@app.route('/search/item/<string:item_name>/')
def search_item(item_name):
    item = db.execute('SELECT ID, NAME FROM items WHERE NAME = ?', [item_name]).fetchone()
    if not item:
        abort(404)

    item_id = item['ID']
    item_name = item['NAME']

    return render_template('item-details.html', item_id=item_id, item_name=item_name)

@app.route('/search/participants/<string:game_id>/')
def search_participants(game_id):
    participants = db.execute('SELECT GameId, Placement, Level, LastRound, InGameDuration/60.0 as InGameDurationMinutes FROM Participants WHERE GameId = ?', [game_id]).fetchall()
    return render_template('participants-details.html', participants=participants, game_id=game_id)



@app.route('/item_stats/<string:item_name>/')
def item_stats(item_name):
    # Buscar ID do item com base no nome do item
    item = db.execute('SELECT ID, NAME FROM items WHERE NAME = ?', [item_name]).fetchone()
    if not item:
        abort(404)

    item_id = str(item['ID'])

    # Criar padrões LIKE para a consulta
    like_pattern = f'%[{item_id},%'
    like_pattern_end = f'%,{item_id}]%'
    like_pattern_single = f'%[{item_id}]%'

    # Contar o número distinto de jogos onde o item aparece
    item_game_count = db.execute('''
        SELECT COUNT(DISTINCT gameId) FROM board
        WHERE items LIKE ? OR
              items LIKE ? OR
              items LIKE ?
    ''', (like_pattern, like_pattern_end, like_pattern_single)).fetchone()[0]

    # Contar o total de vezes que o item é usado
    total_item_count = db.execute('''
        SELECT SUM(total_items) FROM (
            SELECT COUNT(*) as total_items  
            FROM board
            WHERE items LIKE ? OR
                  items LIKE ? OR
                  items LIKE ?
            GROUP BY gameId, championName
        ) as item_count
    ''', (like_pattern, like_pattern_end, like_pattern_single)).fetchone()[0]

    # Encontrar o campeão mais frequente com este item
    most_frequent_champion = db.execute('''
        SELECT championName, COUNT(*) as count
        FROM board
        WHERE items LIKE ? OR
              items LIKE ? OR
              items LIKE ?
        GROUP BY championName
        ORDER BY count DESC
        LIMIT 1
    ''', (like_pattern, like_pattern_end, like_pattern_single)).fetchone()

    champion_name = most_frequent_champion['championName'] if most_frequent_champion else None

    # Calcular a média de uso do item por jogo
    total_games = db.execute('SELECT COUNT(*) FROM games').fetchone()[0]
    item_mean = total_item_count / total_games if total_games > 0 else 0

    return render_template('item-stats.html', item=item, item_game_count=item_game_count, item_mean=item_mean, champion_name=champion_name,total_item_count = total_item_count)

@app.route('/board/')
@app.route('/board/page/<int:page>')
def list_board(page=1):
    per_page = 100  # Número de entradas por página
    board_entries_raw = db.execute('SELECT * FROM board LIMIT ? OFFSET ?', [per_page, (page-1)*per_page]).fetchall()
    board_entries = [dict(entry) for entry in board_entries_raw] 

    # Tratar os dados para converter IDs de itens em nomes
    for entry in board_entries:
        item_ids = entry['items'].strip('[]').split(', ') 
        item_names = []
        for item_id in item_ids:
            if item_id: 
                item = db.execute('SELECT NAME FROM items WHERE ID = ?', [item_id]).fetchone()
                if item:
                    item_names.append(item['NAME'])
        entry['item_names'] = item_names

    total_entries = db.execute('SELECT COUNT(*) FROM board').fetchone()[0]
    total_pages = (total_entries // per_page) + (1 if total_entries % per_page > 0 else 0)

    return render_template('board-list.html', board_entries=board_entries, page=page, total_pages=total_pages)


@app.route('/board/<string:game_id>/<int:placement_id>/')
def search_board(game_id, placement_id):
    board_entries = db.execute('SELECT * FROM board WHERE gameId = ? AND placementId = ?', [game_id, placement_id]).fetchall()
    if not board_entries:
        abort(404)

    board_entries_dicts = []
    for entry in board_entries:
        entry_dict = dict(entry)
        item_ids = entry['items'].strip('[]').split(', ')
        items_with_names = []
        for item_id in item_ids:
            if item_id:
                item = db.execute('SELECT NAME FROM items WHERE ID = ?', [item_id]).fetchone()
                if item:
                    items_with_names.append(item['NAME'])
        entry_dict['item_names'] = items_with_names
        board_entries_dicts.append(entry_dict)

    trait_combinations = get_traits_by_champions(game_id,placement_id)
    print(trait_combinations)
    return render_template('board-details.html', board_entries=board_entries_dicts, trait_combinations = trait_combinations)

def get_traits_by_champions(game_id, placement_id):
    champions_raw = db.execute('SELECT championName FROM board WHERE gameId = ? AND placementId = ?', [game_id, placement_id]).fetchall()

    champion_names = [row['championName'] for row in champions_raw]

    trait_counts = {}
    for name in champion_names:
        name = name.lower()
        traits = db.execute('SELECT Traits FROM champions WHERE Name = ?', [name]).fetchone()

        if traits and traits['Traits']:
            for trait in traits['Traits'].split(','):
                trait_counts[trait] = trait_counts.get(trait, 0) + 1

    traits_with_champions = {trait: count for trait, count in trait_counts.items() if count > 0}

    return traits_with_champions

@app.route('/game/<string:game_id>/placement/<int:placement_id>/traits/')
def show_traits(game_id, placement_id):
    traits_with_champions = get_traits_by_champions(game_id, placement_id)
    return render_template('traits.html', traits_with_champions=traits_with_champions)

def get_popular_winner_traits():
    game_ids = db.execute('SELECT DISTINCT gameId FROM board WHERE placementId = 1').fetchall()
    game_ids = [row['gameId'] for row in game_ids]

    # Dictionary to track trait occurrences in winning games
    trait_occurrences = {}

    for game_id in game_ids:
        # Fetch traits for the winner of each game
        winner_traits = db.execute('''
            SELECT DISTINCT c.Traits
            FROM board b
            JOIN champions c ON LOWER(b.championName) = LOWER(c.Name)
            WHERE b.gameId = ? AND b.placementId = 1
        ''', [game_id]).fetchall()

        # Process traits for the game
        game_traits = set()
        for row in winner_traits:
            if row['Traits']:
                game_traits.update([trait.strip().lower() for trait in row['Traits'].split(',')])

        # Count each trait once per game
        for trait in game_traits:
            trait_occurrences[trait] = trait_occurrences.get(trait, 0) + 1

    # Calculate the percentage of each trait occurrence
    total_games = len(game_ids)
    trait_percentages = {trait: (count / total_games) * 100 for trait, count in trait_occurrences.items()}

    # Sort the traits by percentage in descending order
    sorted_traits_by_percentage = sorted(trait_percentages.items(), key=lambda item: item[1], reverse=True)

    # Return the top 4 traits
    return sorted_traits_by_percentage[:4]

@app.route('/winner-traits/')
def winner_traits():
    top_winner_traits = get_popular_winner_traits()
    return render_template('winner-traits.html', top_winner_traits=top_winner_traits)


def get_popular_winner_champions():
    # Fetch the unique game IDs where there are winners
    game_ids = db.execute('SELECT DISTINCT gameId FROM board WHERE placementId = 1').fetchall()
    game_ids = [row['gameId'] for row in game_ids]

    # Dictionary to track champion occurrences among winners
    champion_occurrences = {}

    # Process each game
    for game_id in game_ids:
        # Fetch the champion for the winner of each game
        winner_champion = db.execute('''
            SELECT DISTINCT b.championName
            FROM board b
            WHERE b.gameId = ? AND b.placementId = 1
        ''', [game_id]).fetchone()

        if winner_champion and winner_champion['championName']:
            champion_name = winner_champion['championName'].lower()  # Normalize the champion name
            champion_occurrences[champion_name] = champion_occurrences.get(champion_name, 0) + 1

    # Calculate the percentage of each champion occurrence
    total_games = len(game_ids)
    champion_percentages = {champion: (count / total_games) * 100 for champion, count in champion_occurrences.items()}

    # Sort the champions by percentage in descending order
    sorted_champions_by_percentage = sorted(champion_percentages.items(), key=lambda item: item[1], reverse=True)

    # Return the top 4 champions
    return sorted_champions_by_percentage[:4]

@app.route('/winner-champions/')
def winner_champions():
    top_winner_champions = get_popular_winner_champions()
    return render_template('winner-champions.html', top_winner_champions=top_winner_champions)
    
@app.route('/all-details/<string:game_id>/')
def all_details(game_id):
    query = '''
    SELECT 
        p.GameId,
        p.Placement,
        p.Level,
        b.championName,
        c.Cost,
        c.Health,
        c.Defense,
        c.Attack,
        c.Attack_range,
        c.Attack_Speed,
        c.DPS,
        c.Skill_Name,
        c.Skill_Cost,
        c.Traits,
        b.star AS ChampionLevel,
        b.items AS ChampionItems,
        g.GameDuration
    FROM 
        Participants p
    INNER JOIN Board b ON p.GameId = b.gameId AND p.Placement = b.placementId
    INNER JOIN Champions c ON LOWER(b.championName) = LOWER(c.Name)
    INNER JOIN Games g ON p.GameId = g.GameId
    WHERE
        p.GameId = ?
    '''
    # ...

    game_data = db.execute(query, [game_id]).fetchall()
    items = db.execute('SELECT ID, NAME FROM Items').fetchall()
    items_dict = {str(item['ID']): item['NAME'] for item in items}


    game_data_list = []
    for row in game_data:
        game_data_list.append(dict(row))

    for entry in game_data_list:
        if entry['ChampionItems']:  
            item_ids = entry['ChampionItems'].strip('[]').split(', ')
            item_names = [items_dict.get(item_id.strip(), 'Unknown Item') for item_id in item_ids if item_id.strip()]
            entry['ChampionItems'] = ', '.join(item_names)

    return render_template('all-details.html', game_data=game_data_list, game_id=game_id)
    
if __name__ == '__main__':
    app.run(debug=True)
