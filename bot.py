import discord
from discord.ext import commands, tasks
from discord.utils import get
import random
import asyncio
from threading import Thread
import os

bot=commands.Bot(command_prefix="맵")

tokenfile=open("token.txt","r")
token = tokenfile.read()

@bot.event
async def on_ready():
    print("ready")


async def timer(ctx):
    global maplist
    global turn
    second=40
    global maplist
    global banlist
    global picklist

    cturn=turn

    for i in range(16):
        await ctx.send(f"{second}초 남음")
        await asyncio.sleep(2.5)
        second-=2.5
        
        if cturn!=turn:
            return

    mapname=random.choice(maplist)

    if isban:
        banlist.append(mapname)
        maplist.remove(mapname)
    else:
        picklist.append(mapname)
        maplist.remove(mapname)

    await SendMaplist(ctx)

    await ChangeTurn(ctx)
    
    

    
    

part=[]
maplist=[]
picklist=[]
banlist=[]
turn=0
order=1
isban=False

#밴픽 참가
@bot.command()
async def 참가(ctx):
    global part

    if len(part)<2:
        if ctx.author.display_name in part:
            await ctx.send("이미 참가하였습니다.")
        else:
            part.append(ctx.author.display_name)
            await ctx.send(ctx.author.display_name+"참가 완료")
    else:
        await ctx.send("최대 2명까지만 가능합니다.")

#밴픽 시작, 맵 추첨
@bot.command()
async def 시작(ctx,mapfilename=None):
    global maplist
    global part
    global turn

    

    if len(part)!=2:
        await ctx.send("2명이어야 합니다.")
        return
        
    if mapfilename==None:
        datalist = os.listdir("maplist")
        senddata = ""
        for data in datalist:
            senddata += f"{data.replace('.txt','')}\n"
        await ctx.send(senddata)
        return


    # 맵추첨
    mapfile=open(f"maplist/{mapfilename}.txt","r",encoding="UTF-8")
    maplist=mapfile.readlines()
    random.shuffle(maplist)


    for i in range(len(maplist)):
        maplist[i]=maplist[i].replace("\n","")
    await SendMaplist(ctx)

    turn=random.randrange(0,2)
    await ctx.send(f"{part[turn]}의 픽부터 시작")

    await timer(ctx)


async def ChangeTurn(ctx):
    global order
    global turn
    global isban

    if order==9:
        sendtext="```"
        index=1
        for track in picklist:
            sendtext+=f"track{index} : {track}\n"
            index+=1
        sendtext+="```"
        await ctx.send(sendtext)
        EndBanPick()
    else:
        order+=1

        if order==2 or order==4:
            isban=True
        else:
            isban=False

    if turn==0:
        turn=1
    else:
        turn=0

    await NoticeTurn(ctx,turn,isban)

    await timer(ctx)
    


#맵 픽
@bot.command()
async def 픽(ctx,index=None):
    global picklist
    global maplist
    global order
    global turn
    global isban

    if ctx.author.display_name!=part[turn]: 
        await ctx.send("상대의 차례입니다.")
        return

    if isban:
        await ctx.send("밴을 할 차례입니다.")
        return

    if index==None:
        await ctx.send("맵 번호를 입력해주세요.")
        return

    mapname=maplist[int(index)-1]
    
    maplist.remove(mapname)
    picklist.append(mapname)

    await SendMaplist(ctx)

    await ChangeTurn(ctx)

    
def EndBanPick():
    global part
    global picklist
    global maplist
    global banlist
    global turn
    global order

    part=[]
    maplist=[]
    picklist=[]
    banlist=[]
    turn=0
    order=1
    

@bot.command()
async def 취소(ctx):
    EndBanPick()


#맵 밴
@bot.command()
async def 밴(ctx,index=None):
    global maplist
    global banlist
    global order
    global turn
    global isban

    if ctx.author.display_name!=part[turn]:
        await ctx.send("상대의 차례입니다.")
        return

    if isban:
        mapname=maplist[int(index)-1]
        
        maplist.remove(mapname)
        banlist.append(mapname)

        await SendMaplist(ctx)

        isban=False

        



    await ChangeTurn(ctx)

    await NoticeTurn(ctx,turn,isban)


async def SendMaplist(ctx):
    global maplist

    sendtext="```"

    index=1

    for track in maplist:
        sendtext+=f"{index}  {track}\n"
        index+=1
    
    sendtext+="```"

    await ctx.send(sendtext)

async def NoticeTurn(ctx,turn,isban):
    if isban:
        await ctx.send(f"{part[turn]}의 밴을 할 차례")
    else:
        await ctx.send(f"{part[turn]}의 픽을 할 차례")

bot.run(token)