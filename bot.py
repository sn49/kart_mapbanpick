from calendar import month
import collections
from datetime import datetime
from typing import Iterable
from xmlrpc.client import DateTime
import nextcord
from nextcord.ext import commands, tasks
from nextcord.ext.commands.core import check
from nextcord.utils import get
import random
import asyncio
import os
import copy
import pymysql
import json
import csv
import ScoreCalcurate
import traceback
import imgkit


inputT = open("secret/bootmode.txt","r").read()

sqlinfo = open("secret/mysql.json", "r")
sqlcon = json.load(sqlinfo)

if inputT == "test":
    testmode = True
    database = pymysql.connect(
        user=sqlcon["user"],
        host=sqlcon["host"],
        db=sqlcon["testdb"],
        charset=sqlcon["charset"],
        password=sqlcon["password"],
        autocommit=True,
    )
elif inputT == "main":
    testmode = False
    database = pymysql.connect(
        user=sqlcon["user"],
        host=sqlcon["host"],
        db=sqlcon["db"],
        charset=sqlcon["charset"],
        password=sqlcon["password"],
        autocommit=True,
    )

cur = database.cursor()
intents = nextcord.Intents.all()

bot = commands.Bot(command_prefix="맵", intents=intents)

testmode = False

tokenfile = open("secret/token.txt", "r")
token = tokenfile.readlines()


@bot.event
async def on_ready():
    print("ready")


timemsg = None


async def timer(ctx):
    global maplist
    global turn
    global maplist
    global banlist
    global picklist
    global timemsg
    global order

    repeat_Time = 2
    second = 0

    second = 60

    corder = copy.deepcopy(order)

    while second > 0:
        await asyncio.sleep(repeat_Time)
        second -= repeat_Time

        if corder != order:
            return

        if bporder[order][0] == "r":
            break

        if timemsg == None:
            timemsg = await ctx.send(f"{second}초 남음")
        else:
            print("tetssetttt")
            await timemsg.edit(content=f"{second}초 남음")

        await asyncio.sleep(0.3)

    if corder != order:
        return
    
    await asyncio.sleep(3)

    if corder != order:
        return

    bpmanage("random", bporder[order][1])

    await SendMaplist(ctx)

    await ChangeTurn(ctx)


gomsg = None
ordermsg = None
userindex = None
banpickctx = None
istheremusic = False


@bot.event
async def on_reaction_add(reaction, user):
    global gomsg
    global part
    global banpickRole
    global ordermsg
    global turn
    global turnmsg
    global startIndex
    global userindex
    global isdbrecord
    global partid
    global istheremusic

    if reaction.message == gomsg:
        if not user.bot:
            if not user.id in partid:
                if reaction.emoji == "🖐️":
                    if len(part) == 1:

                        if isdbrecord:
                            sql = f"select nickname from user where discordid={user.id}"
                            cur.execute(sql)
                            res = cur.fetchone()

                            if res == None:
                                await reaction.message.channel.send("비회원입니다. true 미입력시 비회원으로 가능합니다.")
                                return
                            else:
                                part.append(res[0])
                                partid.append(user.id)

                        else:
                            part.append(user.display_name)
                            partid.append(user.id)

                        await user.add_roles(banpickRole)
                        await reaction.message.edit(content=f"{part}의 밴픽을 보고싶다면 😀를 눌러주세요.")
                        await reaction.message.add_reaction("😀")

                        try:
                            channel = banpickctx.author.voice.channel
                            await channel.connect()

                            music = 'speed' if round(random.random()) == 0 else 'item'

                            banpickctx.voice_client.stop()
                            source = nextcord.PCMVolumeTransformer(
                                nextcord.FFmpegPCMAudio(executable='music/ffmpeg.exe',
                                                        source=f'music/banpick_{music}.mp3'))
                            banpickctx.voice_client.play(source,
                                                         after=lambda e: print(f'Player error: {e}') if e else None)
                            istheremusic = True
                        except:
                            await reaction.message.channel.send("음성 채팅에 접속해있지 않아 음악을 재생하지 않습니다.")
                            istheremusic = False

                        await banpickStart(reaction.message.channel)
                    else:
                        await reaction.message.channel.send("이미 진행중인 밴픽이 있습니다.")
                        return


                elif reaction.emoji == "😀":
                    await newch.set_permissions(user, read_messages=True, send_messages=False)
                else:
                    await reaction.remove(user)
            else:
                await reaction.remove(user)
        return

    if reaction.message == ordermsg:
        if not user.bot:
            if user.id in partid:
                emojiList = ["🇦", "🇧", "🇷"]
                emojiIndex = emojiList.index(reaction.emoji)
                print(emojiIndex)

                if emojiIndex == 0 or emojiIndex == 1:
                    turn = emojiIndex
                else:
                    turn = random.randrange(0, 2)
                await ordermsg.delete()
                for i in range(len(maplist)):
                    maplist[i] = maplist[i].replace("\n", "")
                userindex = {}
                userindex["a"] = [part[turn], partid[turn]]

                if turn == 0:
                    turn = 1
                else:
                    turn = 0

                userindex["b"] = [part[turn], partid[turn]]
                userindex["r"] = ["random"]

                await SendMaplist(newch)
                print(userindex)
                turnmsg = await newch.send(f"{userindex[bporder[order][0]][0]}의 {bporder[order][1]}부터 시작")
                await timer(newch)


part = []
partid = []
maplist = []
banpicklist = []
turn = 0
order = 0
signch = None
bporder = None
isdbrecord = False
dbset = 0
dbround = 0


def bpmanage(usernick, mode, trackname=None,userid=0):
    global maplist
    global banpicklist
    global isdbrecord

    mapname = trackname

    trackno = 0
    if usernick == "random":
        mapname = random.choice(maplist)

    maplist.remove(mapname)

    bancount = len([x for x in banpicklist if x[2] == "ban"])
    print(bancount)

    if mode == "pick":
        trackno = len(banpicklist) - bancount + 1

    banpicklist.append([mapname, usernick, mode])

    

    if isdbrecord:
        banstring = ["", ""]

        if trackno == 0:
            banstring = [",winner,winrecord,loserecord", ",1,'X','X'"]

        sql = f"insert into alltrackplaylist (round,setno,year,month,player1,player2,trackno,trackname,picker{banstring[0]}) values ({dbround},{dbset},{int(str(datetime.now().year)[-2:])},{datetime.now().month},{partid[0]},{partid[1]},{trackno},'{banpicklist[-1][0]}',{userid}{banstring[1]})"
        print(sql)
        cur.execute(sql)


def checkbpofile(filename):
    try:
        tempbpo = []
        bpofile = open(f"bporder/{filename}.bpo", "r", encoding="utf-8")
        tempo = bpofile.readlines()

        count = {}

        for o in tempo:
            info = o.split(',')
            if info[0] == 'a' or info[0] == 'b' or info[0] == 'r':
                if info[1] == 'pick' or info[1] == 'ban':
                    if info[1] in count.keys():
                        count[info[1]] += 1
                    else:
                        count[info[1]] = 1
                    tempbpo.append([info[0], info[1]])
                else:
                    return False
            else:
                return False

        return tempbpo
    except:
        return False

@bot.command()
async def 역할정리(ctx, nickname=None):

    for role in ctx.guild.roles:
        if role.name=="밴픽":
            await role.delete()


@bot.command()
async def 가입(ctx):
    sql = f"insert ignore into user (discordid) values ({ctx.author.id})"
    print(sql)
    result = cur.execute(sql)
    print(result)

    if result > 0:
        await ctx.send("가입 완료")
    else:
        await ctx.send("이미 가입했습니다.")


# 밴픽 참가
@bot.command()
async def 신청(ctx, mapfilename=None, bpofilename=None, dbrecord=None, wround=None, wset=None):
    global part
    global maplist
    global gomsg
    global banpickRole
    global signch
    global bporder
    global isdbrecord
    global partid
    global dbset
    global dbround
    global banpickctx

    try:

        if str(dbrecord).lower() == "true":
            if wround == None or wset == None:
                await ctx.send("라운드와 세트를 입력해주세요")
                return

            dbset = int(wset)
            dbround = int(wround)

            sql = f"select count(discordid) from user where discordid={ctx.author.id}"
            cur.execute(sql)
            res = cur.fetchone()

            if res == 0:
                await ctx.send("비회원입니다. true 미입력시 비회원으로 가능합니다.")
                return

            part.append(ctx.author.display_name)
            partid.append(ctx.author.id)
            isdbrecord = True

        else:
            isdbrecord = False

        if mapfilename == None:
            datalist = os.listdir("maplist")
            senddata = ""
            for data in datalist:
                if ".maptxt" in data:
                    senddata += f"{data.replace('.maptxt', '')}\n"
            await ctx.send(senddata)
            return
        else:
            allmaplist = list(GetAllTrack().keys())



            if mapfilename.startswith("all"):
                
                if mapfilename.count("-")==0:
                    await ctx.send("all을 사용하려면 -를 사용하여 개수를 지정해주세요.")
                    return
                mapcount = int(mapfilename.split("-")[1])
                maplist = random.sample(allmaplist, mapcount)
            else:
                
                addcount=0

                if mapfilename.count("-")==1:
              
                    splitdata=mapfilename.split("-")
                    print(splitdata)
                    mapfilename=splitdata[0]
                    addcount = int(splitdata[1])

                # 맵추첨
                mapfile = open(f"maplist/{mapfilename}.maptxt", "r", encoding="UTF-8")
                maplist = mapfile.readlines()


                while addcount!=0:
                    print(addcount)
                    print(len(maplist))
                    addmaplist = random.sample(allmaplist, addcount)
                    
                    for track in addmaplist:
                        if not track in maplist :
                            addcount-=1
                            maplist.append(track)
                    

                    
            bporder = checkbpofile(bpofilename)

            if bporder == False:
                await ctx.send("올바른 밴픽 순서 파일이 아님")
                return

            if len(bporder) + 1 > len(maplist):
                await ctx.send(f"밴픽 {len(bporder)}개 가능, 하지만 맵리스트는 {len(maplist)}개(동일 개수일시, 마지막 맵은 자동선택과 다르지 않음)")
                return

            banpickRole = await ctx.guild.create_role(name='밴픽', permissions=nextcord.Permissions(0))
            await ctx.author.add_roles(banpickRole)

            if not isdbrecord:
                part.append(ctx.author.display_name)
                partid.append(ctx.author.id)

            if len(part) == 1:
                banpickctx = ctx
                gomsg = await ctx.send(
                    f"{ctx.author.display_name}의 {mapfilename} 밴픽에 참가할려면 🖐️이모지를 눌러주세요.(순서 : {bpofilename})")
                await gomsg.add_reaction("🖐️")
                signch = ctx.channel
            else:
                await ctx.send("이미 신청이 있습니다.")
    except:
        await EndBanPick()


banpickRole = None
newch = None
startIndex = None
sendmsg = None


async def banpickStart(ctx):
    global maplist
    global part
    global partid
    global turn
    global banpickRole
    global newch
    global startIndex
    global ordermsg

    newch = await ctx.guild.create_text_channel('밴픽')
    await newch.edit(category=gomsg.channel.category)
    selfbot = nextcord.utils.get(ctx.guild.members, id=bot.user.id)
    await selfbot.add_roles(banpickRole)
    await newch.set_permissions(banpickRole, read_messages=True)
    await newch.set_permissions(ctx.guild.default_role, read_messages=False)
    ordermsg = await newch.send(f"{part[0]}부터 시작 - 🇦\n{part[1]}부터 시작 - 🇧\n랜덤 시작 - 🇷")
    await ordermsg.add_reaction("🇦")
    await ordermsg.add_reaction("🇧")
    await ordermsg.add_reaction("🇷")

    random.shuffle(maplist)


@bot.command()
async def test(ctx):
    await ctx.send(ctx.author.mention)


@bot.command()
async def 기록(ctx, mapname=None, nickname=None, nickname2=None):
    try:
        if mapname == None:
            sql = """SELECT TABLE1.trackname,TABLE1.winner,TABLE1.winrecord FROM alltrackplaylist AS TABLE1,(SELECT trackname,winner,MIN(winrecord) AS min_sort FROM alltrackplaylist GROUP BY trackname) AS TABLE2 WHERE TABLE1.winrecord=TABLE2.min_sort AND TABLE1.trackname = TABLE2.trackname AND NOT table1.winner=1"""
            cur.execute(sql)
            result = cur.fetchall()
            sendtext = "```"

            index = 0

            for i in result:
                sendtext += f"{'%-20s' % i[0]}\t{'%-9s' % i[1]}\t{'%-9s' % i[2]}\n"
                index += 1
                if index % 20 == 0:
                    sendtext += "```"
                    await ctx.send(sendtext)
                    sendtext = "```"
            sendtext += "```"
            await ctx.send(sendtext)
            return

        sendtext = ""

        if mapname=="file":
            sendtext="```"
            tracklist=open(nickname+".maptxt","r",encoding="UTF-8").readlines()

            for track in tracklist:
                track=track.replace('\n','')
                sql=f"""SELECT TABLE1.trackname,TABLE1.winner,TABLE1.winrecord FROM alltrackplaylist AS TABLE1,(SELECT trackname,winner,MIN(winrecord) AS min_sort FROM alltrackplaylist GROUP BY trackname) AS TABLE2 WHERE TABLE1.winrecord=TABLE2.min_sort AND TABLE1.trackname = TABLE2.trackname AND TABLE1.trackname='{track}'"""

                cur.execute(sql)

                res=cur.fetchone()
                print(track)
                user=ctx.guild.get_member(res[1])
                
                if user!=None:
                    
                    sendtext+=f"{'%-20s' % track} {'%-9s' % user.display_name} {res[2]}\n"
                else:
                    sendtext+=f"{'%-20s' % track} {'%-9s' %'기록 없음'}\n"
            sendtext+="```"
            await ctx.send(sendtext)
            return

            

        if nickname == None:
            # 카운트 해야할것 : 픽 횟수, 밴 횟수, 랜덤 픽 횟수, 랜덤 밴 횟수
            # 찾아야 할것 : 최고기록

            randomban = 0
            ban = 0
            randompick = 0
            pick = 0

            cant = 0
            random_cant = 0

            # 랜덤 밴 횟수
            sql = f"""SELECT COUNT(*) FROM alltrackplaylist WHERE trackname="{mapname}" and picker="random" AND trackno=0"""

            cur.execute(sql)

            randomban = cur.fetchone()[0]

            # 랜덤 픽 횟수
            sql = sql.replace("no=", "no!=")

            print(sql)
            cur.execute(sql)

            randompick = cur.fetchone()[0]

            # 픽 횟수
            sql = sql.replace("ker=", "ker!=")
            cur.execute(sql)

            pick = cur.fetchone()[0]

            # 밴 횟수
            sql = sql.replace("no!=", "no=")
            cur.execute(sql)

            ban = cur.fetchone()[0]

            # 최고기록

            bestrecord = {
                "year": "",
                "month": "",
                "round": "",
                "setno": "",
                "trackno": "",
                "player": "",
                "opponent": "",
                "record": "9'59'999"
            }

            sql = f'''SELECT * FROM alltrackplaylist WHERE trackname="{mapname}" and winner!="X" AND trackno!=0 order by winrecord asc LIMIT 1'''

            cur.execute(sql)

            res = cur.fetchone()

            if res != None:
                bestrecord = {
                    "year": res[1],
                    "month": res[2],
                    "round": res[3],
                    "setno": res[6],
                    "trackno": res[7],
                    "player": res[10],
                    "opponent": "",
                    "record": res[11]
                }

                if bestrecord["player"] == res[4]:
                    bestrecord["opponent"] = res[5]
                else:
                    bestrecord["opponent"] = res[4]

                bestrecord["record"]: res[11]

            sendtext = f"{mapname.replace('_', ' ')}\n픽 {pick}회({cant}회 못함)\n밴 {ban}회\n랜덤밴 {randomban}회\n랜덤픽 {randompick}회({random_cant}회 못함)"

            if bestrecord['record'] != "9'59'999":
                sendtext += f"\n최고 기록 {bestrecord['record']} by {bestrecord['player']}\n{bestrecord['year']}년 {bestrecord['month']}월 {bestrecord['round']}라운드 vs {bestrecord['opponent']} {bestrecord['setno']}세트 {bestrecord['trackno']}트랙"
        else:
            nickname=int(nickname)
            if nickname2 == None:
                if nickname == "all":
                    sql = f""
                    sql = f"select nickname,bestrecord from track_{mapname}"
                    cur.execute(sql)
                    i = cur.fetchall()
                    sendtext = "```"
                    for info in i:
                        sendtext += f"{info[0]} - {info[1]}\n"
                    sendtext += "```"
                    await ctx.send(sendtext)
                    return
                else:
                    
                    #금방 구하는거
                    #픽 횟수(승리, 패배, 못함)
                    sql=f"SELECT count(id) FROM alltrackplaylist WHERE trackname='{mapname}' AND picker={nickname} AND trackno!=0"
                    cur.execute(sql)
                    
                    pick=cur.fetchone()[0]


                    #밴 횟수
                    sql=f"SELECT count(id) FROM alltrackplaylist WHERE trackname='{mapname}' AND picker={nickname} AND trackno=0"

                    cur.execute(sql)
                    
                    ban=cur.fetchone()[0]


                    #랜덤밴 횟수
                    sql=f"SELECT count(id) FROM alltrackplaylist WHERE trackname='{mapname}' AND picker=0 AND trackno=0 and (player1={nickname} or player2={nickname})"

                    cur.execute(sql)
                    
                    randomban=cur.fetchone()[0]



                    #랜덤픽 횟수
                    sql=f"SELECT count(id) FROM alltrackplaylist WHERE trackname='{mapname}' AND picker=0 AND trackno!=0 and (player1={nickname} or player2={nickname})"

                    cur.execute(sql)
                    
                    randompick=cur.fetchone()[0]

                    #승,패


                    #어려운거
                    #최고기록과 언제 했는지
                    bestrecordsql=f"SELECT * FROM (SELECT year,month,round,player1,player2,setno,trackno, IF(winner = {nickname}, winrecord, loserecord) AS record FROM kart1v1.alltrackplaylist WHERE trackname ='{mapname}' AND winner != 1 AND {nickname} IN (player1, player2)) res ORDER BY record LIMIT 1"

                    cur.execute(bestrecordsql)

                    bestrecord_res=cur.fetchone()




                    
                    sendtext = f"{mapname}\n픽 {pick}회\n - 승리 i[2]회\n - 패배 i[3]회\n - 못함 i[1] - i[2] - i[3]회\n밴{ban}회\n랜덤밴 {randomban}회\n랜덤픽{randompick}회\ni[7]승 i[8]패\n최고 기록 : {bestrecord_res[7]}\n{bestrecord_res[0]}년 {bestrecord_res[1]}월 {bestrecord_res[2]}라운드 {bestrecord_res[3]} vs {bestrecord_res[4]} {bestrecord_res[5]}세트 {bestrecord_res[6]}트랙"
            else:
                nickname2=int(nickname2)    
                sendtext = "```"
                sql = f"SELECT trackno,picker,winner FROM alltrackplaylist WHERE ((player1={nickname} AND player2={nickname2}) OR (player1={nickname2} AND player2={nickname})) AND trackname='{mapname}'"
                print(sql)
                cur.execute(sql)
                i = cur.fetchall()

                if len(i) == 0:
                    await ctx.send("기록이 없거나 잘못된 트랙 이름입니다.")
                    return

                pick = [0, 0]
                ban = [0, 0]
                win = [0, 0]
                cant = [0, 0]
                r_pick = 0
                r_ban = 0

                for info in i:
                    if info[0] == 0:  # 밴한 트랙
                        if "random" == info[1]:
                            r_ban += 1
                        elif nickname == info[1]:
                            ban[0] += 1
                        else:
                            ban[1] += 1
                    else:  # 픽한 트랙
                        iscant = False
                        if info[2] == "X" or info[2] == "x":  # 세트가 끝나 못한 트랙
                            iscant = True
                        if "random" == info[1]:  # 랜덤픽
                            r_pick += 1
                        elif nickname == info[1]:  # 랜덤픽 아닌경우
                            pick[0] += 1
                            if iscant:
                                cant[0] += 1
                        else:
                            pick[1] += 1
                            if iscant:
                                cant[1] += 1

                    if not info[2] == "X" or info[2] == "x":
                        if nickname == info[2]:
                            win[0] += 1
                        else:
                            win[1] += 1

                sendtext = f"```{mapname}\n{nickname} vs {nickname2}\n"
                sendtext += f"픽 {pick[0]}({cant[0]}회 못함) : {pick[1]}({cant[1]}회 못함)\n"
                sendtext += f"밴 {ban[0]} : {ban[1]}\n"
                sendtext += f"랜덤밴 {ban[0]}\n"
                sendtext += f"랜덤픽 {ban[0]}\n"
                sendtext += f"승리 {win[0]} : {win[1]}```"

                await ctx.send(sendtext)
                return

        await ctx.send(sendtext)
    except Exception as e:
        await ctx.send("기록이 없는 트랙입니다."+f"\n{str(traceback.format_exc())}")


@bot.command()
async def 전적(ctx, nick1=None, nick2=None):
    try:
        if nick1 == None:
            await ctx.send("nickname을 입력해주세요.")
            return
        
        nick1=int(nick1)

        sendtext = ""

        player1 = {"track": 0, "set": 0, "game": 0}
        player2 = {"track": 0, "set": 0, "game": 0}
        tempscore = {"track": {"player1": 0, "player2": 0}, "set": {"player1": 0, "player2": 0}}

        tempset = -1

        if nick2 == None:
            trackwinsql = f"""select COUNT(winner) from alltrackplaylist WHERE winner={nick1} AND (player1={nick1} OR player2={nick1})"""
            cur.execute(trackwinsql)

            res = cur.fetchone()

            player1["track"] = res[0]

            tracklosesql = f"""select COUNT(winner) from alltrackplaylist WHERE winner!='{nick1}' AND winner!=1 AND (player1={nick1} OR player2={nick1})"""
            cur.execute(tracklosesql)

            res = cur.fetchone()

            player2["track"] = res[0]

            setsql = f"""SELECT winner,COUNT(winner) FROM (SELECT YEAR, MONTH, ROUND, setno,winner,COUNT(winner) AS trackscore from alltrackplaylist WHERE (player1={nick1} or player2={nick1}  ) and winner != 1 GROUP BY YEAR, MONTH, ROUND, setno,winner,player1,player2) res WHERE trackscore>=4 GROUP BY winner"""

            cur.execute(setsql)

            res = cur.fetchall()

            for i in res:
                if i[0] == nick1:
                    player1["set"] = i[1]
                else:
                    player2["set"] += i[1]

            gamewinsql = f"""SELECT COUNT(*) FROM(SELECT YEAR, MONTH, ROUND, player1, player2, COUNT(*) as setscore FROM(SELECT YEAR, MONTH, ROUND, setno, player1, player2, COUNT(winner) AS trackscore FROM alltrackplaylist WHERE({nick1} IN (player1, player2))AND winner={nick1} GROUP BY YEAR, MONTH, ROUND, setno, player1, player2)res WHERE trackscore>=4 GROUP BY YEAR, MONTH, ROUND, LEAST(player1, player2), GREATEST(player1, player2))res WHERE setscore>=2"""

            cur.execute(gamewinsql)

            res = cur.fetchone()

            player1["game"] = res[0]

            gamelosesql = gamewinsql.replace(f"winner={nick1}", f"winner not in ({nick1},1)")

            print(gamelosesql)

            cur.execute(gamelosesql)

            res = cur.fetchone()

            player2["game"] = res[0]

            sendtext = f"{nick1}\n{player1['game']}승 {player2['game']}패\n세트 {player1['set']}승 {player2['set']}패\n트랙 {player1['track']}승 {player2['track']}패"
        else:
            nick2=int(nick2)
            tracksql = f"""select winner,COUNT(winner) from alltrackplaylist WHERE ({nick1} IN (player1, player2) AND {nick2} IN (player1, player2)) AND winner!=1 GROUP BY winner"""

            cur.execute(tracksql)

            res = cur.fetchall()

            for i in res:
                if i[0] == nick1:
                    player1["track"] = i[1]
                else:
                    player2["track"] = i[1]

            setsql = f"""SELECT winner,COUNT(winner) FROM (SELECT YEAR, MONTH, ROUND, setno,winner,COUNT(winner) AS trackscore from alltrackplaylist WHERE ({nick1} IN (player1, player2) AND {nick2} IN (player1, player2)) and winner != 1 GROUP BY YEAR, MONTH, ROUND, setno,winner) res WHERE trackscore>=4 GROUP BY winner"""

            cur.execute(setsql)

            res = cur.fetchall()

            for i in res:
                if i[0] == nick1:
                    player1["set"] = i[1]
                else:
                    player2["set"] = i[1]

            gamesql = f"""SELECT COUNT(*) FROM (SELECT * FROM (SELECT YEAR, MONTH, ROUND, setno,winner,COUNT(winner) AS trackscore from alltrackplaylist WHERE ({nick1} IN (player1, player2) AND {nick2} IN (player1, player2)) and winner != 1 GROUP BY YEAR, MONTH, ROUND, setno,winner) res WHERE trackscore>=4 AND winner="...winner..." GROUP BY year,month,ROUND HAVING COUNT(*)>=2) res"""

            cur.execute(gamesql.replace("...winner...", str(nick1)))

            res = cur.fetchone()

            player1["game"] = res[0]

            cur.execute(gamesql.replace("...winner...", str(nick2)))

            res = cur.fetchone()

            player2["game"] = res[0]

            # 나중에 기록 차이 구하기

            # recordsql=f"select winner,winrecord, loserecord from alltrackplaylist where ('{nick1}' IN (player1, player2) AND '{nick2}' IN (player1, player2))"

            # res=cur.fetchall()

            # for i in res:
            #     winrecord=
            #     if i[0]==nick1:
            #         player1["set"]=i[1]
            #     else:
            #         player2["set"]=i[1]

            sendtext = f"{nick1} vs {nick2}\n{player1['game']} : {player2['game']}\n세트 {player1['set']} : {player2['set']}\n트랙 {player1['track']} : {player2['track']}\n평균 기록 차이 : 업데이트 예정"
        await ctx.send(sendtext)
    except Exception as e:
        await ctx.send(str(e)+"\n디코 유저id를 입력해주세요.")


@bot.command()
async def bpocheck(ctx, bpofilename=None):
    print(bpofilename)
    banpickorder = checkbpofile(bpofilename)

    playera = {"ban": 0, "pick": 0}
    playerb = {"ban": 0, "pick": 0}

    for turn in banpickorder:
        if turn[0] == "a":
            if turn[1] == "pick":
                playera["pick"] += 1
            else:
                playera["ban"] += 1
        elif turn[0] == "b":
            if turn[1] == "pick":
                playerb["pick"] += 1
            else:
                playerb["ban"] += 1

    await ctx.send(
        f'''playera pick-{playera["pick"]}회 ban{playera["ban"]}회\nplayerb pick-{playerb["pick"]}회 ban{playerb["ban"]}회''')


@bot.command()
async def 랜덤맵(ctx,mapfilename="all",dbsave="False"):

    try:
        sendtext=""
        maplist=None

        if mapfilename=="all":
            maplist = list(GetAllTrack().keys())
            

            
        else:
            #맵리스트 파일에서 뽑아오기            
            mapfile = open(f"maplist/{mapfilename}.maptxt", "r", encoding="UTF-8")
            maplist = mapfile.readlines()

        maplist = random.sample(maplist, 7)

        sendtext = "```"

        index = 1



        for track in maplist:
            track=track.replace('\n','')
            sendtext += f"track{index}  {track}\n"

            if str.lower(dbsave)=="true":
                year=None
                month=None
                round=None
                player1=None
                player2=None
                if index==1:
                    sql=f"""select year,month,round,player1,player2,setno from alltrackplaylist order by id desc limit 1"""
                    cur.execute(sql)
                    res=cur.fetchone()
                    year=res[0]
                    month=res[1]
                    round=res[2]
                    player1=res[3]
                    player2=res[4]
                    setno=res[5]

                    if setno!=2:
                        await ctx.send("3세트를 진행하고 있을때에만 DB저장을 할 수 있습니다.")
                        return
                    
                sql=f"""insert into alltrackplaylist (year,month,round,player1,player2,picker) values ('{year}','{month}','{round}','{player1}','{player2}','random')"""

                cur.execute(sql)
            index += 1

        sendtext += "```"

        await ctx.send(sendtext)
    except Exception as e:
        print(e)


async def ChangeTurn(ctx):
    global order
    global turn
    global signch
    global startIndex

    global bporder

    global dbround
    global dbset

    global isdbrecord

    order += 1
    sendlist = ["change"]

    if order == len(bporder):
        for bp in banpicklist:
            if bp[2] == "pick":
                sendlist.insert(sendlist.index("change"), bp)
            else:
                sendlist.append(bp)

        print(f"sendlist : {sendlist}")

        sendtext = f"```round{dbround} {dbset}set\n\n픽 리스트\n"

        trackno = 0

        for bp in sendlist:
            if bp == "change":
                sendtext += f"\n밴 리스트\n"
            else:

                if bp[2] == "pick":
                    trackno += 1
                    sendtext += f"track{trackno} - "

                sendtext += f"{bp[0]} - {bp[1]}\n"

        sendtext += "```"
        await signch.send(f"{sendtext}")

        if istheremusic:
            banpickctx.voice_client.stop()
            source = nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(executable='music/ffmpeg.exe', source='music/game_start.mp3'))
            banpickctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

        await EndBanPick()
        return

    await NoticeTurn(ctx)

    await timer(ctx)


async def EndBanPick(is_banpick_completed=True):
    try:
        global part
        global partid
        global banpicklist
        global maplist
        global turn
        global order
        global banpickRole
        global newch
        global gomsg

        global bporder
        global sendmsg
        global timemsg

        global dbround
        global dbset

        await gomsg.delete()
        await newch.delete()
        await banpickRole.delete()

        if is_banpick_completed:
            await asyncio.sleep(14)

        if istheremusic:
            banpickctx.voice_client.stop()
            await banpickctx.voice_client.disconnect()

        part.clear()
        partid.clear()
        maplist.clear()
        banpicklist.clear()
        turn = 0
        order = 0
        sendmsg = None
        timemsg = None

        dbround = 0
        dbset = 0
    except:
        pass


@bot.command()
async def 취소(ctx):
    await EndBanPick(is_banpick_completed=False)


# 맵 픽
@bot.command()
async def 픽(ctx, index=None):
    global maplist
    global banpicklist
    global order
    global turn
    global userindex
    global isdbrecord

    if bporder[order][1]=="ban":
        await ctx.send("밴을 할 차례입니다.")
        return

    await ctx.message.delete()

    if ctx.author.id != userindex[bporder[order][0]][1]:
        await ctx.send("상대의 차례입니다.")
        return

    if index == None:
        await ctx.send("맵 번호를 입력해주세요.")
        return

    mapname = maplist[int(index) - 1]

    print(userindex)
    print(bporder)
    print(order)

    bpmanage(ctx.author.display_name, bporder[order][1], mapname,ctx.author.id)

    await SendMaplist(ctx)

    await ChangeTurn(ctx)

    await NoticeTurn(ctx)

# 맵 밴
@bot.command()
async def 밴(ctx, index=None):
    global maplist
    global banpicklist
    global order
    global turn
    global userindex
    global isdbrecord

    if bporder[order][1]=="pick":
        await ctx.send("픽을 할 차례입니다.")
        return

    await ctx.message.delete()

    if ctx.author.id != userindex[bporder[order][0]][1]:
        await ctx.send("상대의 차례입니다.")
        return

    if index == None:
        await ctx.send("맵 번호를 입력해주세요.")
        return

    mapname = maplist[int(index) - 1]

    print(userindex)
    print(bporder)
    print(order)

    bpmanage(ctx.author.display_name, bporder[order][1], mapname,ctx.author.id)

    await SendMaplist(ctx)

    await ChangeTurn(ctx)

    await NoticeTurn(ctx)


turnmsg = None


async def SendMaplist(ctx):
    global maplist
    global bporder
    global order
    global banpicklist
    global sendmsg

    sendlist = ["change"]

    index = 1
    sendtext = f"```"

    for track in maplist:
        sendtext += f"{index}  {track}\n"
        index += 1

    for bp in banpicklist:
        if bp[2] == "pick":
            sendlist.insert(sendlist.index("change"), bp)
        else:
            sendlist.append(bp)

    print(f"sendlist : {sendlist}")

    sendtext += f"\n픽 리스트\n"

    for bp in sendlist:
        if bp == "change":
            sendtext += f"\n밴 리스트\n"
        else:
            sendtext += f"{bp[0]} - {bp[1]}\n"

    sendtext += "```"

    if sendmsg == None:
        sendmsg = await ctx.send(sendtext)
    else:
        await sendmsg.edit(content=sendtext)


async def NoticeTurn(ctx):
    global turnmsg

    if turnmsg == None:
        await turnmsg.edit(f"{userindex[bporder[order][0]][0]}의 **{bporder[order][1]}**을 할 차례")
    else:
        await turnmsg.edit(content=f"{userindex[bporder[order][0]][0]}의 **{bporder[order][1]}**을 할 차례")


def GetAllTrack():
    allmaplist = {}
    datalist = os.listdir("maplist/speed")
    senddata = ""
    for data in datalist:
        if data.endswith(".maptxt") and not "item" in data:
            mapfile = open("maplist/speed/" + data, "r", encoding="UTF-8")
            for track in mapfile.readlines():
                temp = track.replace("\n", "")
                if not temp in allmaplist:
                    allmaplist[temp]=[data]
                else:
                    allmaplist[temp].append(data)
    return allmaplist

@bot.command()
async def web(ctx):
    allmaplist = GetAllTrack()

    print(list(allmaplist))

    sortlist=[]
    maxnum=0
    for i in allmaplist:
        index=0
        for j in sortlist:
            count=len(allmaplist[i])
            if count<=len(j[1]):
                index+=1
            if count>maxnum:
                maxnum=count
        sortlist.insert(index,[i,allmaplist[i]])
    print(f"manum {maxnum}")

    htmlfile=open("kart1v1allmap.html","w",encoding="UTF-8")

    htmlfile.write('''<head><style>table,tr,td{border: 1px solid black; vertical-align : top; padding: 15px; border-spacing: 15px;} body{background-color:F38181}</style><meta charset="UTF-8"></head>''')

    count=0

    htmlfile.write("<body><table bgcolor=#FCE38A>")

    for key,value in sortlist:
        count+=1
        if count%3==1:
            htmlfile.write("<tr>")
        ratio=len(value)/float(maxnum)

        print(ratio)

        color_rgb=[98,191,174]

        #color code = #95E1D3
        colorstr=f'''style="background-color: rgb({255-(255-color_rgb[0])*ratio},{255-(255-color_rgb[1])*ratio},{255-(255-color_rgb[2])*ratio})"'''

        # colorstr=f"bgcolor=#95E1D3"
        print(colorstr)
        
        htmlfile.write(f"<td {colorstr}>")
        htmlfile.write(f"<h1>{key}</h1><br>")
        
        htmlfile.write(f"<br><br><details><summary>{len(value)}회 채택</summary>")
        for i in value:
            i=i.replace(".maptxt","")
            i=i.replace("y","")
            i=i.replace("m","년 ")
            i=i.replace("_","월 ")
            
            htmlfile.write(f"{i}<br>")
        htmlfile.write("</details>")
        htmlfile.write("</td>")
        if count%3==0:
            htmlfile.write("</tr>")
    

    htmlfile.write("</table></body>")
    htmlfile.close()


    await ctx.send(files=[nextcord.File("kart1v1allmap.html")])

@bot.command()
async def 리스트(ctx, mapfilename=None,mode=None):
    if mapfilename == None:
        datalist = os.listdir("maplist/speed")
        senddata = ""
        for data in datalist:
            if data.endswith(".maptxt"):
                senddata += f"{data.replace('.maptxt', '')}\n"
        await ctx.send(senddata)
        return
    elif mapfilename == "all":
        
        allmaplist = GetAllTrack()
        tempmaplist=list(allmaplist.keys())
        if mode=="random":
            random.shuffle(tempmaplist)
        embed=nextcord.Embed()
        for i in enumerate(tempmaplist):
            i=list(i)
            print(i)
            print(i[0]+1)

            print(allmaplist[i[1]])
            
            title = f"{i[0]+1} : {i[1]}\n"
            value=""
            count=0
            for fn in enumerate(allmaplist[i[1]]):
                
                if mode=="y22":
                    if not fn[1].startswith("y22"):
                        continue
                count+=1 
                fn=list(fn)
                value+=f"""{fn[1].replace(".maptxt","")},"""
                if fn[0]%2==1:
                    value+="\n"
                
            value+=f"\n{count}회 채택\n\n"
            if count!=0:
                embed.add_field(name=title,value=value)
            value=""
            if i[0] % 24 == 23:
                await ctx.send(embed=embed)
                embed=nextcord.Embed()

        await ctx.send(embed=embed)
        sendtext = "이중 14개 추첨"
        await ctx.send(sendtext)
        return

    # 맵추첨
    mapfile = open(f"maplist/{mapfilename}.maptxt", "r", encoding="UTF-8")
    maplist = mapfile.read()
    await ctx.send("```" + maplist + "```")


owner = json.load(open("owner.json", "r"))


@bot.command()
async def 평가(ctx, mapfilename=None):
    if owner["owner"] == ctx.author.id:

        mapfile = open(f"votelist/{mapfilename}.maptxt", "r", encoding="UTF-8")
        maplist = mapfile.readlines()

        result = random.sample(maplist, 3)

        sendtext = "```"
        for i in result:
            i = i.replace('\n', '')
            sendtext += f"{i}\n"

        await ctx.send(f"{sendtext}```")
    else:
        await ctx.send("권한이 없습니다.")

@bot.command()
async def 승리(ctx, win=None, lose=None):
    #멘션의 id를 확인

    #승리 기록 안된 매치id 확인



    #player1과 player2에 멘션id가 있는지 확인
    sql=f"select * from alltrackplaylist where "

    #있다면 DB에 기록
    sql=f""

    cur.execute(sql)
    return


@bot.command()
async def 랭킹(ctx, nickname=None):
    ranklist = []

    alldata = ScoreCalcurate.GetRanking(cur,bot)

    for user in alldata.keys():

        rank = 0
        for data in ranklist:
            if data[1] > alldata[user]["score"]:
                rank += 1

        ranklist.insert(
            rank,
            [
                user,
                alldata[user]["score"],
                alldata[user]["win"],
                alldata[user]["lose"],
                alldata[user]["winstrike"],
                alldata[user]["maxwinstrike"],
            ],
        )

    sendtext = "```"
    index = 1

    for i in ranklist:
        print(i)
        user=ctx.guild.get_member(int(i[0]))
        sendtext += f"{index} {user.display_name} {i[1]} {i[2]}승 {i[3]}패 {i[4]}연승(최대 {i[5]}연승) 승률 : {i[2] / (i[2] + i[3]) * 100}%\n"
        index += 1

    sendtext += "```"
    await ctx.send(sendtext)


@bot.command()
async def 통계(ctx):
    sql=f"SELECT COUNT(res2.row_num) from (SELECT ROW_NUMBER() OVER (ORDER BY id) row_num,id FROM (SELECT * from alltrackplaylist WHERE winner!=1) res1) res2;"

    cur.execute(sql)

    sendtext=f"총 게임수 : {cur.fetchone()[0]}회\n"


    sql=sql.replace("winner!=1","loserecord='retire'")

    cur.execute(sql)

    sendtext+=f"총 리타이어 수 : {cur.fetchone()[0]}회\n"

    sql="SELECT trackname,COUNT(trackname) from alltrackplaylist WHERE winner!=1 GROUP BY trackname ORDER BY COUNT(trackname) DESC LIMIT 1"

    cur.execute(sql)

    res=cur.fetchone()
    sendtext+=f"가장 많이 플레이한 트랙 : {res[0]} ({res[1]}회)\n"

    sql=f"SELECT COUNT(*) FROM (SELECT trackname,COUNT(trackname) AS playcount from alltrackplaylist WHERE winner!=1 GROUP BY trackname ORDER BY COUNT(trackname)) res WHERE res.playcount=1"

    cur.execute(sql)

    sendtext+=f"1회 플레이한 트랙들의 개수 : {cur.fetchone()[0]}개"


    await ctx.send(sendtext)

@bot.command()
async def 선호도(ctx, nick=None,startid=None):
    checkno = 1
    sql = '''SELECT trackname FROM speedtracklist GROUP BY trackname'''
    cur.execute(sql)
    res = cur.fetchall()

    trackscore = {}

    for d in res:
        trackscore[d[0]] = {"score": 0, "pick": 0, "ban": 0}

    if nick == None:
        sql = '''SELECT id,setno,trackno,trackname,picker FROM alltrackplaylist'''
    else:
        if nick=="id":
            sql = f'''SELECT setno,trackno,trackname FROM alltrackplaylist where id>={startid}'''
            nick=None
        else:
            sql = f'''SELECT setno,trackno,trackname FROM alltrackplaylist where picker="{nick}"'''

    col = cur.execute(sql)
    res = cur.fetchall()

    if col == 0:
        await ctx.send("존재하지 않는 유저 닉네임")
        return

    setno = 0

    pickbancount = {}

    for d in res:
        if checkno == 1:
            setno = 1
        else:
            pass

        if nick == None:
            if d[1] != setno:
                pickbancount.clear()
                setno = d[1]
        else:
            print(d[0], setno)

            if d[0] != setno:
                print(pickbancount)
                pickbancount.clear()
                setno = d[0]

        trackname = ""
        trackno = -1
        nickname = ""

        if nick == None:
            trackname = d[3]
            trackno = d[2]
            nickname = d[4]
        else:
            trackname = d[2]    
            trackno = d[1]
            nickname = nick
        print(nick)
        if nickname == 0:
            continue
        else:
            nickname=nick

        if not nickname in pickbancount:
            pickbancount[nickname] = {"pick": 0, "ban": 0}

        if trackno == 0:
            trackscore[trackname]["score"] += -5 + pickbancount[nickname]["ban"]
            trackscore[trackname]["ban"] += 1
            pickbancount[nickname]["ban"] += 1
        else:
            trackscore[trackname]["score"] += 5 - pickbancount[nickname]["pick"]
            trackscore[trackname]["pick"] += 1
            pickbancount[nickname]["pick"] += 1

        checkno += 1

    sendlist = []

    for name in trackscore.keys():

        rank = 0
        for data in sendlist:
            if data[1] > trackscore[name]["score"]:
                rank += 1
            elif data[1] == trackscore[name]["score"]:
                if data[2] > trackscore[name]["pick"]:
                    rank += 1

        sendlist.insert(
            rank,
            [
                name,
                trackscore[name]["score"],
                trackscore[name]["pick"],
                trackscore[name]["ban"],
            ],
        )

    sendtext = "```"

    indexno = 0

    for data in sendlist:
        indexno += 1

        sendtext += f"{'%-2s' % indexno} {data[0]} : {data[1]}점 픽 {data[2]}회 밴 {data[3]}회(밴픽 {data[2] + data[3]}회)\n"

        if indexno % 20 == 0:
            sendtext += "```"
            # await ctx.send(sendtext)
            sendtext = "```"

    sendtext += "```"

    # await ctx.send(sendtext)

    csvname = ""

    if nick == None:
        csvname = "../everyone_trackscore.csv"
    else:
        csvname = f"../{nickname}_trackscore.csv"

    with open(csvname, 'w', newline='') as csvfile:
        cw = csv.writer(csvfile)
        cw.writerow(["트랙 이름", "점수", "픽", "밴", "픽+밴"])

        for data in sendlist:
            data.append(data[2] + data[3])
            cw.writerow(data)

    await ctx.send(files=[nextcord.File(csvname)])


if testmode:
    bot.command_prefix = "map"
    bot.run(token[1])
else:
    bot.run(token[0])
