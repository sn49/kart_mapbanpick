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

inputT = input("test or main : ")

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

bot = commands.Bot(command_prefix="맵")

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

    if testmode:
        second = 90
    else:
        second = 40

    corder = copy.deepcopy(order)

    while second > 0:
        if corder != order:
            return

        if bporder[order][0] == "r":
            break

        if timemsg == None:
            timemsg = await ctx.send(f"{second}초 남음")
        else:
            print("tetssetttt")
            await timemsg.edit(content=f"{second}초 남음")
        await asyncio.sleep(repeat_Time)
        second -= repeat_Time

    bpmanage("random", bporder[order][1])

    await SendMaplist(ctx)

    await ChangeTurn(ctx)


gomsg = None
ordermsg = None
userindex = None
banpickctx = None


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
                            print("disconnect try")
                            await banpickctx.voice_client.disconnect()
                        except:
                            pass

                        channel = banpickctx.author.voice.channel
                        await channel.connect()

                        banpickctx.voice_client.stop()
                        source = nextcord.PCMVolumeTransformer(
                            nextcord.FFmpegPCMAudio(executable='music/ffmpeg.exe', source='music/banpick.mp3'))
                        banpickctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

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


def bpmanage(username, mode, trackname=None):
    global maplist
    global banpicklist
    global isdbrecord

    mapname = trackname

    trackno = 0
    if username == "random":
        mapname = random.choice(maplist)

    bancount = len([x for x in banpicklist if x[2] == "ban"])
    print(bancount)

    if mode == "pick":
        trackno = len(banpicklist) - bancount + 1

    banpicklist.append([mapname, username, mode])

    maplist.remove(mapname)

    if isdbrecord:
        banstring = ["", ""]

        if trackno == 0:
            banstring = [",winner,winrecord,loserecord", ",'X','X','X'"]

        sql = f"insert into alltrackplaylist (round,setno,year,month,player1,player2,trackno,trackname,picker{banstring[0]}) values ({dbround},{dbset},{int(str(datetime.now().year)[-2:])},{datetime.now().month},'{userindex['a'][0]}','{userindex['b'][0]}',{trackno},'{banpicklist[-1][0]}','{username}'{banstring[1]})"
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
async def 가입(ctx, nickname=None):
    banword = open("secret/banword.txt", "r", encoding="UTF-8").readlines()
    for i in range(len(banword)):
        banword[i] = banword[i].replace("\n", "")

        if banword[i] in nickname:
            await ctx.send("사용할수 없는 닉네임")
            return

    if len(nickname) > 15:
        await ctx.send("닉네임 글자 수 15자 이하")
        return

    sql = f"insert ignore into user (discordid,nickname) values ({ctx.author.id},'{nickname}')"
    print(sql)
    result = cur.execute(sql)
    print(result)

    if result > 0:
        await ctx.send("가입 완료")
    else:
        await ctx.send("이미 가입했거나 중복된 닉네임입니다.")


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

    if str(dbrecord).lower() == "true":
        if wround == None or wset == None:
            await ctx.send("라운드와 세트를 입력해주세요")
            return

        dbset = int(wset)
        dbround = int(wround)

        sql = f"select nickname from user where discordid={ctx.author.id}"
        cur.execute(sql)
        res = cur.fetchone()

        if res == None:
            await ctx.send("비회원입니다. true 미입력시 비회원으로 가능합니다.")
            return

        part.append(res[0])
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

        if mapfilename.startswith("all"):
            mapcount = int(mapfilename.split("-")[1])
            maplist = GetAllTrack()
            maplist = random.sample(maplist, mapcount)
        else:
            # 맵추첨
            mapfile = open(f"maplist/{mapfilename}.maptxt", "r", encoding="UTF-8")
            maplist = mapfile.readlines()

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
            sql = """SELECT TABLE1.trackname,TABLE1.winner,TABLE1.winrecord FROM alltrackplaylist AS TABLE1,(SELECT trackname,winner,MIN(winrecord) AS min_sort FROM alltrackplaylist GROUP BY trackname) AS TABLE2 WHERE TABLE1.winrecord=TABLE2.min_sort AND TABLE1.trackname = TABLE2.trackname AND NOT table1.winner='X'"""
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

            if nickname2 == None:
                if nickname == "all":
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
                    sql = f"SELECT * FROM track_{mapname} WHERE nickname='{nickname}'"
                    cur.execute(sql)
                    i = cur.fetchone()
                    sendtext = f"{i[0]}\n픽 {i[1]}회\n - 승리 {i[2]}회\n - 패배 {i[3]}회\n - 못함 {i[1] - i[2] - i[3]}회\n밴{i[4]}회\n랜덤밴 {i[5]}회\n랜덤픽{i[6]}회\n{i[7]}승 {i[8]}패\n최고 기록 : {i[9]}\n{i[10]}년 {11}월 {i[12]}라운드 vs {i[15]} {i[13]}세트 {i[14]}트랙"
            else:
                sendtext = "```"
                sql = f"SELECT trackno,picker,winner FROM alltrackplaylist WHERE ((player1='{nickname}' AND player2='{nickname2}') OR (player1='{nickname2}' AND player2='{nickname}')) AND trackname='{mapname}'"
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
        print(e)
        await ctx.send("기록이 없는 트랙입니다.")


@bot.command()
async def 전적(ctx, nick1=None, nick2=None):
    if nick1 == None:
        await ctx.send("nickname을 입력해주세요.")
        return

    sendtext = ""

    player1 = {"track": 0, "set": 0, "game": 0}
    player2 = {"track": 0, "set": 0, "game": 0}
    tempscore = {"track": {"player1": 0, "player2": 0}, "set": {"player1": 0, "player2": 0}}

    tempset = -1

    if nick2 == None:
        trackwinsql = f"""select COUNT(winner) from alltrackplaylist WHERE winner='{nick1}' AND (player1='{nick1}' OR player2='{nick1}')"""
        cur.execute(trackwinsql)

        res = cur.fetchone()

        player1["track"] = res[0]

        tracklosesql = f"""select COUNT(winner) from alltrackplaylist WHERE winner!='{nick1}' AND winner!='X' AND (player1='{nick1}' OR player2='{nick1}')"""
        cur.execute(tracklosesql)

        res = cur.fetchone()

        player2["track"] = res[0]

        setsql = f"""SELECT winner,COUNT(winner) FROM (SELECT YEAR, MONTH, ROUND, setno,winner,COUNT(winner) AS trackscore from alltrackplaylist WHERE (player1='{nick1}' or player2='{nick1}') and winner != 'X' GROUP BY YEAR, MONTH, ROUND, setno,winner,player1,player2) res WHERE trackscore>=4 GROUP BY winner"""

        cur.execute(setsql)

        res = cur.fetchall()

        for i in res:
            if i[0] == nick1:
                player1["set"] = i[1]
            else:
                player2["set"] += i[1]

        gamewinsql = f"""SELECT COUNT(*) FROM(SELECT YEAR, MONTH, ROUND, player1, player2, COUNT(*) as setscore FROM(SELECT YEAR, MONTH, ROUND, setno, player1, player2, COUNT(winner) AS trackscore FROM alltrackplaylist WHERE('{nick1}' IN (player1, player2))AND winner='{nick1}' GROUP BY YEAR, MONTH, ROUND, setno, player1, player2)res WHERE trackscore>=4 GROUP BY YEAR, MONTH, ROUND, LEAST(player1, player2), GREATEST(player1, player2))res WHERE setscore>=2"""

        cur.execute(gamewinsql)

        res = cur.fetchone()

        player1["game"] = res[0]

        gamelosesql = gamewinsql.replace(f"winner='{nick1}'", f"winner not in ('{nick1}','X')")

        print(gamelosesql)

        cur.execute(gamelosesql)

        res = cur.fetchone()

        player2["game"] = res[0]

        sendtext = f"{nick1}\n{player1['game']}승 {player2['game']}패\n세트 {player1['set']}승 {player2['set']}패\n트랙 {player1['track']}승 {player2['track']}패"
    else:
        tracksql = f"""select winner,COUNT(winner) from alltrackplaylist WHERE ('{nick1}' IN (player1, player2) AND '{nick2}' IN (player1, player2)) AND winner!='X' GROUP BY winner"""

        cur.execute(tracksql)

        res = cur.fetchall()

        for i in res:
            if i[0] == nick1:
                player1["track"] = i[1]
            else:
                player2["track"] = i[1]

        setsql = f"""SELECT winner,COUNT(winner) FROM (SELECT YEAR, MONTH, ROUND, setno,winner,COUNT(winner) AS trackscore from alltrackplaylist WHERE ('{nick1}' IN (player1, player2) AND '{nick2}' IN (player1, player2)) and winner != 'X' GROUP BY YEAR, MONTH, ROUND, setno,winner) res WHERE trackscore>=4 GROUP BY winner"""

        cur.execute(setsql)

        res = cur.fetchall()

        for i in res:
            if i[0] == nick1:
                player1["set"] = i[1]
            else:
                player2["set"] = i[1]

        gamesql = f"""SELECT COUNT(*) FROM (SELECT * FROM (SELECT YEAR, MONTH, ROUND, setno,winner,COUNT(winner) AS trackscore from alltrackplaylist WHERE ('{nick1}' IN (player1, player2) AND '{nick2}' IN (player1, player2)) and winner != 'X' GROUP BY YEAR, MONTH, ROUND, setno,winner) res WHERE trackscore>=4 AND winner="...winner..." GROUP BY year,month,ROUND HAVING COUNT(*)>=2) res"""

        cur.execute(gamesql.replace("...winner...", nick1))

        res = cur.fetchone()

        player1["game"] = res[0]

        cur.execute(gamesql.replace("...winner...", nick2))

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
async def 랜덤맵(ctx):
    maplist = GetAllTrack()
    maplist = random.sample(maplist, 7)

    sendtext = "```"

    index = 1

    for track in maplist:
        sendtext += f"track{index}  {track}\n"
        index += 1

    sendtext += "```"

    await ctx.send(sendtext)


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

        banpickctx.voice_client.stop()
        source = nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(executable='music/ffmpeg.exe', source='music/gamestart.mp3'))
        banpickctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

        await EndBanPick()
        return

    await NoticeTurn(ctx)

    await timer(ctx)


async def EndBanPick():
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

    await gomsg.delete()
    await newch.delete()
    await banpickRole.delete()


@bot.command()
async def 취소(ctx):
    banpickctx.voice_client.stop()
    await EndBanPick()


# 맵 밴
@bot.command()
async def 밴픽(ctx, index=None):
    global maplist
    global banpicklist
    global order
    global turn
    global userindex
    global isdbrecord

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

    bpmanage(userindex[bporder[order][0]][0], bporder[order][1], mapname)

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
    allmaplist = []
    datalist = os.listdir("maplist/speed")
    senddata = ""
    for data in datalist:
        if data.endswith(".maptxt") and not "item" in data:
            mapfile = open("maplist/speed/" + data, "r", encoding="UTF-8")
            for track in mapfile.readlines():
                temp = track.replace("\n", "")
                if not temp in allmaplist:
                    allmaplist.append(temp)
    return allmaplist


@bot.command()
async def 리스트(ctx, mapfilename=None):
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
        sendtext = "```"
        for i in range(len(allmaplist)):
            sendtext += f"{i + 1} : {allmaplist[i]}\n"

            if i % 20 == 19:
                sendtext += "```"
                await ctx.send(sendtext)
                sendtext = "```"
        sendtext += "이중 14개 추첨\n```"
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
async def 랭킹(ctx, nickname=None):
    ranklist = []

    alldata = ScoreCalcurate.GetRanking(cur)

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
        sendtext += f"{index} {i[0]} {i[1]} {i[2]}승 {i[3]}패 {i[4]}연승(최대 {i[5]}연승) 승률 : {i[2] / (i[2] + i[3]) * 100}%\n"
        index += 1

    sendtext += "```"
    await ctx.send(sendtext)


@bot.command()
async def 선호도(ctx, nick=None):
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

        if nickname == "random":
            continue

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
