# utilities
import os
import sys
import glob
import logging
import pandas as pd
import numpy as np
from datetime import date

# figure plotting
import bokeh.models as bkm
from bokeh.io import show, curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, RangeTool, DatetimeTickFormatter, LabelSet
from bokeh.plotting import figure, show

# bokeh widgets
from bokeh.layouts import column, widgetbox
from bokeh.models.widgets import Button, Select, DateRangeSlider, TableColumn, DataTable

# import backtesting script
sys.path.append('./jupyter_py')
sys.path.append('./process_data')
sys.path.append('./log_helper')
sys.path.append('./model')

from decode_logs import *

# use this dictionary to store all backtesting params
backtest_params = {
    "strategy_type": "kalman",
    "stk_0": "AAN",
    "stk_1": "AER",
    "backtest_start": "2017-05-01",
    "backtest_end": "2017-12-31"
}
    
def build_price_and_spread_fig(data, action_df):
    # ========== themes & appearance ============= #
    STK_1_LINE_COLOR = "#053061"
    STK_2_LINE_COLOR = "#67001f"
    STK_1_LINE_WIDTH = 1.5
    STK_2_LINE_WIDTH = 1.5
    WINDOW_SIZE = 10
    TITLE = "PRICE OF {} vs {}".format(backtest_params["stk_0"], backtest_params["stk_1"]) 
    HEIGHT = 250
    SLIDER_HEIGHT = 150
    WIDTH = 600

    # ========== data ============= #
    # use sample data from ib-data folder
    dates = np.array(data['date'], dtype=np.datetime64)
    STK_1_source = ColumnDataSource(data=dict(date=dates, close=data['data0']))
    STK_2_source = ColumnDataSource(data=dict(date=dates, close=data['data1']))

    # ========== plot data points ============= #
    # x_range is the zoom in slider setup. Pls ensure both STK_1 and STK_2 have same length, else some issue
    normp = figure(plot_height=HEIGHT, 
                   plot_width=WIDTH, 
                   x_range=(dates[-WINDOW_SIZE], dates[-1]), 
                   title=TITLE, 
                   toolbar_location=None)

    normp.line('date', 'close', source=STK_1_source, line_color = STK_1_LINE_COLOR, line_width = STK_1_LINE_WIDTH)
    normp.line('date', 'close', source=STK_2_source, line_color = STK_2_LINE_COLOR, line_width = STK_2_LINE_WIDTH)
    normp.yaxis.axis_label = 'Price'

    normp.xaxis[0].formatter = DatetimeTickFormatter()
    
    # ========== render spread stuff ============= #
    
    palette = ["#053061", "#67001f"]
    LINE_WIDTH = 1.5
    LINE_COLOR = palette[-1]
    SPREAD_TITLE = "RULE BASED SPREAD TRADING"
    HEIGHT = 250
    WIDTH = 600

    # ========== data ============= #
    # TODO: get action_source array
    # TODO: map actions to colours so can map to palette[i]
    spread_source = ColumnDataSource(data=dict(date=dates, 
                                               spread=data['spread'], 
                                               upper_limit=data['upper_limit'], 
                                               lower_limit=data['lower_limit']))
    action_source = ColumnDataSource(action_df)
    # action_source['colors'] = [palette[i] x for x in action_source['actions']]

    # ========== figure INTERACTION properties ============= #
    TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

    spread_p = figure(tools=TOOLS, 
                      toolbar_location=None, 
                      plot_height=HEIGHT, 
                      plot_width=WIDTH, 
                      title=SPREAD_TITLE, 
                      x_range=(dates[-WINDOW_SIZE], dates[-1]))
    # spread_p.background_fill_color = "#dddddd"
    spread_p.xaxis.axis_label = "Backtest Period"
    spread_p.yaxis.axis_label = "Spread"
    # spread_p.grid.grid_line_color = "white"

    # ========== plot data points ============= #
    # plot the POINT coords of the ACTIONS
    circles = spread_p.circle("date", "spread", size=12, source=action_source, fill_alpha=0.8)

    circles_hover = bkm.HoverTool(renderers=[circles], tooltips = [
        ("Action", "@latest_trade_action"),                    
        ("Stock Bought", "@buy_stk"),
        ("Bought Amount", "@buy_amt"),
        ("Stock Sold", "@sell_stk"),
        ("Sold Amount", "@sell_amt")
        ])

    spread_p.add_tools(circles_hover)

    # plot the spread over time
    spread_p.line('date', 'spread', source=spread_source, line_color = LINE_COLOR, line_width = LINE_WIDTH)
    spread_p.line('date', 'upper_limit', source=spread_source, line_color = LINE_COLOR, line_width = LINE_WIDTH)
    spread_p.line('date', 'lower_limit', source=spread_source, line_color = LINE_COLOR, line_width = LINE_WIDTH)
    spread_p.xaxis[0].formatter = DatetimeTickFormatter()

    # ========== RANGE SELECT TOOL ============= #

    select = figure(title="Drag the middle and edges of the selection box to change the range above",
                    plot_height=SLIDER_HEIGHT, plot_width=WIDTH, y_range=normp.y_range,
                    x_axis_type="datetime", y_axis_type=None,
                    tools="", toolbar_location='above', background_fill_color="#efefef")

    range_tool = RangeTool(x_range=normp.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    
    range_tool_spread = RangeTool(x_range=spread_p.x_range)

    select.line('date', 'close', source=STK_1_source, line_color = STK_1_LINE_COLOR, line_width = STK_1_LINE_WIDTH)
    select.line('date', 'close', source=STK_2_source, line_color = STK_2_LINE_COLOR, line_width = STK_2_LINE_WIDTH)
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    select.add_tools(range_tool_spread)
    select.toolbar.active_multi = range_tool

    return column(normp, spread_p, select)

def build_pv_fig(data):
    # ========== themes & appearance ============= #
    LINE_COLOR = "#053061"
    LINE_WIDTH = 1.5
    TITLE = "PORTFOLIO VALUE OVER TIME" 

    # ========== data ============= #
    dates = np.array(data['date'], dtype=np.datetime64)
    pv_source = ColumnDataSource(data=dict(date=dates, portfolio_value=data['portfolio_value']))

    # ========== plot data points ============= #
    # x_range is the zoom in slider setup. Pls ensure both STK_1 and STK_2 have same length, else some issue
    pv_p = figure(plot_height=250, plot_width=600, title=TITLE, toolbar_location=None)
    pv_p.line('date', 'portfolio_value', source=pv_source, line_color = LINE_COLOR, line_width = LINE_WIDTH)
    pv_p.yaxis.axis_label = 'Portfolio Value'
    pv_p.xaxis[0].formatter = DatetimeTickFormatter()
    return pv_p

def build_widgets_wb(stock_list, metrics):
    # CODE SECTION: setup buttons, widgetbox name = controls_wb
    WIDGET_WIDTH = 250

    # ========== Select Stocks ============= #
    select_stk_1 = Select(width = WIDGET_WIDTH, title='Select Stock 1:', value = stock_list[0], options=stock_list)
    select_stk_2 = Select(width = WIDGET_WIDTH, title='Select Stock 2:', value = stock_list[1], options=stock_list)

    # ========== Strategy Type ============= #
    strategy_list = ['kalman', 'distance', 'cointegration']
    select_strategy = Select(width = WIDGET_WIDTH, title='Select Strategy:', value = strategy_list[0], options=strategy_list)

    # ========== set start/end date ============= #
    # date time variables
    MAX_START = date(2014, 1, 1)
    MAX_END = date(2018, 12, 30)
    DEFAULT_START = date(2017, 5, 1)
    DEFAULT_END = date(2017, 12, 31)
    STEP = 1

    backtest_dates = DateRangeSlider(width = WIDGET_WIDTH, 
                                     start=MAX_START, end=MAX_END, 
                                     value=(DEFAULT_START, DEFAULT_END), 
                                     step=STEP, title="Backtest Date Range:")

    start_bt = Button(label="Backtest", button_type="success", width = WIDGET_WIDTH)

    # controls = column(select_stk_1, select_stk_2, select_strategy, backtest_dates, start_bt)
    controls_wb = widgetbox(select_stk_1, select_stk_2, select_strategy, backtest_dates, start_bt, width=300)

    # CODE SECTION: setup table, widgetbox name = metrics_wb

    metric_source = ColumnDataSource(metrics)
    metric_columns = [
        TableColumn(field="Metrics", title="Metrics"),
        TableColumn(field="Value", title="Performance"),
    ]

    metric_table = DataTable(source=metric_source, columns=metric_columns, width=300)

    # return the master widgetbox
    master_wb = row(controls_wb, widgetbox(metric_table))
    return master_wb, select_stk_1, select_stk_2, select_strategy, backtest_dates, start_bt

output_dir = "./jupyter_py/output/backtest-" + str(get_current_time())
execution_command = """
python ./jupyter_py/backtest_pair.py \
--strategy_type {} \
--output_dir {} \
--backtest_start {} \
--backtest_end {} \
--stk0 {} \
--stk1 {}
"""
if backtest_params["strategy_type"] == "kalman":
    execution_command += " --kalman_estimation_length 200"
elif backtest_params["strategy_type"] == "cointegration":
    execution_command += " --lookback 76"
elif backtest_params["strategy_type"] == "distance":
    execution_command += " --lookback 70"

execution_command = execution_command.format(backtest_params["strategy_type"], 
                                            output_dir,
                                            backtest_params["backtest_start"],
                                            backtest_params["backtest_end"],
                                            backtest_params["stk_0"],
                                            backtest_params["stk_1"])

os.system(execution_command)

stock_list = glob.glob("./data/nyse-daily-tech/*.csv")
for i, file in enumerate(stock_list):
    stock_list[i] = os.path.basename(file)[:-4]

# get results from log file
backtest_df, trades_df = Decoder.get_strategy_status(output_dir)
metrics_dict = Decoder.get_strategy_performance(str(output_dir))
metrics_pd = pd.DataFrame.from_dict(metrics_dict, orient='index', columns=['Value']).reset_index()
metrics_pd.columns = ['Metrics', 'Value']

# build figures
spread_fig = build_price_and_spread_fig(backtest_df, trades_df)
pv_fig = build_pv_fig(backtest_df)
master_wb, select_stk_1, select_stk_2, select_strategy, backtest_dates, start_bt = build_widgets_wb(stock_list, metrics_pd)

def update_stk_1(attrname, old, new):
    backtest_params['stk_0'] = select_stk_1.value
    
def update_stk_2(attrname, old, new):
    backtest_params['stk_1'] = select_stk_2.value
    
def update_strategy(attrname, old, new):
    backtest_params['strategy_type'] = select_strategy.value

def update_dates(attrname, old, new):
    val = list(backtest_dates.value)
    # backtest_params['backtest_start'] = str(datetime.datetime.fromtimestamp(val[0]).date())
    # backtest_params['backtest_end'] = str(datetime.datetime.fromtimestamp(val[1]).date())

def run_backtest():
    output_dir = "./jupyter_py/output/backtest-" + str(get_current_time())
    execution_command = """
    python ./jupyter_py/backtest_pair.py \
    --strategy_type {} \
    --output_dir {} \
    --backtest_start {} \
    --backtest_end {} \
    --stk0 {} \
    --stk1 {}
    """
    if backtest_params["strategy_type"] == "kalman":
        execution_command += " --kalman_estimation_length 200"
    elif backtest_params["strategy_type"] == "cointegration":
        execution_command += " --lookback 76"
    elif backtest_params["strategy_type"] == "distance":
        execution_command += " --lookback 70"

    execution_command = execution_command.format(backtest_params["strategy_type"], 
                                                output_dir,
                                                backtest_params["backtest_start"],
                                                backtest_params["backtest_end"],
                                                backtest_params["stk_0"],
                                                backtest_params["stk_1"])

    os.system(execution_command)

    stock_list = glob.glob("./data/nyse-daily-tech/*.csv")
    for i, file in enumerate(stock_list):
        stock_list[i] = os.path.basename(file)[:-4]

    # get results from log file
    backtest_df, trades_df = Decoder.get_strategy_status(output_dir)
    metrics_dict = Decoder.get_strategy_performance(str(output_dir))
    metrics_pd = pd.DataFrame.from_dict(metrics_dict, orient='index', columns=['Value']).reset_index()
    metrics_pd.columns = ['Metrics', 'Value']

    # build figures
    spread_fig = build_price_and_spread_fig(backtest_df, trades_df)
    pv_fig = build_pv_fig(backtest_df)
    master_wb, select_stk_1, select_stk_2, select_strategy, backtest_dates, start_bt = build_widgets_wb(stock_list, metrics_pd)
    
    left = column(master_wb, pv_fig)
    grid = row(left, spread_fig)
    curdoc().clear()
    curdoc().add_root(grid)

# behavior
select_stk_1.on_change('value', update_stk_1)
select_stk_2.on_change('value', update_stk_2)
select_strategy.on_change('value', update_strategy)
backtest_dates.on_change('value', update_dates)
start_bt.on_click(run_backtest)

# build_final_gridplot
left = column(master_wb, pv_fig)
grid = row(left, spread_fig)
curdoc().add_root(grid)


