import random


maplist=open("maplist/templist/y22m11_01.maptxt","r",encoding="UTF-8").readlines()

for i in range(len(maplist)) :
    maplist[i] = maplist[i].replace("\n","")


result=random.sample(maplist,19)
notresult = [x for x in maplist if x not in result]

writefile=open("maplist/templist/y22m11_02.maptxt","w",encoding="UTF-8")
for i in result:
    writefile.write(i+"\n")
writefile.close()

random.shuffle(notresult)

writefile=open("maplist/templist/y22m11_01.maptxt","w",encoding="UTF-8")
for i in notresult:
    writefile.write(i+"\n")
writefile.close()
