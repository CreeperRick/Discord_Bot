root@localhost:/data/data/com.termux/files/home/Discord_Bot# python3.11 ./bot.py
Starting bot.py...
Imports OK                                                      Traceback (most recent call last):
  File "/data/data/com.termux/files/home/Discord_Bot/./bot.py", line 25, in <module>
    config = json.load(f)
             ^^^^^^^^^^^^
  File "/usr/lib/python3.11/json/__init__.py", line 293, in load
    return loads(fp.read(),                                                ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/json/decoder.py", line 337, in decode                                                                   obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/json/decoder.py", line 353, in raw_decode                                                               obj, end = self.scan_once(s, idx)
               ^^^^^^^^^^^^^^^^^^^^^^
json.decoder.JSONDecodeError: Expecting ',' delimiter: line 11 column 5 (char 338)                                              root@localhost:/data/data/com.termux/files/home/Discord_Bot#
