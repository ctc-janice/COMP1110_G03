'''
main.py
=======
Entry point for the Smart Public Transport Advisor.
 
Usage:
    python main.py
 
On Windows only, install curses support first:
    pip install windows-curses
 
Requires:
    Controller_IO/sample_data/stops.csv
    Controller_IO/sample_data/segments.csv
'''
 
from tui import main
 
if __name__ == '__main__':
    main()