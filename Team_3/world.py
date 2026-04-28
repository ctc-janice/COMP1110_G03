import math

with open("Team_3/testworld.txt", "r") as file:
    pieces = file.readlines()

segments=[]
stations=[]
for i in pieces:
    if i.startswith("seg_start"):
        continue
    else:
        tripMetadata = i.strip().split(",")
        if tripMetadata[0] not in stations:
            stations.append(tripMetadata[0])
        segments.append({"from":f"{tripMetadata[0]}", "to":f"{tripMetadata[1]}", "cost":int(tripMetadata[2]), "duration":int(tripMetadata[3])})
        
adjacencies={}
for s in segments:
    if (s["from"] not in adjacencies):
        adjacencies[s["from"]] = []
    adjacencies[s["from"]].append(s)

results=[]
visited=set()
def dfsTravel(currentpoint, endpoint, max_path_length = math.inf, journey=[]):
    if (currentpoint == endpoint):
        results.append(journey)
        journey=[]
        return None
    if (currentpoint not in adjacencies):
        return None
    for option in adjacencies[currentpoint]:
        if (option["to"] in visited):
            continue
        journey.append(option)
        visited.add(option["from"])
        nextStop = option["to"]
        dfsTravel(nextStop, endpoint, max_path_length, journey[:])
        journey.pop(-1)
        visited.remove(option["from"])
    
    for i in results:
        if ( len(i) > max_path_length ):
            results.remove(i)



#use same results list as the first DFS algorithm
def iterativeDFS(adj_list, startpoint, endpoint, max_path_length = math.inf):
    if (startpoint == endpoint):
        print("You are already at your destination!")
        return None

    # Defining variables necessary for a stack-based DFS algorithm
    # the stack initally contains a segment that connects the spawn to one of its neighbours
    sub_path = []
    visited = [startpoint]
    stack = [adj_list[startpoint][0]]

    while len(stack) > 0:
        stack_top = stack.pop()
        destination = stack_top["to"]

        sub_path.append(stack_top) # storing the path that moved the user forward

        if (destination == endpoint):
            results.append(sub_path[:])

            #implementing the iterative version of backtracking
            if (len(stack)):
                while sub_path[-1]["to"] != stack[-1]["from"]:
                    _ = sub_path.pop()
                    if _["to"] in visited:
                        visited.remove(_["to"])
            continue

        if (destination not in visited):
            visited.append(destination)

            preAdjSearch_stacklength = len(stack)

            for seg in adj_list[destination]:
                if (seg["to"] not in visited):
                    stack.append(seg)
                
                # cleaning up sub_path after reaching explicit dead ends
                elif (seg["to"] in visited) and (len(adjacencies[seg["from"]]) == 1):
                    while (sub_path[-1]["to"] != stack[-1]["from"]):
                        failedpath = sub_path.pop()
                        visited.remove(failedpath["to"])
            
            # cleaning up sub_path after reaching silent dead ends
            if (preAdjSearch_stacklength == len(stack)):
                while (sub_path[-1]["to"] != stack[-1]["from"]):
                    failedpath = sub_path.pop()
                    visited.remove(failedpath["to"])
    
    for i in results:
        if ( len(i) > max_path_length ):
            results.remove(i)
            



dfsTravel("HKU", "Tsim Sha Tsui")
for subitem in results:
    for sub_subitem in subitem:
        print(sub_subitem)
    print("--------------------")