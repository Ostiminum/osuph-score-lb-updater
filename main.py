import json
import ossapi

if __name__ == '__main__':
    with open('creds.json') as creds_file:
        creds = json.load(creds_file)

    client_id = creds['CLIENT_ID']
    client_secret = creds['CLIENT_SECRET']

    api_client = ossapi.Ossapi(client_id, client_secret)

    ph_players = []

    ranking_iterator = None
    current_page_num = 1
    current_score_rank = 1

    while True:
        score_ranking = api_client.ranking(
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

    print("PH Ranked Score Rankings")

    for index in range(len(ph_players)):
        player, global_score_rank = ph_players[index]
        print(
            f"{index+1}.".ljust(4),
            f"({global_score_rank})".ljust(7),
            player.user.username.ljust(25),
            f"{player.ranked_score}".rjust(15)
        )
