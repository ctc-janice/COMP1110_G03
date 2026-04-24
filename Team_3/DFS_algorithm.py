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