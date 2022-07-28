GuiInfo = {"proj": "PyCOM",
           "version": " v1.0.0",
           "email": "kainanos@outlook.com",
           "win_tmp": "C:/temp",
           "dbg_reldir": r"log/pycom/debug",
           "cwd": ""
           }

SerialInfo = {"baudrate": ['300', '600', '1200', '2400', '4800', '9600', '14400', '19200', '38400', '57600', '76800',
                           '115200', '128000', '230400', '256000', '460800', '921600', '1000000', '2000000', '3000000'],
              "bytesize": ['8', '7', '6', '5'],
              "stopbit": ['1', '2'],
              "paritybit": ['None', 'Odd', 'Even'],
              "timeout": 0.01
              }

AboutInfo = f"""
    Project: {GuiInfo["proj"]}
    Version: {GuiInfo["version"]}

    Support: {GuiInfo["email"]}
    Github Repo: https://github.com/kainan2020/PyCom
"""
