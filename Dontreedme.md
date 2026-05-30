python3.11 -c "open('config.json','rb').read()" && python3.11 -c "import sys; d=open('config.json','rb').read(); print(len(d)); print(d[:30])"
