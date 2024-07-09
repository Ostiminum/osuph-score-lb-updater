import json
import ossapi
import gspread

RANKING_SPREADSHEET: gspread.Spreadsheet 

def get_players(osu_api_client: ossapi.Ossapi):
    ph_players = []

    ranking_iterator = None
    current_page_num = 1
    current_score_rank = 1

    while True:
        score_ranking = osu_api_client.ranking(
            "osu",
            ossapi.RankingType.SCORE,
            cursor=ranking_iterator
        )

        ranking_iterator = score_ranking.cursor

        if ranking_iterator is None:
            break

        print(f"Visiting Page {current_page_num}...")

        for player in score_ranking.ranking:
            if player.user.country.code == "PH":
                ph_players.append((player, current_score_rank))

            current_score_rank += 1

        current_page_num += 1

    return ph_players


if __name__ == '__main__':
    with open('creds.json') as osu_creds_file:
        creds = json.load(osu_creds_file)

    osu_client_id = creds['CLIENT_ID']
    osu_client_secret = creds['CLIENT_SECRET']

    osu_api_client = ossapi.Ossapi(osu_client_id, osu_client_secret)

    gsheets_client = gspread.service_account("gsheets_creds.json")   

    # ph_players = get_players(osu_api_client)

    # print("PH Ranked Score Rankings")

    # for index in range(len(ph_players)):
    #     player, global_score_rank = ph_players[index]
    #     print(
    #         f"{index+1}.".ljust(4),
    #         f"({global_score_rank})".ljust(7),
    #         player.user.username.ljust(25),
    #         f"{player.ranked_score}".rjust(15)
    #     )

    RANKING_SPREADSHEET = gsheets_client.open(creds['RANKING_SHEET'])

    print(RANKING_SPREADSHEET.sheet1.get('A1'))

