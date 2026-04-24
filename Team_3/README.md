Running the DFS algorithm

    The two most important parts of the algorithm are its while loop and two if statements nested within it.

    Upon each iteration, while loop pops off the top element from the stack and assigns it to a variable named stack_top. This element is one of the segments in the map, stored as a dictionary. It then assigns the stop at the end of that segment to a variable named destination.

    Now, an important thing to note is that, even though the variable is named "destination," you may think of it as the algorithm's current location. The reason for this because the algorithm always performs computations on the end stop of the segment its currently traversing. Thus, the program is written as if that point is where it's already at.
    
    Consequently, the program performs two checks on the stop stored in the destination variable.
        The first one (if(destination == endpoint)) checks to see if it's equal to the user's target location.
        The second one checks to see if the that stop has not been visited before. If it has not been visited, the algorithm does a few main things:
            1. It adds it to the visited list.
            2. It runs a for loop which searches the adjacency list and adds all its (unvisited) neighbours to the stack.
            3. Additionally, it also tests for silent dead ends (visiting a node whose neighbours have all been visited). It does this by storing the length of the stack before the for loop/adjacency search in a variable. Then, after the for loop has run, it compares the length of the stack with the value of the variable. If the stack's length has not changed, it repeatedly removes elements from the sub_path list until the choice at the top of the stack can proceed.

    It appends sub_path to the list of results when it successfully gets to the destination.

    Unlike a recursive algorithm, in which copies of sub_path are deleted once each recursive call ends, an iterative algorithm has to use explicit rules to clean up sub_path after unwanted paths or successful attempts.

    The two main challenges that this algorithm faces are:
        1. cleaning up the sub_path list while backtracking
        2. cleaning up the sub_path list after reaching dead ends
            Note: there are two kinds of dead ends that the algoritm has to deal with:

            a. Silent dead ends: happen when the algorithm travels to a node (with two or more neighbours) whose neighbours have all been visited.
            b. Explicit dead ends: are a special kind of silent dead end that happen when the algorithm travels to a node at the end of an MTR line. In that case, the node has only one neighbour, and the algorithm has already been there, so it triggers a dead end.
    
    For clarification, the difference between backtracking and dealing with dead ends is the fact that backtracking happens after a successful trip to the destination while a post-dead-end cleanup happens after the algorithm fails to travel any further (due to a dead end).