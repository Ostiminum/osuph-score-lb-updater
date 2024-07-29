import json
import ossapi
import gspread

RANKING_SPREADSHEET: gspread.Spreadsheet 
CURR_RANKING_SHEET: gspread.Worksheet
PREV_RANKING_SHEET: gspread.Worksheet

PREV_PH_PLAYERS = []
PH_PLAYERS = []

class PH_Player():

    username: str
    user_id: int
    user_avatar_url: str

    prev_ranked_score: int
    ranked_score: int
    prev_country_score_rank = -1
    country_score_rank = -1
    prev_global_score_rank = -1
    global_score_rank = -1

    country_score_rank_increment = 0
    global_score_rank_increment = 0

    ranked_score_gain = 0

    def __init__(self, user_stats: ossapi.models.UserStatistics):
        curr_user = user_stats.user

        self.username = curr_user.username
        self.user_id = curr_user.id
        self.user_avatar_url = curr_user.avatar_url
        self.ranked_score = user_stats.ranked_score

    def __repr__(self):
        return f"PH_Player({self.username}, {self.user_id}, {self.user_avatar_url}, {self.ranked_score}, #{self.global_score_rank} (#{self.country_score_rank}))"

def get_ph_players(osu_api_client: ossapi.Ossapi):
    ranking_iterator = None
    current_page_num = 1

    print("Currently browsing PH PERFORMANCE ranking.")

    while True:
        ph_ranking = osu_api_client.ranking(
            "osu",
            ossapi.RankingType.PERFORMANCE,
            country="PH",
            cursor=ranking_iterator
        )

        ranking_iterator = ph_ranking.cursor

        if ranking_iterator is None:
            break

        print(f"Visiting Page {current_page_num}...")

        for player in ph_ranking.ranking:
            PH_PLAYERS.append(PH_Player(player))

        current_page_num += 1

        break


def get_global_score_ranks():
    ranking_iterator = None
    current_page_num = 1
    current_ph_player_index = 0
    current_rank = 1

    print("Currently browsing SCORES ranking.")

    while True:
        global_score_ranking = osu_api_client.ranking(
            "osu",
            ossapi.RankingType.SCORE,
            cursor=ranking_iterator
        )

        ranking_iterator = global_score_ranking.cursor

        if ranking_iterator is None:
            break

        print(f"Visiting Page {current_page_num}...")

        for player in global_score_ranking.ranking:
            if (player.user.id == PH_PLAYERS[current_ph_player_index].user_id):
                PH_PLAYERS[current_ph_player_index].global_score_rank = current_rank
                current_ph_player_index += 1
            
            current_rank += 1
    
        current_page_num += 1

def create_sheet_values():
    values = []
    
    for player in PH_PLAYERS:
        player_avatar_image_str = f"IMAGE(\"{player.user_avatar_url}\")"

        values.append([
            f"#{player.country_score_rank}",
            player.country_score_rank_increment,
            f"(#{player.global_score_rank})" if player.global_score_rank != -1 else "-",
            f"=HYPERLINK(\"https://osu.ppy.sh/users/{player.user_id}/osu\", {player_avatar_image_str})",
            player.username,
            player.ranked_score,
            player.ranked_score_gain
        ])

    return values

def get_prev_ranking():
    starting_column = "B"
    ending_column = "H"

    starting_row = 2
    ending_row = f"{len(PH_PLAYERS) + starting_row}"

    prev_ranking = CURR_RANKING_SHEET.get(
        f"{starting_column}{starting_row}:{ending_column}{ending_row}",
        value_render_option=gspread.utils.ValueRenderOption.formula
    )

    # parsing for local stuff
    for record in prev_ranking:
        record


    PREV_RANKING_SHEET.update(
        prev_ranking,
        f"{starting_column}{starting_row}:{ending_column}{ending_row}",
        raw=False
    )


def update_ranking_sheet():
    starting_column = "B"
    ending_column = "H"

    starting_row = 2
    ending_row = f"{len(PH_PLAYERS) + starting_row}"

    CURR_RANKING_SHEET.update(
        create_sheet_values(),
        f"{starting_column}{starting_row}:{ending_column}{ending_row}",
        raw=False
    )
    

if __name__ == '__main__':
    with open('creds.json') as osu_creds_file:
        creds = json.load(osu_creds_file)

    osu_client_id = creds['CLIENT_ID']
    osu_client_secret = creds['CLIENT_SECRET']

    osu_api_client = ossapi.Ossapi(osu_client_id, osu_client_secret)

    gsheets_client = gspread.service_account("gsheets_creds.json")   

    RANKING_SPREADSHEET = gsheets_client.open(creds['RANKING_SHEET'])
    CURR_RANKING_SHEET = RANKING_SPREADSHEET.worksheet("Current")
    PREV_RANKING_SHEET = RANKING_SPREADSHEET.worksheet("Previous Update")

    # TODO:
    # [ ] 1.) store the previous rankings
    # [x] 2.) get the top 10k players in PH ranking
    # [x] 3.) sort them by ranked score
    # [x] 4.) get top 10k PH players' global and country score rank
    # [x] 4.) update ranking sheet
    # [ ] 5.) bing chilling

    get_prev_ranking()

    get_ph_players(osu_api_client)
    PH_PLAYERS.sort(key=lambda player: player.ranked_score, reverse=True)

    for curr_player_index in range(len(PH_PLAYERS)):
        PH_PLAYERS[curr_player_index].country_score_rank = curr_player_index + 1

    get_global_score_ranks()

    update_ranking_sheet()