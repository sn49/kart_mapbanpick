import discord
from discord.ext import commands, tasks
from discord.ext.commands.core import check
from discord.utils import get
import random
import asyncio
import os
import copy
import pymysql
import json

sqlinfo = open("mysql.json", "r")
sqlcon = json.load(sqlinfo)

database = pymysql.connect(
    user=sqlcon["user"],
    host=sqlcon["host"],
    db=sqlcon["db"],
    charset=sqlcon["charset"],
    password=sqlcon["password"],
    autocommit=True,
)
cur = database.cursor()


bot=commands.Bot(command_prefix="맵")

testmode=False

tokenfile=open("token.txt","r")
token = tokenfile.readlines()

@bot.event  
async def on_ready():
    print("ready")

timemsg=None

async def timer(ctx):
    global maplist
    global turn
    global maplist
    global banlist
    global picklist
    global timemsg
    global order

    repeat_Time=5
    second=0

    if testmode:
        second=35
    else:   
        second=40

    


    corder=copy.deepcopy(order)

    

    

    while second>0:
        if bporder[order][0]=="r":
            break

        if timemsg==None:
            timemsg=await ctx.send(f"{second}초 남음")
        else:
            print("tetssetttt")
            await timemsg.edit(content=f"{second}초 남음")
        await asyncio.sleep(repeat_Time)
        second-=repeat_Time
        
        if corder!=order:
            return

    

    randombp()

    await SendMaplist(ctx)

    await ChangeTurn(ctx)
    
gomsg=None
ordermsg=None
userindex=None

@bot.event
async def on_reaction_add(reaction,user):
    global gomsg
    global part
    global banpickRole
    global ordermsg
    global turn
    global startIndex
    global userindex

    if reaction.message == gomsg:
        if not user.bot:
            if not user.display_name in part:
                if reaction.emoji =="🖐️":
                    if len(part)<2:
                        part.append(user.display_name)
                        await user.add_roles(banpickRole)
                        await reaction.message.edit(content=f"{part}의 밴픽을 보고싶다면 😀를 눌러주세요.")
                        await reaction.message.add_reaction("😀")
                        await banpickStart(reaction.message.channel)
                    else:
                        await reaction.message.channel.send("이미 진행중인 밴픽이 있습니다.")
                        return

                    
                elif reaction.emoji =="😀": 
                    await newch.set_permissions(user,read_messages=True,send_messages=False)
                else:
                    await reaction.remove(user)
            else:
                await reaction.remove(user)
        return
    
    if reaction.message == ordermsg:
        if not user.bot:
            if user.display_name in part:
                emojiList=["🇦","🇧","🇷"]
                emojiIndex=emojiList.index(reaction.emoji)
                print(emojiIndex)

                if emojiIndex==0 or emojiIndex==1:
                    turn=emojiIndex
                else:
                    turn=random.randrange(0,2)
                await ordermsg.delete()
                for i in range(len(maplist)):
                    maplist[i]=maplist[i].replace("\n","")
                userindex={}
                userindex["a"]=part[turn]

                if turn==0:
                    turn=1
                else:
                    turn=0

                userindex["b"]=part[turn]
                userindex["r"]="random"

                await SendMaplist(newch)
                await newch.send(f"{userindex[bporder[order][0]]}의 {bporder[order][1]}부터 시작")
                await timer(newch)
                
    

part=[]
maplist=[]
picklist=[]
banlist=[]
turn=0
order=0
signch=None
bporder=None

def randombp():
    global maplist
    global banlist
    global picklist

    mapname=random.choice(maplist)

    if bporder[order][1]=="ban":
        banlist.append([mapname,"random"])
        maplist.remove(mapname)
    else:
        picklist.append([mapname,"random"])
        maplist.remove(mapname)


def checkbpofile(filename):
    try:
        tempbpo=[]
        bpofile=open(f"{filename}.bpo","r",encoding="utf-8")
        tempo=bpofile.readlines()

        count={}

        for o in tempo:
            info=o.split(',')
            if info[0]=='a' or info[0]=='b' or info[0]=='r':
                if info[1]=='pick' or info[1]=='ban':
                    if info[1] in count.keys():
                        count[info[1]]+=1
                    else:
                        count[info[1]]=1
                    tempbpo.append([info[0],info[1]])
                else:
                    return False
            else:
                return False

        return tempbpo
    except:
        return False

    

#밴픽 참가
@bot.command()
async def 신청(ctx,mapfilename=None,bpofilename=None):
    global part
    global maplist
    global gomsg
    global banpickRole
    global signch
    global bporder

    if mapfilename==None:
        datalist = os.listdir("maplist")
        senddata = ""
        for data in datalist:
            if ".maptxt" in data:
                senddata += f"{data.replace('.maptxt','')}\n"
        await ctx.send(senddata)
        return
    else:
        
        if mapfilename=="all":
            maplist=GetAllTrack()
            maplist=random.sample(maplist,12)
        else:
            # 맵추첨
            mapfile=open(f"maplist/{mapfilename}.maptxt","r",encoding="UTF-8")
            maplist=mapfile.readlines()


        bporder=checkbpofile(bpofilename)

        if bporder==False:
            await ctx.send("올바른 밴픽 순서 파일이 아님")
            return


        banpickRole=await ctx.guild.create_role(name='밴픽',permissions=discord.Permissions(0))
        await ctx.author.add_roles(banpickRole)

        if len(part)==0:
            part.append(ctx.author.display_name)
            gomsg=await ctx.send(f"{ctx.author.display_name}의 {mapfilename} 밴픽에 참가할려면 🖐️이모지를 눌러주세요.(순서 : {bpofilename})")
            await gomsg.add_reaction("🖐️")
            signch=ctx.channel
        else:
            await ctx.send("이미 신청이 있습니다.")

banpickRole=None
newch=None
startIndex=None
sendmsg=None


async def banpickStart(ctx):
    global maplist
    global part
    global turn
    global banpickRole
    global newch
    global startIndex
    global ordermsg
    

    newch=await ctx.guild.create_text_channel('밴픽')
    await newch.edit(category=gomsg.channel.category)
    selfbot=discord.utils.get(ctx.guild.members,id=bot.user.id)
    await selfbot.add_roles(banpickRole)
    await newch.set_permissions(banpickRole,read_messages=True)
    await newch.set_permissions(ctx.guild.default_role,read_messages=False)
    ordermsg=await newch.send(f"{part[0]}부터 시작 - 🇦,{part[1]}부터 시작 - 🇧,랜덤 시작 - 🇷")
    await ordermsg.add_reaction("🇦")
    await ordermsg.add_reaction("🇧")
    await ordermsg.add_reaction("🇷")
    
    

    random.shuffle(maplist)

@bot.command()
async def test(ctx):
    await ctx.send(ctx.author.mention)
    
@bot.command()
async def 기록(ctx,mapname=None,nickname=None,nickname2=None):
    try:
        if mapname==None:
            sql="""SELECT TABLE1.trackname,TABLE1.winner,TABLE1.winrecord FROM alltrackplaylist AS TABLE1,(SELECT trackname,winner,MIN(winrecord) AS min_sort FROM alltrackplaylist GROUP BY trackname) AS TABLE2 WHERE TABLE1.winrecord=TABLE2.min_sort AND TABLE1.trackname = TABLE2.trackname AND NOT table1.winner='X'"""
            cur.execute(sql)
            result=cur.fetchall()
            sendtext="```"
            for i in result:
                sendtext+=f"{'%-20s' % i[0]}\t{'%-9s' % i[1]}\t{'%-9s' % i[2]}\n"
            sendtext+="```"
            await ctx.send(sendtext)
            return
        
        mapname=mapname.replace(' ','_')

        
        sendtext=""


        if nickname==None:
            sql=f"SELECT SUM(pick),SUM(ban),MIN(bestrecord) FROM track_{mapname}"
            cur.execute(sql)
            i=cur.fetchone()
            sendtext=f"{mapname.replace('_',' ')}\n픽 {i[0]}회\n밴 {i[1]}회\n최고 기록 {i[2]}"
        else:
            

            if nickname2==None:
                if nickname=="all":
                    sql=f"select nickname,bestrecord from track_{mapname}"
                    cur.execute(sql)
                    i=cur.fetchall()
                    sendtext="```"
                    for info in i:
                        sendtext+=f"{info[0]} - {info[1]}\n"
                    sendtext+="```"
                    await ctx.send(sendtext)
                    return
                else:
                    sql=f"SELECT * FROM track_{mapname} WHERE nickname='{nickname}'"
                    cur.execute(sql)
                    i=cur.fetchone()
                    sendtext=f"{i[0]}\n픽 {i[1]}회\n - 승리 {i[2]}회\n - 패배 {i[3]}회\n - 못함 {i[1]-i[2]-i[3]}회\n밴 {i[4]}회\n{i[5]}승 {i[6]}패\n최고 기록 : {i[7]}\n{i[8]}년 {i[9]}월 시즌{i[10]} {i[11]}라운드 vs {i[14]} {i[12]}세트 {i[13]}트랙"
            else:
                sendtext="```"
                sql=f"SELECT trackno,picker,winner FROM alltrackplaylist WHERE ((player1='{nickname}' AND player2='{nickname2}') OR (player1='{nickname2}' AND player2='{nickname}')) AND trackname='{mapname}'"
                print(sql)
                cur.execute(sql)
                i=cur.fetchall()
                
                if len(i)==0:
                    await ctx.send("기록이 없거나 잘못된 트랙 이름입니다.")
                    return

                pick=[0,0]
                ban=[0,0]
                win=[0,0]
                cant=[0,0]

                
                for info in i:
                    if info[0]==0:
                        if nickname==info[1]:
                            ban[0]+=1
                        else:
                            ban[1]+=1
                    else:
                        iscant=False
                        if info[2]=="X" or info[2]=="x" :
                            iscant=True
                        if nickname==info[1]:
                            pick[0]+=1
                            if iscant:
                                cant[0]+=1
                        else:
                            pick[1]+=1
                            if iscant:
                                cant[1]+=1

                    if not info[2]=="X" or info[2]=="x" :
                        if nickname==info[2]:
                            win[0]+=1
                        else:
                            win[1]+=1


                
                sendtext=f"```{mapname}\n{nickname} vs {nickname2}\n"
                sendtext+=f"픽 {pick[0]}({cant[0]}회 못함) : {pick[1]}({cant[1]}회 못함)\n"
                sendtext+=f"밴 {ban[0]} : {ban[1]}\n"
                sendtext+=f"승리 {win[0]} : {win[1]}```"

                await ctx.send(sendtext)
                return

        await ctx.send(sendtext)
    except pymysql.ProgrammingError:
        await ctx.send("기록이 없는 트랙입니다.")



@bot.command()
async def 전적(ctx,nickname=None,nickname2=None):
    try:
        if nickname==None:
            await ctx.send("nickname을 입력해주세요.")
            return

        sendtext=""
        

        if nickname2==None:
            sql=f"SELECT SUM(gamewin),SUM(gamelose), SUM(setwin),SUM(setlose),SUM(trackwin),SUM(tracklose) FROM user_{nickname}"
            print(sql)
            cur.execute(sql)
            i=cur.fetchone()
            sendtext=f"{nickname}\n{i[0]}승 {i[1]}패\n세트 {i[2]}승 {i[3]}패\n트랙 {i[4]}승 {i[5]}패"
        else:
            sql=f"select * from user_{nickname} where nickname='{nickname2}'"
            cur.execute(sql)
            i=cur.fetchone()
            if i==None:
                sendtext="상대를 찾지 못했습니다."
            else:
                sendtext=f"{nickname} vs {i[0]}\n{i[1]} : {i[2]}\n세트 {i[3]} : {i[4]}\n트랙 {i[5]} : {i[6]}"
        await ctx.send(sendtext)
    except pymysql.ProgrammingError:
        await ctx.send("존재하지 않는 유저입니다.")





@bot.command()
async def 랜덤맵(ctx):
    maplist=GetAllTrack()
    maplist=random.sample(maplist,7)

    sendtext="```"

    index=1

    for track in maplist:
        sendtext+=f"track{index}  {track}\n"
        index+=1
    
    sendtext+="```"

    await ctx.send(sendtext)




async def ChangeTurn(ctx):
    global order
    global turn
    global signch
    global startIndex

    global bporder

    order+=1

    if order==len(bporder):
        sendtext=""
        index=1
        for track in picklist:
            sendtext+=f"track{index} : {track[0]} - {track[1]}\n"
            index+=1
        sendtext+="\n\n밴 리스트\n"
        for ban in banlist:
            sendtext+=f"{ban[0]} - {ban[1]}\n"
        await signch.send(f"```{sendtext}```")
        await EndBanPick()
        return

    await NoticeTurn(ctx)

    await timer(ctx)
    



    
async def EndBanPick():
    global part
    global picklist
    global maplist
    global banlist
    global turn
    global order
    global banpickRole
    global newch
    global gomsg
    
    global bporder
    global sendmsg
    global timemsg

    part=[]
    maplist=[]
    picklist=[]
    banlist=[]
    turn=0
    order=0
    sendmsg=None
    timemsg=None

    await gomsg.delete()
    await newch.delete()
    await banpickRole.delete()
    
    
    
    

@bot.command()
async def 취소(ctx):
    await EndBanPick()


#맵 밴
@bot.command()
async def 밴픽(ctx,index=None):
    global maplist
    global banlist
    global order
    global turn
    global picklist
    global userindex

    if ctx.author.display_name!=userindex[bporder[order][0]]: 
        await ctx.send("상대의 차례입니다.")
        return

    if index==None:
        await ctx.send("맵 번호를 입력해주세요.")
        return

    mapname=maplist[int(index)-1]
    maplist.remove(mapname)

    if bporder[order][1]=="ban":
        banlist.append([mapname,userindex[bporder[order][0]]])
    else:
        picklist.append([mapname,userindex[bporder[order][0]]])

    await SendMaplist(ctx)

    await ChangeTurn(ctx)

    await NoticeTurn(ctx)

    await ctx.message.delete()

turnmsg=None

async def SendMaplist(ctx):
    global maplist
    global bporder
    global order
    global picklist
    global banlist
    global sendmsg

    sendtext="```"

    index=1

    for track in maplist:
        sendtext+=f"{index}  {track}\n"
        index+=1

    sendtext+=f"\n밴 리스트\n"


    for ban in banlist:
        sendtext+=f"{ban[0]}\n"

    sendtext+=f"\n픽 리스트\n"

    for pick in picklist:
        sendtext+=f"{pick[0]}\n"
    sendtext+="```"

    if sendmsg==None:
        sendmsg=await ctx.send(sendtext)
    else:
        await sendmsg.edit(content=sendtext)



async def NoticeTurn(ctx):
    global turnmsg

    if turnmsg==None:
        turnmsg=await ctx.send(f"{userindex[bporder[order][0]]}의 {bporder[order][1]}을 할 차례")
    else:
        await turnmsg.edit(content=f"{userindex[bporder[order][0]]}의 {bporder[order][1]}을 할 차례")


def GetAllTrack():
    allmaplist=[]
    datalist = os.listdir("maplist")
    senddata = ""
    for data in datalist:
        if data.endswith(".maptxt"):
            mapfile=open("maplist/"+data,"r",encoding="UTF-8")
            for track in mapfile.readlines():
                temp=track.replace("\n","")
                if not temp in allmaplist:
                    allmaplist.append(temp)
    return allmaplist

@bot.command()
async def 리스트(ctx,mapfilename=None):
    if mapfilename==None:
        datalist = os.listdir("maplist")
        senddata = ""
        for data in datalist:
            if data.endswith(".maptxt"):
                senddata += f"{data.replace('.maptxt','')}\n"
        await ctx.send(senddata)
        return
    elif mapfilename=="all":
        allmaplist=GetAllTrack()
        sendtext="```"
        for i in range(len(allmaplist)):
            sendtext+=f"{i+1} : {allmaplist[i]}\n"

            if i%20==19:
                sendtext+="```"
                await ctx.send(sendtext)
                sendtext="```"
        sendtext+="이중 12개 추첨\n```"
        await ctx.send(sendtext)
        return


    # 맵추첨
    mapfile=open(f"maplist/{mapfilename}.maptxt","r",encoding="UTF-8")
    maplist=mapfile.read()
    await ctx.send("```"+maplist+"```")

@bot.command()
async def 평가(ctx,mapfilename=None):
    mapfile=open(f"votelist/{mapfilename}","r",encoding="UTF-8")
    maplist=mapfile.readlines()

    sendtext="```"

    for i in maplist:
        sendtext+=f"{i}"
    sendtext+="```\n추후 기능 추가 예정"

    await ctx.send(sendtext)


inputT=input("test or main : ")
if inputT=="test":
    testmode=True
    bot.command_prefix="map"
    bot.run(token[1])
elif inputT=="main":
    testmode=False
    bot.run(token[0])