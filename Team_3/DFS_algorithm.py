"""
This is the DFS_algorithm.py file.

It implements two major functions: createAdjList and journeyGenerator.

createAdjList: returns adj_list, a dictionary that where each key is the name of
a stop and each value is a list of all the segments that emerge from that stop:
    adj_list = {
        "stop_name1": ["segment_to_neighbour1", "segment_to_neighbour2", ...],
        "stop_name2": ["segment_to_neighbour3", "segment_to_neighbour4", ...],
        "stop_name3": ["segment_to_neighbour5", "segment_to_neighbour6", ...],
        ...
    }

recursive_journeyGenerator is the recursive implementation of a DFS algorithm
that traverses the map, and iterative_journeyGenerator is the iterative
implementation.

NOTE:
    This module keeps input/data validation to a minimum for code readability.
    Those functions have been dealt with in io_handler.py and validator.py.
"""


#   Generate an adjacency list for all stops
#   Reads the list of segments and extracts two things from each segment:
#   the "from" stop, and the "to" stop ("from" and "to" are keys in each segment)

def createAdjList(segments):
    adj_list = {}

    for seg in segments:
        startpoint = seg["from"]
        endpoint = seg["to"]
        
        if startpoint not in adj_list:
            adj_list[startpoint] = []
        
        adj_list[startpoint].append(seg)

    return adj_list

results = []
visited = set()
def recursive_journeyGenerator(adj_list, currentpoint, endpoint, journey=[]):
    if currentpoint == endpoint:
        results.append(journey)
        journey=[]
        return None
    if currentpoint not in adj_list:
        return None
    for option in adj_list[currentpoint]:
        if option["to"] in visited:
            continue
        journey.append(option)
        visited.add(option["from"])
        nextStop = option["to"]
        recursive_journeyGenerator(nextStop, endpoint, journey[:])
        journey.pop(-1)
        visited.remove(option["from"])


#use same results list as the first DFS algorithm
def iterativeDFS(adj_list, startpoint, endpoint):
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