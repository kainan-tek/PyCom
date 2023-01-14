GuiInfo = {"proj": "PyCOM",
           "version": " v1.2.1",
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

    Support: kainanos@outlook.com
    Github Repo: https://github.com/kainan2020/PyCom
"""


GuideInfo = """
    Encoding: the default encoding is gbk, plese change in the settings menu if needed.

    Single Send: 
      Send the datas directly with Send button, or send the datas with a cycle time.

    Multi Send:
      Send each data item directly with its Send button, or send all selected items with a cycle time.

    File Send:
      Support txt file and json file.
      1. for txt file: just send the file contents directly with Send button.
      2. for json file: it is similar to multi send function, user can customize the datas and cycle time.
      check the details in demo_txt_data.json or demo_hex_data.json, the meaning of the tags as below.
      cycle_ms tag: 0: send all selected items directly; 1000: send all selected items with the cycle time.
      hexmode tag: 0: send all selected items as txt contents; 1: send all selected items as hex contents.
      select tag: 0: the data is selected to be sent; 1: the data is not selected to be sent.
"""
