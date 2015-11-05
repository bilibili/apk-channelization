#!/usr/bin/env python
import sys, getopt, os

apkfiles = []
zipalignexe = None
class signingConfig:
    verbose = False
    keystore = None
    storepass = None
    keyalias = None
    keypass = None
def usage():
    print 'Usage: ./signingapks.py <signingConfig> [--zipalignexe=path/to/zipalign] <apkfile>...'
    print 'signingConfig:\n --keystore=path/to/keystore'
    print ' --storepass=keystore password'
    print ' --keyalias=key alias'
    print ' --keypass=key password'

def parse_options(argv):
    try:
        opts, args = getopt.getopt(argv, 'hv', ['keystore=','storepass=','keyalias=','keypass=','zipalignexe='])
        if len(args) == 0:
            print 'path to apk is missing'
            usage()
            return 1
        global apkfiles
        global zipalignexe
        apkfiles = args[:]

        for opt, arg in opts:
            if opt == '-h':
                usage()
                return 1
            if opt == '-v':
                signingConfig.verbose = True
            elif opt == '--keystore':
                signingConfig.keystore = arg
            elif opt == '--storepass':
                signingConfig.storepass = arg
            elif opt == '--keyalias':
                signingConfig.keyalias = arg
            elif opt == '--keypass':
                signingConfig.keypass = arg
            elif opt == '--zipalignexe':
                zipalignexe = arg
            else:
                print 'invalid option "%s %s"' %(opt, arg)

        return 0
    except getopt.GetoptError as inst:
        print 'invalid options:', inst 
        sys.exit(1)

def sign_apks():
    
    if signingConfig.keystore == None:
        raise ValueError('where is your keystore file ?')
    if signingConfig.keyalias == None:
        raise ValueError('missing key alias ?')
    for apkfile in apkfiles:
        if not os.path.exists(apkfile):
            raise RuntimeError('apk file %s is not exists!' %apkfile)
        print 'signing ', apkfile
        cmd = 'jarsigner'
        if signingConfig.verbose:
            cmd += ' -verbose'
        cmd += ' -sigalg SHA1withRSA -digestalg SHA1 -keystore '+signingConfig.keystore
        if signingConfig.storepass != None:
            cmd += ' -storepass '+signingConfig.storepass
        if signingConfig.keypass != None:
            cmd += ' -keypass '+signingConfig.keypass
        cmd += ' '+apkfile+' '+signingConfig.keyalias
        # print 'run '+cmd
        result = os.system(cmd)
        if result:
            print 'jarsigner exit non-zero: ', result
            sys.exit(1)
        raw_filename = os.path.splitext(apkfile)[0]
        if raw_filename.endswith('-unsigned'):
            raw_filename = raw_filename[:-len('-unsigned')]
        signedapk = raw_filename
        if not signedapk.endswith('-signed-unaligned'):
            signedapk+='-signed-unaligned.apk'
        if apkfile is not signedapk:
            if os.path.exists(signedapk):
                os.remove(signedapk)
            os.rename(apkfile, signedapk)
        alignedapk = os.path.splitext(signedapk)[0][:-len('-signed-unaligned')]+'.apk'

        if zipalignexe != None and zipalignexe is not 'null':
            print 'zipalign ', signedapk
            cmd = zipalignexe+' -f 4 '+signedapk +' '+alignedapk
            result = os.system(cmd)
            if result:
                print 'zipalign exit non-zero: ', result
                sys.exit(1)
            os.remove(signedapk)



if __name__ == '__main__':
    try:
        if parse_options(sys.argv[1:]):
            sys.exit(1)
        sign_apks()
    except Exception, e:
        print e
        sys.exit(2)