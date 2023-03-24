#!/usr/bin/env python
import PySimpleGUI as sg
import pandas as pd
import xlwings as xw
#import base64
import re
#import plotly.express as px
import matplotlib.pyplot as plt
#from matplotlib.figure import Figure
"""
    Demonstration of MENUS!
    How do menus work?  Like buttons is how.
    Check out the variable menu_def for a hint on how to 
    define menus
"""
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)
# Dataframes
maindf = pd.DataFrame() # extracted data from file
plotdf = pd.DataFrame() # data read for plot
#df=pd.DataFrame() # added to avoid bugs as I work through this.  

window_icon = r'C:\Users\lstrickland\PycharmProjects\VSAMGui\dataanalysis.ico'
windows = [] # array to store windows
data_for_windows = [] # array to store data in windows (used for sorting)

#filters
MaxRatio = 10
DSN_include_regex, DSN_exclude_regex = "",""
JOB_include_regex, JOB_exclude_regex = "",""
startDateTime, finishDateTime = "", ""
x, y = 100,100

main_win = None

def list_window(df,name):
    global x, y
    header_list = list(df.columns.values)
    data = df[0:].values.tolist()
    layout = [
        [sg.Text(text="Progress", key= '-Progress-')],
        [sg.Table(values=data,
                  headings=header_list,
                  display_row_numbers=False,
                  justification='left',
                  auto_size_columns=True,
                  alternating_row_color='lightblue',
                  key='-TABLE-',
                  selected_row_colors='red on yellow',
                  enable_events=True,
                  expand_x=True,
                  expand_y=True,
                  enable_click_events=True,
                  num_rows=min(25, len(data))),],
        [sg.Text(text = "", size = (60, 1), key = '-Selected-')],
        [sg.Button('Ok'), sg.Button('Replot'), sg.Button('Replot with write rates'), sg.Button('To Excel')],
        #[sg.Button('Ok'), sg.Button('DSN Group by Job'), sg.Button('DSN Detail'), sg.Button('To Excel'), sg.Text('   '),
        # sg.Button('Filter by Date Time'), sg.Button('Filter by R_JOB'),sg.Button('Filter by R_DSN'), sg.Button('Filter by max_size_gb')],
        
    ]
    x = x+20; y=y+20

    return sg.Window(name, layout, icon=window_icon, location = (x,y), grab_anywhere=False, resizable = True,finalize=True)

def table_window(df, name):
    global x, y
    x = x+20; y=y+20
    #df should have column 'Unique ID' 

def main_window():
    sg.theme('Material1')
    sg.set_options(element_padding=(2, 2))

    # ------ Menu Definition ------ #
    menu_def = [['&File', ['&Open', 'Clear',  'E&xit']],
                ['F&ilters', ['&DateTime Range', 'Max Ratio'], ],
                ['View', ['Loaded Data','Plot Data']],
                ['!&Help', '&About...'], ]

    #right_click_menu = ['Unused', ['Right', '!&Click', '&Menu', 'E&xit', 'Properties']]

    # ------ GUI Defintion ------ #
    layout = [
        [sg.Menu(menu_def, tearoff=False, pad=(200, 1))],
        #[sg.Text('Right click me for a right click menu example')],
        [sg.Output(size=(60, 20))],
        #[sg.ButtonMenu('ButtonMenu',  right_click_menu, key='-BMENU-'), sg.Button('Plain Button')],
    ]

    return sg.Window("Main Window",
                       layout,
                       default_element_size=(12, 1),
                       default_button_element_size=(12, 1),
                       #right_click_menu=right_click_menu,
                       icon=window_icon,
                       location = (x,y),
                       finalize=True)

   
def main():
    global startDateTime, finishDateTime #, R_DSN_include, R_DSN_exclude, R_JOB_include, R_JOB_exclude
    global windows
    global data_for_windows
    #global df, maindf
    global main_win
    main_win = main_window()
    #windows.append(main_window())
    #data_for_windows.append(pd.DataFrame)
    # ------ Loop & Process button menu choices ------ #
    while True:
        window, event, values = sg.read_all_windows()
        
        # Get window index i
        i=0
        for win in windows:
            if window == win:  
                break
            i = i+1
        #`(i)
        if window == sg.WIN_CLOSED:     # if all windows were closed
            break
        if event == sg.WIN_CLOSED or event == 'Exit':
            window.close()
            if i < len(windows): # otherwise currently main window
                windows.pop(i)
                data_for_windows.pop(i)
           
       # print('window')
        #print(window)
        #print('event')
       # print(event)
        #print('values')
        #print(values)
        # ------ Process menu choices ------ #
        if event == 'About...':
            window.disappear()
            sg.popup('About this program', 'Version 1.0','Application written by Larry Strickland, no warrantee provided or implied',
                     'PySimpleGUI Version', sg.version,  grab_anywhere=True)
            window.reappear()
        elif event == '-TABLE-':
            print(values[event])
            rows_selected = values[event]
        elif event =='Replot':
            print(event)
            #get selected rows with rows_selected
            if not rows_selected: loadTablesPlot()
            else:
                plotSelected(data_for_windows[i], rows_selected)
                rows_selected = []
        elif event == 'Replot with write rates':
            print(event)
            #get selected rows with rows_selected
            if not rows_selected: loadTablesPlot()
            else:
                plotSelected(data_for_windows[i], rows_selected, True)
                rows_selected = []
        elif event =='DateTime Range':
            getDateTimeRange()
        elif event =='Max Ratio':
            getMaxRatio()
        # elif event =='R_DSN Exclude (regex)':
        #     getDSNExclude()
        # elif event =='R_JOB Include (regex)':
        #     getJOBInclude()
        # elif event =='R_JOB Exclude (regex)':
            # getJOBExclude()
        elif event == 'Open':
            filenames = sg.popup_get_file(
                'filename to open', no_window=True, file_types = (('ALL Files', '*.* *'),), multiple_files = True,files_delimiter = ";")
            #print('Loading and processing file:{}'.format(filename))
            #sg.popup_get_text('NS ..',default_text=filenames[0])
        
            for file in filenames:
                #try:
                    print('Loading file '+file)
                    process_file(file)
                #except:
                    #sg.popup_error('Error reading file', icon=window_icon)
            
            loadTablesPlot()
            
        elif event == 'To Excel':
            toExcel()
        elif event == 'Clear':
            clearAll()
        elif event == 'Ok':
            window.close()
            windows.pop(i)
            data_for_windows.pop(i)
        elif event == 'Loaded Data':
            windows.append(list_window(maindf, 'Loaded Data' ))
            data_for_windows.append(maindf)
            windows[-1]['-Progress-'].update('Loaded Data')
        elif event == 'Plot Data':
            windows.append(list_window(plotdf, 'Plot Data'))
            data_for_windows.append(plotdf)
            windows[-1]['-Progress-'].update('Plot Data')
         
        # elif event == 'DSN Group by Job':
        #     if len(window['-Selected-'].get()) > 1:
        #         data_for_windows.append(groupByJOB(window['-Selected-'].get()))
        #         windows.append(list_window(data_for_windows[-1], window['-Selected-'].get() +' by R_JOB'))
        #         windows[-1]['-Progress-'].update(f'R_DSN={window["-Selected-"].get()}, Grouped R_JOB')
        #     else:
        #         sg.popup_error('Select row first')
        # elif event == 'DSN Detail':
        #      if len(window['-Selected-'].get()) > 1:
        #          data_for_windows.append(detail(window['-Selected-'].get()))
        #          #.insert(0, "DSN", window['-Selected-'].get(), allow_duplicates=False)
        #          windows.append(list_window(data_for_windows[-1], window['-Selected-'].get()))
        #          windows[-1]['-Progress-'].update(f'R_DSN={window["-Selected-"].get()}')
        #      else:
        #         sg.popup_error('Select row first', icon=window_icon)

        # if isinstance(event, tuple):
        #     # TABLE CLICKED Event has value in format ('-TABLE-', '+CLICKED+', (row,col))
        #     if event[0] == '-TABLE-':
        #         print(event)
        #         if event[2][0] == -1 and event[2][1] != -1:           # Header was clicked and wasn't the "row" column
        #             col_num_clicked = event[2][1]
        #             #col_name_clicked = window['-TABLE-'].headings[col_num_clicked]
        #             header = data_for_windows[i].columns.values[col_num_clicked]
        #             window['-Selected-'].update(f'Column Header ({event[2][1]}) clicked  {header}')
        #             data_for_windows[i] = data_for_windows[i].sort_values(header, ascending=False)  #.reset_index(drop=True)
        #             data = data_for_windows[i][0:].values.tolist()
        #             #new_table = sort_table(data[1:][:],(col_num_clicked, 0))
        #             window['-TABLE-'].update(data)
        #             #data = [data[0]] + new_table
        #         elif event[2][0] != -1 and event[2][1] != -1:
        #             row_num_clicked = event[2][0]
        #             #row_name_clicked = window.data_selected[0]
        #             cell = data_for_windows[i]
        #             window['-Selected-'].update(f'{cell.iloc[row_num_clicked][0]}')
        #         #window['-CLICKED-'].update(f'{event[2][0]},{event[2][1]}')
            
def toExcel():
    wb = xw.Book() # create a new workbook
    # for each openned window, create spreadsheet with window contents (in same order windows openned)
    for j in range(len(windows)-1, -1, -1):
        win_title = windows[j].Title
        if len(win_title)>31:
            win_title = win_title[0:30]
        sht = wb.sheets.add(win_title)
        sht.range('A1').options(index=False).value = data_for_windows[j]
        sht.used_range.select()              # Select the used range of the sheet.
        tbl_range = sht.range("A1").expand()
        sht.api.ListObjects.Add(1, sht.api.Range(tbl_range.address))
        sht.autofit(axis="columns")
        sht.range(tbl_range).number_format = '[>=10]#,##0 ;[>=1]  #,###.0;  0.00'
    wb.sheets('Sheet1').delete()
    return

def plotSelected(df, selected_rows, show_writes=False):
    global plotdf
    for j in range(len(windows)-1, -1, -1):
        windows[j].close()
        windows.pop(j)
        data_for_windows.pop(j)
    #print(df)
    #print(selected_rows)
    newdf = df.loc[selected_rows]
    #print(newdf)
    plotdf = plotdf[plotdf['id'].isin(newdf['Unique ID'])]
    #unique_tables = pd.DataFrame(plotdf.id.unique(), columns=['Unique ID'])
    #unique_tables['table'] = unique_tables['Unique ID'].apply(lambda x: x.split('.')[-1])
    data_for_windows.append(getUniqueTables())
    windows.append(list_window(data_for_windows[-1], 'Unique Data'))
    make_plot(show_writes)
    return

def loadTablesPlot():
    global MaxRatio
    global data_for_windows, windows
    
    for j in range(len(windows)-1, -1, -1):
        windows[j].close()
        windows.pop(j)
        data_for_windows.pop(j)
    update_plotdata(MaxRatio)
    
    data_for_windows.append(getUniqueTables())
    windows.append(list_window(data_for_windows[-1], 'Unique Data'))
    make_plot()
    return

def getUniqueTables():
    # Need to add peak and trough for read rate to this table.  
    unique_tables = plotdf[['id','average','read_rate','write_rate']]
    #unique_tables.rename(columns = {'id':'Unique ID','average':'Read Rate Average'})
   # unique_tables.set_index('Unique ID')
    #unique_tables = pd.concat([plotdf['id'],plotdf['average']], axis=1, keys=['Unique ID','Read Rate Average'])
    unique_tables = unique_tables.groupby(['id'], as_index=False).agg({'average':'mean', 'read_rate':['max','min'], 'write_rate':['max','min']})
    unique_tables['Table'] = unique_tables['id'].apply(lambda x: x.split('.')[-1])
    unique_tables.columns = ['Unique ID', 'Read Rate Average','Read Rate Max','Read Rate Min', 'Write Rate Max', 'Write Rate Min','Table']
    #unique_tables = unique_tables.sort_values(['average'], ascending= False).reset_index(drop=True)
    unique_tables = unique_tables[['Table','Unique ID','Read Rate Average','Read Rate Max','Read Rate Min', 'Write Rate Max', 'Write Rate Min']].sort_values(['Read Rate Average'], ascending= False).reset_index(drop=True)
    return unique_tables

def clearAll():
    global plotdf, maindf
    global data_for_windows, windows, MaxRatio
    MaxRatio = 10
    plotdf = pd.DataFrame()
    maindf = pd.DataFrame()
    for j in range(len(windows)-1, -1, -1):
        windows[j].close()
        windows.pop(j)
        data_for_windows.pop(j)
    plt.clf()
    plt.show(block=False)
    return

# def toExcel():
#     wb = xw.Book() # create a new workbook
#     # for each openned window, create spreadsheet with window contents (in same order windows openned)
#     for j in range(len(windows)-1, -1, -1):
#         win_title = windows[j].Title
#         if len(win_title)>31:
#             win_title = win_title[0:30]
#         sht = wb.sheets.add(win_title)
#         sht.range('A1').options(index=False).value = data_for_windows[j]
#         sht.used_range.select()              # Select the used range of the sheet.
#         tbl_range = sht.range("A1").expand()
#         sht.api.ListObjects.Add(1, sht.api.Range(tbl_range.address))
#         sht.autofit(axis="columns")
#     wb.sheets('Sheet1').delete()
#     return

def getDateTimeRange():
    global startDateTime, finishDateTime
    newDateTime = sg.popup_get_text('Update start/finish Date Time (keep formating)', default_text=f'{startDateTime},{finishDateTime}', icon=window_icon)
    if newDateTime is not None:
        splitDateTime = newDateTime.split(',')
        if len(splitDateTime) == 2:
            if not pd.isnull(pd.to_datetime(splitDateTime[0],errors='coerce')) and not pd.isnull(pd.to_datetime(splitDateTime[1],errors='coerce')):
                if pd.to_datetime(splitDateTime[0],errors='coerce') < pd.to_datetime(splitDateTime[1],errors='coerce'):
                    startDateTime = splitDateTime[0]
                    finishDateTime = splitDateTime[1]
                    #Trigger refresh of windows
                    #runFilter()
                    #clearAndLoadMaind() # ideally refresh each window based on new filter - 
                    loadTablesPlot()
                else:
                    sg.popup_error('Start date time must be less than finish date time')
            else:
                sg.popup_error('Invalid date time format')
        else:
            sg.popup_error('two date times required')
    return

def getMaxRatio():
    global MaxRatio
    val = sg.popup_get_text('Update REGEX to include DSN', default_text=f'{MaxRatio}', icon=window_icon)
    if val.isdigit():
        MaxRatio = int(val)
        update_plotdata(MaxRatio)
    loadTablesPlot()
    return

def runFilter():
    
    df = maindf[(maindf['Timestamp'] < pd.to_datetime(finishDateTime)) & (
                maindf['Timestamp'] > pd.to_datetime(startDateTime))]
    if JOB_exclude_regex:
        df=df[~df.R_JOB.str.contains(JOB_exclude_regex, regex= True, na=False)]
    if JOB_include_regex:
         df=df[df.R_JOB.str.contains(JOB_include_regex, regex= True, na=False)]
    if DSN_exclude_regex:
        df=df[~df.R_JOB.str.contains(DSN_exclude_regex, regex= True, na=False)]
    if DSN_include_regex:
        df=df[df.R_JOB.str.contains(DSN_include_regex, regex= True, na=False)]
    return df

def clearAndLoadMaind():
    global windows, data_for_windows, x, y
    for j in range(len(windows)-1, -1, -1):
        windows[j].close()
        windows.pop(j)
        data_for_windows.pop(j)
    # clear filters
    x, y = 100, 100
    
    # runFilter()
    #data_for_windows.append(groupByDSN())
    windows.append(list_window(data_for_windows[-1], 'Group by DSN'))
    windows[-1]['-Progress-'].update('Grouped by DSN')
    return

def make_plot(show_writes=False):
    global plotdf
    #fig = plt.figure("Plots")
    if plt.get_fignums():
        plt.clf()
    plt.figure('Plot')
    for id in plotdf.id.unique():
        tableName = id.split('.')[-1]
        linedf = plotdf[plotdf['id'].str.fullmatch(id)]
        plt.plot(linedf['start_time'], linedf['read_rate'], label=tableName)
        if show_writes:
            plt.plot(linedf['start_time'], linedf['write_rate'], label=tableName+'-read')
        #plotdf[plotdf['id'].str.fullmatch(id)].plot(kind = 'line', x="start_time", y="read_rate")
        #plotdf[plotdf['id'].str.fullmatch(id)].plot(kind = 'line', x="start_time", y="read_rate", error_x="time_diffs", hover_data=["write_rate", "Size(gb)"])
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.show(block=False)
    return

def update_plotdata(maxratio):
    global plotdf
    
    if maindf is not None:
        # df = runfilter()
        df = runFilter().sort_values(['id', 'Timestamp'])
        # apply filter to df.  
        
        df['read_diffs'] = df.groupby(['id'])['Accesses'].transform(lambda x: x.diff())
        df['time_diffs'] = df.groupby(['id'])['Timestamp'].transform(lambda x: x.diff())
        df['start_time'] = df['Timestamp'] - df['time_diffs']
        df['time_diffs_seconds'] = df['time_diffs'].transform(lambda x: x.total_seconds())
        df['write_diffs'] = df.groupby(['id'])['Writes'].transform(lambda x: x.diff())
        df['read_rate'] = df['read_diffs'] / df['time_diffs_seconds']
       
        df['write_rate'] = df['write_diffs'] / df['time_diffs_seconds']
        with pd.option_context('mode.use_inf_as_na', True):
            df = df[df['read_rate'].notna()]
        df = df[df['read_rate'] > 0]
        df['average'] = df.groupby(['id'])['read_rate'].transform(lambda x: x.mean())

        # create new data from to plot start/end lines
        df2 = df[~df['start_time'].isnull()]
        df2['start_time'] = df2['Timestamp']
        df2.loc[:, 'start_time'] -= pd.Timedelta(1, unit='s')
        df = pd.concat([df,df2], ignore_index=True)
        df = df.sort_values(['average', 'Timestamp', 'start_time'], ascending=[False, True, True])
        max_max = df['average'].max() / int(maxratio)
        df = df.groupby(['id']).filter(lambda x: x['average'].max() > max_max)
       # df['Table'] = df['id'].apply(lambda x: x.split('.')[-1])

        #max_rows = 1000
        plotdf = df.sort_values(['average', 'Timestamp', 'start_time'], ascending=[False, True, True])
        return

def process_file(filename):
    global startDateTime
    global finishDateTime
    global maindf
    #global df
    #decoded = base64.b64decode(content_string)
    regex1 = "\s*(([A-Za-z0-9_]){1,8}\s+){2}(([A-Za-z0-9_#?]){1,128}\s+){2}[0-9]{4}(-([0-9]){2}){3}(\.([0-9]){2}){2}(\s+([0-9])+){4}"
    regex2 = "s*(([A-Za-z0-9_]){1,8}\s+){2}(([A-Za-z0-9_#?]){1,128}\s+){2}[0-9]{4}(-([0-9]){2}){2}\s+(([0-9]){2}:){2}([0-9]){2}(\s+([0-9])+){4}"
    regex1date = "([0-9]{4})-([0-9]{2})-([0-9]{2})-([0-9]{2}).([0-9]{2}).([0-9]{2})"
    lines_list = []
    badlines = ""

    #try:
    
    for line in open(filename):
        if re.match(regex1, line):
            # lines += line
            dict1 = {k: v for k, v in enumerate(line.split())}
            sd = re.split(regex1date, dict1[4])
            dict1[4] = sd[1] + '-' + sd[2] + '-' + sd[3] + 'T' + sd[4] + ':' + sd[5] + ':' + sd[5]

            lines_list.append(dict1)
        elif re.match(regex2, line):
            dict1 = {k: v for k, v in enumerate(line.split())}
            dict1.update({4: dict1[4] + 'T' + dict1[5]})
            dict1.pop(5)
            lines_list.append(dict1)
        else:
            badlines += line

    df = pd.DataFrame(lines_list)
    df.columns = ['DB', 'TS', 'Schema', 'Table', 'Timestamp', 'Accesses', 'Writes', 'Size(kb)', 'Prts']
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['id'] = df['DB'] + "." + df['TS'] + "." + df['Schema'] + "." + df['Table']
    df['Size(gb)'] = df['Size(kb)'].astype(float).div(1048576).round(4)
    df = df.drop(['DB', 'TS', 'Schema','Table'], axis=1)
    numeric_cols = ['Accesses','Writes','Size(kb)']
    df[numeric_cols] = pd.to_numeric(df[numeric_cols].stack(), errors='coerce').unstack()
    df = df.dropna()
    if maindf is None:
        maindf = df.sort_values(['id', 'Timestamp'])
    else:
        maindf = pd.concat([maindf, df.sort_values(['id', 'Timestamp'])], ignore_index=True)
        
    startDateTime = min(maindf['Timestamp'])
    finishDateTime = max(maindf['Timestamp'])
        
    return
    

if __name__ == '__main__':
    main()