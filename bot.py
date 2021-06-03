import discord
from discord.ext import commands, tasks
from discord.utils import get
import random

bot=commands.Bot(command_prefix="맵")

tokenfile=open("token.txt","r")
token = tokenfile.read()

@bot.event
async def on_ready():
    print("ready")


part=[]
maplist=[]
picklist=[]
banlist=[]
turn=0
order=1

#밴픽 참가
@bot.command()
async def 참가(ctx):
    global part

    if len(part)<2:
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
        return
    # 맵추첨
    mapfile=open(f"maplist/{mapfilename}.txt","r",encoding="UTF-8")
    maplist=mapfile.readlines()


    for i in range(len(maplist)):
        maplist[i]=maplist[i].replace("\n","")
    await SendMaplist(ctx)

    turn=random.randrange(0,2)
    await ctx.send(f"{part[turn]}의 픽부터 시작")
    

#맵 픽
@bot.command()
async def 픽(ctx,mapname=None):
    global picklist
    global maplist
    global order
    global turn

    if ctx.author.display_name!=part[turn]:
        await ctx.send("상대의 차례입니다.")
        return

    if order==2 or order==4:
        await ctx.send("밴을 할 차례입니다.")
        return

    if mapname==None:
        await ctx.send("맵 이름을 입력해주세요.")
        return

    result=CheckMap(mapname)

    if result==-1:
        await ctx.send("맵 이름을 잘못 입력함")
        return
    
    maplist.remove(mapname)
    picklist.append(mapname)    

    await SendMaplist(ctx)

    if order==9:
        await ctx.send(picklist)
        EndBanPick()
    else:
        order+=1

    if turn==0:
        turn=1
    else:
        turn=0

def EndBanPick():
    global part
    global picklist
    global maplist
    global banlist

    part.clear()
    picklist.clear()
    maplist.clear()
    banlist.clear()
    

@bot.command()
async def 취소(ctx):
    EndBanPick()


#맵 밴
@bot.command()
async def 밴(ctx,mapname=None):
    global maplist
    global banlist
    global order
    global turn

    if ctx.author.display_name!=part[turn]:
        await ctx.send("상대의 차례입니다.")
        return

    if order==2 or order==4:
        result=CheckMap(mapname)

        if result==-1:
            await ctx.send("맵 이름을 잘못 입력함")
            return
        
        maplist.remove(mapname)
        banlist.append(mapname)

        await SendMaplist(ctx)
        order+=1

    if turn==0:
        turn=1
    else:
        turn=0
    

def CheckMap(mapname):
    global maplist

    if mapname in maplist:
        return 1
    else:
        return -1

async def SendMaplist(ctx):
    global maplist

    await ctx.send(maplist)


bot.run(token)