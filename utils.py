import pandas as pd
import numpy as np

matchups = pd.read_csv('data/Matchups.csv')
synergies = pd.read_csv('data/Synergies.csv')
ratings = pd.read_csv('data/ratings.csv')
matchups = matchups.set_index(['champion', 'role', 'Matchup', 'Matchup Role'])
synergies = synergies.set_index(['champion', 'role', 'Synergy', 'Matchup Role'])
matchups = matchups.to_dict(orient='dict')
synergies = synergies.to_dict(orient='dict')
# avg, std, games = combs.loc[('Aatrox', 'JUNGLE', 'JarvanIV', 'TOP_LANE')][["Performance avg","Performance std","games"]]
combinations = {"Synergies": synergies, "Matchups": matchups}

ratings = ratings.set_index(['patch', 'name', 'role'])
ratings = ratings.to_dict(orient='dict')


def trim_role(role_ordered):
    return role_ordered.replace("_BLUE", "").replace("_RED", "")


def matchup_or_synergy(role, roleM):
    if role[-4:] == roleM[-4:]:
        return "Synergies"
    return "Matchups"


def get_from_combinations(role, roleM, champion, championM):
    k = (champion, trim_role(role), championM, trim_role(roleM))
    if k in combinations[matchup_or_synergy(role, roleM)]["Performance avg"]:
        return {
            "Performance avg": combinations[matchup_or_synergy(role, roleM)]["Performance avg"][k] if not np.isnan(
                combinations[matchup_or_synergy(role, roleM)]["Performance avg"][k]
            ) else 0,
            "Performance std": combinations[matchup_or_synergy(role, roleM)]["Performance std"][k] if not np.isnan(
                combinations[matchup_or_synergy(role, roleM)]["Performance std"][k]
            ) else 100,
            "games": combinations[matchup_or_synergy(role, roleM)]["games"][k]}
    else:
        return {"Performance avg": 0, "Performance std": 100, "games": 0}


def get_rating(role, champion, patch):
    k = (patch, champion, trim_role(role))
    return {
        "Performance avg": ratings["rel_rate"][k] if ratings["rel_rate"][k] != -1000 else 0,
        "Performance std": 2 * (1 / np.sqrt(ratings["games"][k])),
        "games": ratings["games"][k]
    }


roles_ordered = ['TOP_LANE_BLUE', 'JUNGLE_BLUE', 'MID_LANE_BLUE', 'BOT_LANE_BLUE', 'UTILITY_BLUE', 'TOP_LANE_RED',
                 'JUNGLE_RED', 'MID_LANE_RED', 'BOT_LANE_RED', 'UTILITY_RED']
role_labels = ['TOP_LANE', 'JUNGLE', 'MID_LANE', 'BOT_LANE', 'UTILITY']


def load_combination_weights(params):
    to_ret = {role: {roleM: None} for role in roles_ordered for roleM in roles_ordered}
    for index, role in enumerate(roles_ordered):
        for m_index, roleM in enumerate(roles_ordered):
            param_index = (index * 10) + m_index
            to_ret[role][roleM] = params[param_index]
    return to_ret


def load_role_weights(params):
    first = 100
    return {role: params[first + index] for index, role in enumerate(role_labels)}


def load_role_std(params):
    first = 105
    return {role: params[first + index] for index, role in enumerate(role_labels)}
