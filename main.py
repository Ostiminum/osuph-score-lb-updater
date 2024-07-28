import json
import requests
import ossapi
import gspread

RANKING_SPREADSHEET: gspread.Spreadsheet 

SCORE_RANK_API_URL = "https://score.respektive.pw/"

PH_PLAYERS = []

class PH_Player():

    username: str
    user_id: int
    user_avatar_url: str
    curr_ranked_score: int
    prev_ranked_score: int
    country_score_rank = -1
    global_score_rank = -1

    def __init__(self, user_stats: ossapi.models.UserStatistics):
        curr_user = user_stats.user

        self.username = curr_user.username
        self.user_id = curr_user.id
        self.user_avatar_url = curr_user.avatar_url
        self.curr_ranked_score = user_stats.ranked_score

    def __repr__(self):
        return f"PH_Player({self.username}, {self.user_id}, {self.user_avatar_url}, {self.curr_ranked_score}, #{self.global_score_rank} (#{self.country_score_rank}))"

def get_ph_players(osu_api_client: ossapi.Ossapi):
    ranking_iterator = None
    current_page_num = 1

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


def get_score_ranks():


if __name__ == '__main__':
    with open('creds.json') as osu_creds_file:
        creds = json.load(osu_creds_file)

    osu_client_id = creds['CLIENT_ID']
    osu_client_secret = creds['CLIENT_SECRET']

    osu_api_client = ossapi.Ossapi(osu_client_id, osu_client_secret)

    gsheets_client = gspread.service_account("gsheets_creds.json")   

    RANKING_SPREADSHEET = gsheets_client.open(creds['RANKING_SHEET'])

    # TODO:
    # [ ] 1.) store the previous rankings
    # [x] 2.) get the top 10k players in PH ranking
    # [x] 3.) sort them by ranked score
    # [ ] 4.) get top 10k PH players' global and country score rank
    # [ ] 4.) update ranking sheet
    # [ ] 5.) bing chilling

    get_ph_players(osu_api_client)
    PH_PLAYERS.sort(key=lambda player: player.curr_ranked_score, reverse=True)

    for player in PH_PLAYERS:
        print(player)