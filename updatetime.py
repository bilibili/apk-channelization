#!/usr/bin/env python
import os, time

def update_file_time(dir_path):
    for root,dirs,files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            st = os.stat(file_path)
            mtime = time.localtime(st.st_mtime)
            file_time = mtime[0:6]
            #ZIP does not support timestamps before 1980
            if file_time[0] < 1980:
                now = int(time.time())
                os.utime(file_path, (now, now))