from fastapi import FastAPI, HTTPException
from utils import *
from models import models
from math import erf, sqrt
from fastapi.middleware.cors import CORSMiddleware
from scipy.stats import norm

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Acess-Control-Allow-Origin"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/evaluate_draft/")
async def evaluate_draft(champions: str, patch: str):
    champions_ordered = champions.split(",")
    params = None
    for patch_cluster in models:
        if patch in patch_cluster:
            params = models[patch_cluster]
    if params is None or len(champions_ordered) != 10:
        raise HTTPException(status_code=400, detail="Bad request")

    role_weights = load_role_weights(params)
    role_std = load_role_std(params)
    combinations_weights = load_combination_weights(params)

    matchups_matrix = {
        role: {
            roleM:
                get_from_combinations(
                    role, roleM, champions_ordered[role_index], champions_ordered[roleM_index]
                ) if role_index != roleM_index else get_rating(role, champions_ordered[role_index], patch)
            for roleM_index, roleM in enumerate(roles_ordered)
        }
        for role_index, role in enumerate(roles_ordered)
    }

    roles_predicted_performances = {
        r: {"Performance avg": 0, "Performance std": 0} for r in roles_ordered
    }

    for role in roles_ordered:
        roles_predicted_performances[role]["Performance avg"] = np.average(
            [matchups_matrix[role][roleM]["Performance avg"] for roleM in roles_ordered],
            weights=[combinations_weights[role][roleM] for roleM in roles_ordered]
        )
        roles_predicted_performances[role]["Performance std"] = np.sum(
            [matchups_matrix[role][roleM]["Performance std"] for roleM in roles_ordered]
        ) * np.abs(role_std[trim_role(role)])

    team1_performance_avg = np.average(
        [roles_predicted_performances[role]["Performance avg"] for role in roles_ordered[:5]],
        weights=[role_weights[trim_role(role)] for role in roles_ordered[:5]]
    )

    team2_performance_avg = np.average(
        [roles_predicted_performances[role]["Performance avg"] for role in roles_ordered[5:]],
        weights=[role_weights[trim_role(role)] for role in roles_ordered[5:]]
    )

    team1_performance_std = np.sum(
        [roles_predicted_performances[role]["Performance std"] for role in roles_ordered[5:]]
    )
    team2_performance_std = np.sum(
        [roles_predicted_performances[role]["Performance std"] for role in roles_ordered[:5]]
    )

    mu_team1_wins = team1_performance_avg - team2_performance_avg
    print(mu_team1_wins)
    std_team1_wins = np.sqrt(team1_performance_std**2 + team2_performance_std**2)
    print(std_team1_wins)
    # p_team1_wins = 1 - ((1 + (erf(z_value) / sqrt(2.0))) / 2.0)
    p_team1_wins = 1 - norm.cdf(0, loc=mu_team1_wins, scale=std_team1_wins)
    print(p_team1_wins)
    p_team2_wins = 1 - p_team1_wins
    return {
        'predicted_winner': int(p_team2_wins > p_team1_wins) + 1,
        'p_team1_wins': p_team1_wins,
        'p_team2_wins': p_team2_wins,
        'draft_matrix': matchups_matrix,
        'roles_predicted_performances': roles_predicted_performances,
        'team1_performance_avg': team1_performance_avg,
        'team2_performance_avg': team2_performance_avg,
        'team1_performance_std': team1_performance_std,
        'team2_performance_std': team2_performance_std,
        'combinations_weights': combinations_weights,
        'role_weights': [role_weights[r] for r in role_weights]
    }
