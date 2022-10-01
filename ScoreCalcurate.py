import math
import json
import os
import time
import elo

def GetRanking(cur):
    userinfo={}

    sql="select * from alltrackplaylist"
    cur.execute(sql)

    result=cur.fetchall()

    for i in result:
        player=(i[4],i[5])
        trackno=i[7]
        winner=i[10]
        loser=""

        if winner=="X":
            continue

        for p in player:
            if p in userinfo:
                pass
            else:
                userinfo[p]={
                    "score":2000,
                    "win":0,
                    "lose":0,
                    "winstrike":0,
                    "maxwinstrike":0,
                }

        userinfo[winner]["win"]+=1
        userinfo[winner]["winstrike"]+=1

        if userinfo[winner]["winstrike"]>userinfo[winner]["maxwinstrike"]:
            userinfo[winner]["maxwinstrike"]=userinfo[winner]["winstrike"]

        getscore=0

        bonus=0
        
        if winner==player[0]:
            score=elo.rate_1vs1(userinfo[player[0]]["score"],userinfo[player[1]]["score"])

            for st in range(1,userinfo[winner]["winstrike"]+1):
                bonus+=st-1
            
            bonus=bonus/100

            getScore=(score[0]-userinfo[player[0]]["score"])*(1+bonus)

            loser=player[1]
        else:
            score=elo.rate_1vs1(userinfo[player[1]]["score"],userinfo[player[0]]["score"])
            loser=player[0]

        
        userinfo[winner]["score"]+=getScore

        userinfo[loser]["score"]=score[1]
        userinfo[loser]["lose"]+=1
        userinfo[loser]["winstrike"]=0

    

    with open("카트 1대1 elo rating.json", "w", encoding="UTF-8") as jsonfile:
        json.dump(userinfo, jsonfile, indent=4)

    return userinfo