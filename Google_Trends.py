"""
Richard Herron

python Google_Trends.py path/to/Data/input_file.txt [first_line last_line pause_override]

v0.1

-   Run from "../Code" folder
-   reads/writes from a "../Data" folder at the same folder level
-   first_line, last_line, and pause_override are optional and allow:
    -   completing an aborted run 
    -   completing a subset of a given file
        -   permits one input file 
        -   work through it in chunks
        -   even chunks that time out
        -   just pick up with the last completed line
        -   output file names based on input file name and line number
    -   overriding pause length specified in file header
        -   might be handy if you want to exhaust query limit
        -   there's a limit of 1 sec to be a good citizen (silent limit)
-   throughout I'm using the following convention
    -   `row` is the object (i.e., string from input file)
    -   `line` is the counter (i.e., integer from 1 to bottom)
    -   `o` for outer loop and `i` for inner

v0.2 

-   add search by country (or region)
-   add console log

"""

# packages
import cookielib
import csv
import mechanize #needs to be downloaded, use pip
import os
import StringIO
import sys
import time
import logging

if __name__ == '__main__':


    # create log
    log_file = '../Logs/' + sys.argv[1].split('/')[-1].replace('.csv', '.log')
    logging.basicConfig(level = logging.DEBUG, filename = log_file, filemode = 'w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    # create browser and cookie jar, then act like real browser
    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    # zeroth arg is script name
    # first arg is input file name
    # optional second arg is start line 
    # optional third arg is stop line 
    # optional fourth arg is pause override
    start_line = int(sys.argv[2]) if (len(sys.argv) > 2) else 1
    stop_line = int(sys.argv[3]) if (len(sys.argv) > 3) else int(1e6)
    pause_override = max(int(sys.argv[4]), 1) if (len(sys.argv) > 4) else None

    # loop over rows in input file
    line_o = 0
    with open(sys.argv[1]) as input_file:
        for row_o in csv.reader(input_file):

            # first row is username, password, and pause length
            if any(row_o) & (line_o == 0):
                username, password, pause = row_o
                pause = int(pause) if (pause_override == None) else pause_override

                # echo login and pause length information
                logging.info('Username: ' + username)
                logging.info('Password: ' + password)
                logging.info('Pause: ' + str(pause))

                # login to Google with username and password
                response = br.open('https://accounts.google.com/ServiceLogin?hl=en&continue=https://www.google.com/')
                forms = mechanize.ParseResponse(response)
                form = forms[0]
                form['Email'] = username
                form['Passwd'] = password
                response = br.open(form.click())

            # remaining rows are query and countries
            elif any(row_o) & (line_o > 0) & (start_line <= line_o) & (line_o <= stop_line):

                # output filename root
                output_root = sys.argv[1].replace('.csv', '_' + str(line_o)) 

                # pause before subsequent queries
                if (line_o > 1): time.sleep(pause)

                # generate query url
                url_head = 'http://www.google.com/trends/trendsReport?'
                query = row_o.pop(0)
                if any(row_o):
                    url_heart = 'q=' + query.replace(' ', '%20') + '&geo=' + '%2C%20'.join(row_o) + '&cmpt=geo'
                else:
                    url_heart = 'q=' + query.replace(' ', '%20') 
                url_tail = '&export=1'
                url_complete = url_head + url_heart + url_tail
                logging.info('Line ' + str(line_o) + ': ' + url_complete)

                # get/read .csv file from Google Trends
                response = br.open(url_complete)

                # split .csv file into many
                section_i = 0
                line_i = 0
                for row_i in csv.reader(StringIO.StringIO(response.read())):
                    if any(row_i) & (line_i == 0):
                        output_file = output_root + '_' + str(section_i) + '.csv'
                        output = open(output_file, 'wb')
                        writer = csv.writer(output)
                        writer.writerow(row_i)
                        line_i += 1

                    elif any(row_i) & (line_i > 0):
                        writer.writerow(row_i)
                        line_i += 1

                    elif (line_i > 0):
                        output.close()
                        section_i += 1
                        line_i = 0

            # increment outer loop row number
            line_o += 1
