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
    if s["from"] not in adjacencies:
        adjacencies[s["from"]] = []
    adjacencies[s["from"]].append(s)

results=[]
visited=set()
def dfsTravel(currentpoint, endpoint, journey=[]):
    if currentpoint == endpoint:
        results.append(journey)
        journey=[]
        return None
    if currentpoint not in adjacencies:
        return None
    for option in adjacencies[currentpoint]:
        if option["to"] in visited:
            continue
        journey.append(option)
        visited.add(option["from"])
        nextStop = option["to"]
        dfsTravel(nextStop, endpoint, journey[:])
        journey.pop(-1)
        visited.remove(option["from"])


# the code below is the version of the algorithm before the handling of dead ends was
# implemented. it is DEFECTIVE.

#use same results list as the first DFS algorithm
def iterativeDFS(adj_list, startpoint, endpoint):
    if startpoint == endpoint:
        print("You are already at your destination!")
        return None

    # Defining variables necessary for a stack-based DFS algorithm
    # the stack initally contains a segment that connects the spawn to one of its neighbours
    sub_path = []
    visited = [startpoint]
    stack = [adj_list[startpoint][0]]
    
    """ Running the DFS algorithm
    ------------------------------------
    This algorithm traverses segments while loading them into a list called sub_path.

    It appends sub_path to the list of results when it successfully gets to
    the destination.

    Unlike a recursive algorithm, in which copies of sub_path are deleted once each
    recursive call ends, an iterative algorithm has to use explicit rules to clean up
    sub_path after unwanted paths or successful attempts.

    The two main challenges that this algorithm faces are:
        1. cleaning up the sub_path list after reaching dead ends
        2. cleaning up the sub_path list while backtracking
    
    ------------------------------------
    """


    while len(stack) > 0:
        stack_top = stack.pop()
        destination = stack_top["to"]

        sub_path.append(stack_top)

        if destination == endpoint:
            results.append(sub_path[:])

            #implementing the iterative version of backtracking
            if len(stack):
                while sub_path[-1]["to"] != stack[-1]["from"]:
                    _ = sub_path.pop()
                    if _["to"] in visited:
                        visited.remove(_["to"])
    
            continue

        if destination not in visited:
            visited.append(destination)

            for seg in adj_list[destination]:
                if seg["to"] not in visited:
                    stack.append(seg)
                
                # cleaning up sub_path after reaching dead ends
                elif (seg["to"] in visited) and (len(adjacencies[seg["from"]]) == 1):
                    while (sub_path[-1]["to"] != stack[-1]["from"]):
                        failedpath = sub_path.pop()
                        visited.remove(failedpath["to"])

"""
----
Undeveloped Iterative Version
-----
def journeyGenerator(map_stops, map_segments, adj_list, startpoint, finalstop):
    if startpoint == finalstop:
        print("You are already at your destination!")
        return None

    # Defining variables necessary for a stack-based DFS algorithm
    successful_paths = []
    visited = []
    stack = [startpoint]
    
    # Running a DFS algorithm
    while len(stack) > 0:
        sub_path = []
        loc = stack.pop()
        if loc == finalstop:
            successful_paths.append(sub_path)
        if loc not in visited:
            visited.append(loc)
            for place in adj_list[loc]:
                if place["from"] not in visited:
                    stack.append(place)
"""

iterativeDFS(adjacencies, "HKU", "Wan Chai")
for subitem in results:
    for sub_subitem in subitem:
        print(sub_subitem)
    print("--------------------")