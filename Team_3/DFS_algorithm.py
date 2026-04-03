"""
This is the DFS_algorithm.py file.

It implements two major functions: createAdjList and journeyGenerator.

createAdjList: returns adj_list, a dictionary that is structured as follows:
    adj_list = {
        "stop_name1": ["neighbour1", "neighbour2", ...],
        "stop_name2": ["neighbour1", "neighbour2", ...],
        "stop_name3": ["neighbour1", "neighbour2", ...],
        ...
    }

journeyGenerator: ...

NOTE:
    This module keeps input/data validation to a minimum for code readability.
    Those functions have been dealt with in io_handler.py and validator.py.

"""

#generate an adjacency list for all stops
def createAdjList(segments):
    adj_list = {}

    for seg in segments:
        startpoint = seg["from"]
        endpoint = seg["to"]
        
        if startpoint not in adj_list:
            adj_list[startpoint] = []
        
        adj_list[startpoint].append(endpoint)

    return adj_list

def journeyGenerator(map, adj_list):
    pass