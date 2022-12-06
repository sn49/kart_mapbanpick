import os
import pymysql
import json





sqlinfo = open("secret/mysql.json", "r")
sqlcon = json.load(sqlinfo)


testmode=False
database = pymysql.connect(
user=sqlcon["user"],
host=sqlcon["host"],
db=sqlcon["db"],
charset=sqlcon["charset"],
password=sqlcon["password"],
autocommit=True,
)

filename="y22m11_02.maptxt"
cur = database.cursor()


senddata = ""




if filename.endswith(".maptxt"):
    y=int(filename[1:3])
    m=int(filename[4:6])
    no=int(filename[7:9])
    
    mapfile=open(f"maplist/speed/{filename}","r",encoding="UTF-8")
    maplist=mapfile.readlines()



    for track in maplist:
        name=track.replace('\n','')
        sql=f"insert ignore into speedtracklist values ({y},{m},{no},'{name}')"
        print(sql)
        cur.execute(sql)

