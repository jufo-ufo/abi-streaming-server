
import sys
import requests
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

import pandas as pd
import sys
import time

x_vals = []
y_vals = []

def animate(i):
    try:
        data = pd.read_csv(sys.argv[1])
    except:
        print("Invalid first argument (logfile), exiting...")
        exit()
    data["date"] = pd.to_datetime(data["date"])

    x = data["date"]


    plt.subplot(2, 3, 1)
    plt.cla()
    plt.grid()
    plt.ylim(0, 100)
    plt.plot(x, data[" CPU%"], label='CPU in %', linewidth=0.75, color="mediumblue")
    plt.legend(loc='upper left')

    plt.subplot(2, 3, 2)
    plt.cla()
    plt.grid()
    plt.ylim(0, 100)
    plt.plot(x, data[" Mem%"], label='Memory in %', linewidth=1, color="green")
    plt.legend(loc='upper left')

    plt.subplot(2, 3, 3)
    plt.cla()
    plt.grid()
    plt.plot(x, data[" Net_out(tx)"], label='TX in kB/s', linewidth=0.75, color="darkorange")
    plt.plot(x, data[" Net_in(rx)"], label='RX in kB/s', linewidth=0.75, color="royalblue")
    plt.legend(loc='upper left')

    plt.subplot(2, 3, 4)
    plt.cla()
    plt.grid()
    plt.ylim(-5, 120)
    plt.plot(x, data[" Temp°"], label='Temp in °C', linewidth=1, color="darkred")
    plt.legend(loc='upper left')

    #plt.subplot(2, 3, 5)
    #plt.cla()
    #plt.grid()
    #plt.plot(x, data[" Server_out(tx)"], label='Nginx TX in kB/s', linewidth=0.75, color="darkorange")
    #plt.plot(x, data[" Server_in(rx)"], label='Nginx RX in kB/s', linewidth=0.75, color="royalblue")
    #plt.legend(loc='upper left')

    plt.subplot(2, 3, 6)
    plt.cla()
    plt.ylim(0, 20)
    plt.plot(x, data[" clients"], label='Clients', linewidth=1, color="darkred")
    plt.legend(loc='upper left')

    plt.tight_layout()


ani = FuncAnimation(plt.gcf(), animate, interval=500)
#animate(0)

#mng = plt.get_current_fig_manager()
#mng.window.showMaximized()
plt.show()
