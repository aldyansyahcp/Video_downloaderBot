services:
  - type: worker
    name: telegram-downloader-bot
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python bbot.py"
    
