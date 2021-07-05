import discord
from discord.ext import commands, tasks
from discord.utils import get
import random
import asyncio
import os
import copy

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

    cturn=copy.deepcopy(turn)

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
    
gomsg=None

@bot.event
async def on_reaction_add(reaction,user):
    global gomsg
    global part
    global banpickRole



    
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




    
    

part=[]
maplist=[]
picklist=[]
banlist=[]
turn=0
order=1
isban=False
signch=None




#밴픽 참가
@bot.command()
async def 신청(ctx,mapfilename=None):
    global part
    global maplist
    global gomsg
    global banpickRole
    global signch


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

        banpickRole=await ctx.guild.create_role(name='밴픽',permissions=discord.Permissions(0))
        await ctx.author.add_roles(banpickRole)

        if len(part)==0:
            part.append(ctx.author.display_name)
            gomsg=await ctx.send(f"{ctx.author.display_name}의 {mapfilename} 밴픽에 참가할려면 🖐️이모지를 눌러주세요.")
            await gomsg.add_reaction("🖐️")
            signch=ctx.channel
        else:
            await ctx.send("이미 신청이 있습니다.")

banpickRole=None
newch=None
startIndex=None

async def banpickStart(ctx):
    global maplist
    global part
    global turn
    global banpickRole
    global newch
    global startIndex

    newch=await ctx.guild.create_text_channel('밴픽')
    selfbot=discord.utils.get(ctx.guild.members,id=bot.user.id)
    await selfbot.add_roles(banpickRole)
    await newch.set_permissions(banpickRole,read_messages=True)
    await newch.set_permissions(ctx.guild.default_role,read_messages=False)

    
    

    random.shuffle(maplist)


    for i in range(len(maplist)):
        maplist[i]=maplist[i].replace("\n","")
    await SendMaplist(newch)

    turn=random.randrange(0,2)
    startIndex=copy.deepcopy(turn)
    await newch.send(f"{part[turn]}의 픽부터 시작")

    await timer(newch)

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
    global isban
    global signch
    global startIndex

    if order==9:
        sendtext=""
        index=1
        for track in picklist:
            sendtext+=f"track{index} : {track}\n"
            index+=1
        await signch.send(f"```{part}\n{part[startIndex]}의 픽부터 시작(track1,2,3,5,7)\n{sendtext}\n밴 리스트 : {banlist}```")
        await EndBanPick()
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
    else:

        if index==None:
            await ctx.send("맵 번호를 입력해주세요.")
            return

        mapname=maplist[int(index)-1]
        
        maplist.remove(mapname)
        picklist.append(mapname)

        await SendMaplist(ctx)

        await ChangeTurn(ctx)

    
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
    

    part=[]
    maplist=[]
    picklist=[]
    banlist=[]
    turn=0
    order=1

    await gomsg.delete()
    await newch.delete()
    await banpickRole.delete()
    
    
    
    

@bot.command()
async def 취소(ctx):
    await EndBanPick()


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
        if index==None:
            await ctx.send("맵 번호를 입력해주세요.")
            return
        mapname=maplist[int(index)-1]
        
        maplist.remove(mapname)
        banlist.append(mapname)

        await SendMaplist(ctx)

        isban=False

        
        await ChangeTurn(ctx)

        await NoticeTurn(ctx,turn,isban)
    else:
        await ctx.send("밴을 할 차례입니다.")


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
        sendtext+="이중 12개 추첨\n```"
        await ctx.send(sendtext)
        return


    # 맵추첨
    mapfile=open(f"maplist/{mapfilename}.maptxt","r",encoding="UTF-8")
    maplist=mapfile.read()
    await ctx.send("```"+maplist+"```")
bot.run(token)