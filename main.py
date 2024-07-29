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
    prev_country_score_rank: int
    country_score_rank: int
    prev_global_score_rank: int
    global_score_rank: int

    country_score_rank_delta: int
    global_score_rank_delta: int

    ranked_score_gain: int

    def __init__(self, username="", user_id=0, user_avatar_url="", ranked_score=0, country_rank=0, user_stats=None):
        if user_stats is not None:
            curr_user = user_stats.user

            username = curr_user.username
            user_id = curr_user.id
            user_avatar_url = curr_user.avatar_url
            ranked_score = user_stats.ranked_score

        self.username = username
        self.user_id = user_id
        self.user_avatar_url = user_avatar_url
        self.ranked_score = ranked_score

        self.prev_country_score_rank = 0
        self.country_score_rank = 0
        self.prev_global_score_rank = 0
        self.global_score_rank = 0

        self.country_score_rank_delta = 0
        self.global_score_rank_delta = 0

        self.ranked_score_gain = 0

    def __repr__(self):
        return f"PH_Player({self.username}, {self.user_id}, {self.user_avatar_url}, {self.ranked_score}, #{self.global_score_rank} (#{self.country_score_rank}))"

# ----- UTILITY FUNCTIONS -----

def create_hyperlink_str(url, label):
    return f"=HYPERLINK(\"{url}\", {label})"


def create_sheet_values():
    values = []
    
    for player in PH_PLAYERS:
        player_avatar_image_str = f"IMAGE(\"{player.user_avatar_url}\")"
        player_profile_url = f"https://osu.ppy.sh/users/{player.user_id}/osu"

        values.append([
            f"#{player.country_score_rank}",
            player.country_score_rank_delta,
            f"(#{player.global_score_rank})" if player.global_score_rank != -1 else "-",
            create_hyperlink_str(player_profile_url, player_avatar_image_str),
            create_hyperlink_str(player_profile_url, f"\"{player.username}\""),
            player.ranked_score,
            player.ranked_score_gain
        ])

    return values
# -----------------------------


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

        for player_stats in ph_ranking.ranking:
            PH_PLAYERS.append(PH_Player(user_stats=player_stats))

        current_page_num += 1


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


def get_prev_ranking():
    

    starting_column = "B"
    ending_column = "H"

    starting_row = 2
    ending_row = 10000

    prev_ranking = CURR_RANKING_SHEET.get(
        f"{starting_column}{starting_row}:{ending_column}{ending_row}",
        value_render_option=gspread.utils.ValueRenderOption.formula
    )

    for record in prev_ranking:
        curr_player = PH_Player()

        country_score_rank_str, country_score_rank_delta, global_rank_str, user_avatar_hyperlink, username_hyperlink, ranked_score, ranked_score_gained_str = record

        user_id_str = user_avatar_hyperlink[user_avatar_hyperlink.find("users/")+6 : user_avatar_hyperlink.find("/osu\"")]
        avatar_url = user_avatar_hyperlink[user_avatar_hyperlink.find(", IMAGE(\"")+9 : user_avatar_hyperlink.rfind("\"))")]
        username = username_hyperlink[username_hyperlink.find(", \"")+3 : username_hyperlink.rfind("\")")]
        global_rank_str = global_rank_str[global_rank_str.find("(")+2 : global_rank_str.find(")")]

        curr_player.country_score_rank = int(country_score_rank_str[1:])
        curr_player.country_score_rank_delta = int(country_score_rank_delta)
        curr_player.global_score_rank = int(global_rank_str) if global_rank_str != '-' else 0
        curr_player.user_avatar_url = avatar_url
        curr_player.user_id = int(user_id_str)
        curr_player.username = username
        curr_player.ranked_score = ranked_score
        curr_player.ranked_score_gain = ranked_score_gained_str

        PREV_PH_PLAYERS.append(curr_player)

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
    
def calc_delta_stats():
    for curr_player in PH_PLAYERS:
        l = 0
        r = len(PREV_PH_PLAYERS)-1
        
        while l <= r:
            curr_index = (l+r)//2

            if curr_player.user_id == PREV_PH_PLAYERS[curr_index].user_id:
                curr_player.prev_country_score_rank = PREV_PH_PLAYERS[curr_index].country_score_rank
                curr_player.prev_global_score_rank = PREV_PH_PLAYERS[curr_index].global_score_rank
                curr_player.prev_ranked_score = PREV_PH_PLAYERS[curr_index].ranked_score

                curr_player.country_score_rank_delta = curr_player.prev_country_score_rank - curr_player.country_score_rank
                curr_player.global_score_rank_delta = curr_player.prev_global_score_rank - curr_player.global_score_rank
                curr_player.ranked_score_gain = curr_player.ranked_score - curr_player.prev_ranked_score
                
                break

            if curr_player.user_id > PREV_PH_PLAYERS[curr_index].user_id:
                l = curr_index + 1
            else:
                r = curr_index - 1

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

    get_prev_ranking()
    PREV_PH_PLAYERS.sort(key=lambda player: player.user_id)

    get_ph_players(osu_api_client)
    PH_PLAYERS.sort(key=lambda player: player.ranked_score, reverse=True)

    for curr_player_index in range(len(PH_PLAYERS)):
        PH_PLAYERS[curr_player_index].country_score_rank = curr_player_index + 1

    get_global_score_ranks()

    calc_delta_stats()

    update_ranking_sheet()

