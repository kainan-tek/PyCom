GuiInfo = {"proj": "PyCOM",
           "version": " v1.1.0",
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

GuideInfo = f"""
    Encoding: the default encoding is gbk, plese change in the setting menu if needed.

    Single Send: 
      Send the single datas directly with Send button, or send the datas with a cycle time.

    Multi Send:
      Send each data item directly with its Send button, or send all selected items with a cycle time.

    File Send:
      Support txt file and json file. 
      For txt file, just send the file contents directly with Send button.
      For json file, it is similar to multi send function, user can customize the datas and cycle time.
      check the demo_data.json file. 
      for cycle_ms tag, 0: send all selected items directly. 1000: send all selected items with the cycle time.
      for select tag, 0: the data is selected to be sent; 1: the data is not selected to be sent.
"""

AboutInfo = f"""
    Project: {GuiInfo["proj"]}
    Version: {GuiInfo["version"]}

    Support: {GuiInfo["email"]}
    Github Repo: https://github.com/kainan2020/PyCom
"""
