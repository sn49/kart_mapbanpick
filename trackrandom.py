import random


maplist=open("maplist/speed/y22m10_01.maptxt","r",encoding="UTF-8").readlines()

for i in range(len(maplist)) :
    maplist[i] = maplist[i].replace("\n","")


result=random.sample(maplist,14)
notresult = [x for x in maplist if x not in result]

writefile=open("maplist/y22m10_02.maptxt","w",encoding="UTF-8")
for i in result:
    writefile.write(i+"\n")
writefile.close()

random.shuffle(notresult)

writefile=open("maplist/y22m10_01.maptxt","w",encoding="UTF-8")
for i in notresult:
    writefile.write(i+"\n")
writefile.close()
