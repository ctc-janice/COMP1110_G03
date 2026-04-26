'''
main.py
=======
Entry point for the Smart Public Transport Advisor.
 
Usage:
    python main.py
 
On Windows only, install curses support first:
    pip install windows-curses
 
Requires:
    Team_2/sample_data/stops.csv
    Team_2/sample_data/segments.csv
'''
 
from tui import main
 
if __name__ == '__main__':
    main()