Android多渠道输出脚本
===
这是博文[另辟蹊径实现Android多渠道打包][1]的一个简单实现，通过直接修改二进制AndroidManifest.xml实现渠道替换。

注意，只能修改编码为**UTF-16**的二进制AndroidManifest.xml。

替换二进制字符串核心代码来自：<https://github.com/wanchouchou/playWithAXML>

文件说明：
===
1. `signingapks.py`： 签名多个apk  
```./signingapks.py <signingConfig> [--zipalignexe=path/to/zipalign] <apkfile>...```  
2. `repackage.py`：输出渠道包  
```./repackage.py [options] <path/to/apk>```
3. 多渠道文件的格式：'#'开头为注释，不为空的字符串即为`渠道名`，如有文件`channels`：  

```
##############
#channel list#
##############
aaaa
bbb

ccc
```

使用方法：
===
- 请先将AndroidManifest.xml渠道名改为**占位符** "xxxxxxxxxxxxxxxx"，如umeng渠道：
```xml
<meta-data android:name="UMENG_CHANNEL"  android:value="xxxxxxxxxxxxxxxx" />
```

示例：

1. 输出当前目录`source.apk`的渠道包"aaa","bbb","ccc"到`out`目录并签名：  
```./repackage.py -c aaa,bbb,ccc -o out --keystore=android.key --keypass=android --storepass=android --keyalias=debug source.apk```

2. 输出当前目录`source.apk`的所有定义在文件`channels`中的渠道包，输出到`out`目录并签名  
```./repackage.py -f channels -o out --keystore=android.key --keypass=android --storepass=android --keyalias=debug source.apk```

3. 签名之前进行`zipalign`  
```./repackage.py -f channels -o out --zipalignexe=$ANDROID_SDK/build-tools/23.0.1/zipalign --keystore=android.key --keypass=android --storepass=android --keyalias=debug source.apk```

4. 与android gradle构建工具(1.3.0)一起使用：
在app的build.gradle中添加task如`releaseAllChannels`：
```groovy
afterEvaluate {
    android.applicationVariants.all { variant ->
        def output = variant.outputs.get(0).outputFile as File
        if ("release".equals(variant.name) && variant.signingConfig != null) {
            def task = tasks.findByName("zipalign${variant.name.capitalize()}")
            def zipalignExe = task?.zipAlignExe
            def repackageTask = tasks.create(name: "releaseAllChannels",
                    description: "Build all channel apks",
                    group: "build", type: Exec) {
                commandLine 'python', rootProject.file("repackage.py").absolutePath,
                        '-f', rootProject.file('channels').absolutePath,
                        '-o', builderOutput.absolutePath,
                        "--keystore=${variant.signingConfig.storeFile}",
                        "--keypass=${variant.signingConfig.keyPassword}",
                        "--storepass=${variant.signingConfig.storePassword}",
                        "--keyalias=${variant.signingConfig.keyAlias}",
                        "--zipalignexe=${zipalignExe}",
                        output.absolutePath
            }
            repackageTask.dependsOn variant.assemble
        }
}
```
执行task `releaseAllChannels` 即可以直接从源码编译并输出渠道包到`build`目录

[1]: http://yrom.net/blog/2015/05/25/the_other_way_to_package_multi_channel_apks/

