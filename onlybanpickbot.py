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

sqlinfo = open("mysql.json", "r")
sqlcon = json.load(sqlinfo)

inputT=input("test or main : ")





if inputT=="test":
    database = pymysql.connect(
    user=sqlcon["user"],
    host=sqlcon["host"],
    db=sqlcon["db"],
    charset=sqlcon["charset"],
    password=sqlcon["password"],
    autocommit=True,
)
elif inputT=="main":
    database = pymysql.connect(
    user=sqlcon["user"],
    host=sqlcon["host"],
    db=sqlcon["testdb"],
    charset=sqlcon["charset"],
    password=sqlcon["password"],
    autocommit=True,
    )

cur = database.cursor()


bot=commands.Bot(command_prefix="t!")

tokenfile=open("obpbtoken.txt","r")
token = tokenfile.readlines()

@bot.event  
async def on_ready():
    print("ready")


if inputT=="test":
    testmode=True
    bot.command_prefix="ㅌ!"
    bot.run(token[1])
elif inputT=="main":
    testmode=False
    bot.run(token[0])


def GetAllTrack():
    allmaplist=[]
    datalist = os.listdir("maplist")
    senddata = ""
    for data in datalist:
        if data.endswith(".maptxt") and not "item" in data:
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
        sendtext+="이중 14개 추첨\n```"
        await ctx.send(sendtext)
        return


    # 맵추첨
    mapfile=open(f"maplist/{mapfilename}.maptxt","r",encoding="UTF-8")
    maplist=mapfile.read()
    await ctx.send("```"+maplist+"```")

trackbanpick={"none":{},"ban":{},"pick":{}}



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
            maplist=random.sample(maplist,14)
        else:
            # 맵추첨
            mapfile=open(f"maplist/{mapfilename}.maptxt","r",encoding="UTF-8")
            maplist=mapfile.readlines()


        bporder=checkbpofile(bpofilename)

        if bporder==False:
            await ctx.send("올바른 밴픽 순서 파일이 아님")
            return


        banpickRole=await ctx.guild.create_role(name='밴픽',permissions=nextcord.Permissions(0))
        await ctx.author.add_roles(banpickRole)

        if len(part)==0:
            part.append(ctx.author.display_name)
            gomsg=await ctx.send(f"{ctx.author.display_name}의 {mapfilename} 밴픽에 참가할려면 🖐️이모지를 눌러주세요.(순서 : {bpofilename})")
            await gomsg.add_reaction("🖐️")
            signch=ctx.channel
            await ctx.send(signch.jump_url)
        else:
            await ctx.send("이미 신청이 있습니다.")

def ManageTrackList(tracklist,index,mode):
    if mode=="ban":

    if mode=="pick"


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

                await ManageTrackList(newch)
                await newch.send(f"{userindex[bporder[order][0]]}의 {bporder[order][1]}부터 시작")
                await timer(newch)