#!/usr/bin/env python

import getopt, sys, os, zipfile, shutil, traceback, struct, signingapks

class options:
    channels = []
    apkfile = None
    output = None


def usage():
    print 'Usage: %s [options] <path/to/apk>' %(sys.argv[0])
    print 'options:\n -c <a,b,c...>\trepackage channels'
    print ' -o <path>\toutput directory'
    print ' -f <file>\tpath to channel names file'
    signingapks.usage()

def parse_options(argv):
    try:
        opts, args = getopt.getopt(argv, "hc:f:o:s:",['keystore=','storepass=','keyalias=','keypass=','zipalignexe='])
        if len(args) == 0:
            print 'path to apk is missing'
            usage()
            return 1

        options.apkfile = args[0]

        for opt, arg in opts:
            if opt == '-h':
                usage()
                return 1
            elif opt == '-c':
                options.channels = arg.split(',')
            elif opt == '-f':
                options.channels = parse_channels_file(arg)
            elif opt == '-o':
                options.output = arg
            elif opt == '--keystore':
                signingapks.signingConfig.keystore = arg
            elif opt == '--storepass':
                signingapks.signingConfig.storepass = arg
            elif opt == '--keyalias':
                signingapks.signingConfig.keyalias = arg
            elif opt == '--keypass':
                signingapks.signingConfig.keypass = arg
            elif opt == '--zipalignexe':
                signingapks.zipalignexe = arg
            else:
                print 'invalid option "%s %s"' %(opt, arg)

        return 0
    except getopt.GetoptError as inst:
        print 'invalid options:', inst 
        sys.exit(1)
def parse_channels_file(path):
    if not os.path.exists(path):
        raise ValueError("path of channels file %s is not exists" %path)
    with open(path) as f:
        lines = f.read().splitlines()
        channels = []
        for line in lines:
            if len(line) == 0 or line[0] == '#':
                continue
            channels.append(line)
        return channels


def axml_utf16_pack(string):
    pack = bytearray(string.encode('utf-16'))
    str_len_pack = struct.pack('<I', len(string)) 
    pack[ : 2] = struct.unpack('BB', str_len_pack[ : 2])
    return pack

def find_pack_in_axml(axml_data, pack, start_pos):
    pos = axml_data.find(pack, start_pos, -1)
    return pos

def replace_axml_string(axml_data, old_string, new_string):
    new_string_pack = axml_utf16_pack(new_string)
    old_string_pack = axml_utf16_pack(old_string)
    new_string_pack_len = len(new_string_pack)
    old_string_pack_len = len(old_string_pack)
    if old_string_pack_len < new_string_pack_len:
        raise ValueError('new_string cannot be larger than old_string! ')
    pos = 0
    while True:
        pos = find_pack_in_axml(axml_data, old_string_pack, pos)
        if pos < 0:
            break
        axml_data[pos : pos + new_string_pack_len] = new_string_pack[ : new_string_pack_len]
        delta = old_string_pack_len - new_string_pack_len
        if delta:
            axml_data[pos + new_string_pack_len: pos + old_string_pack_len] = bytearray(delta)


_ANDROID_MANIFEST_XML = 'AndroidManifest.xml'
_CHANNEL_PLACE_HOLDER = 'xxxxxxxxxxxxxxxx' #should be larger than every length of channels
_CHANNEL_PLACE_HOLDER_LEN = len(_CHANNEL_PLACE_HOLDER)
def repackage(argv):
    if parse_options(argv):
        sys.exit(1)

    if len(options.channels) == 0:
        print 'you have not defined channels!'
        sys.exit(2)
    for channel in options.channels:
        if len(channel) > _CHANNEL_PLACE_HOLDER_LEN:
            raise ValueError('channel string cannot be larger than place-holder:'+ channel)
    if not os.path.isfile(options.apkfile):
        print 'the path of apk you point to is not a file: ', options.apkfile
        sys.exit(2)
    if options.output is None:
        options.output = os.path.abspath(os.path.join(options.apkfile, os.pardir, 'channels'))

    print 'repackage %s to channels %s \noutput path is %s' %(options.apkfile, options.channels, options.output)

    out = options.output
    if not os.path.exists(out):
        os.mkdir(out)
    temp = os.path.join(out, 'tmp')
    apkfile = options.apkfile
    
    # unzip apk to temp
    if os.path.exists(temp):
        print 'cleaning temp directory:', temp
        shutil.rmtree(temp)
    os.system('unzip -q '+apkfile+' -d '+temp)
    # delete signing info
    shutil.rmtree(os.path.join(temp, 'META-INF'))

    temp_manifest = os.path.join(temp,_ANDROID_MANIFEST_XML)
    with open(temp_manifest, 'rb') as source:
        raw_axml_data = bytearray(source.read())

    raw_filename, ext = os.path.splitext(os.path.basename(apkfile))
    # loop channel conditions
    apkfiles = []
    for channel in options.channels:
        print 'starting package channel %s apk' %channel    
        apkfile = package_channel_apk(raw_axml_data, channel, raw_filename, out, temp)
        apkfiles.append(apkfile)

    shutil.rmtree(temp)
    shutil.rmtree(os.path.join(out, 'raw'))
    signingapks.apkfiles[:] = apkfiles
    signingapks.sign_apks()


def package_channel_apk(raw_axml_data, channel, raw_filename, out, temp):
    newapk_name = raw_filename+'-'+channel+'-unsigned'
    newapk = os.path.join(out, newapk_name+'.apk')
    if os.path.isfile(newapk):
        os.remove(newapk) # remove old apk
    print 'creating unsigned apk :', newapk
    # clone a new buffer
    cloned_buffer = bytearray(len(raw_axml_data))
    cloned_buffer[:] = raw_axml_data
    replace_axml_string(cloned_buffer, _CHANNEL_PLACE_HOLDER, channel)
    temp_manifest = os.path.join(temp, _ANDROID_MANIFEST_XML)
    with open(temp_manifest, 'wb') as f:
        #print 'writing channel %s to AndroidManifest.xml' %channel
        f.write(cloned_buffer)
    temp_raw = os.path.join(temp, 'res/raw')
    if os.path.exists(temp_raw):
    	shutil.move(temp_raw, out)
    tempzip_name = os.path.join(out, newapk_name)
    tempzip = tempzip_name+'.zip'
    if os.path.exists(tempzip):
       os.remove(tempzip)
    #print 'creating channel archive', tempzip
    shutil.make_archive(tempzip_name, 'zip', temp)
    out_raw = os.path.join(out, 'raw')
    mZipFile = zipfile.ZipFile(tempzip, "a")
    for file in os.listdir(out_raw):
		full_path = os.path.join(out_raw, file);
		if os.path.isfile(full_path):
			mZipFile.write(full_path, "res\\raw\\" + file, zipfile.ZIP_STORED )
    mZipFile.close()
    os.rename(tempzip, newapk)
    #print 'renamed to ', newapk
    return newapk


if __name__ == '__main__':
    try:
        repackage(sys.argv[1:])
    except Exception, e:
        print traceback.format_exc()
        sys.exit(2)