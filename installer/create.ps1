$TARGETDIR = "FILES"

if ((Test-Path -Path $TARGETDIR)) {
    Remove-Item -Recurse $TARGETDIR
}

New-Item -ItemType Directory -Path $TARGETDIR
New-Item -ItemType Directory -Path "$TARGETDIR\conf"
New-Item -ItemType Directory -Path "$TARGETDIR\db"
New-Item -ItemType Directory -Path "$TARGETDIR\kvdb"
New-Item -ItemType Directory -Path "$TARGETDIR\proxy"
New-Item -ItemType Directory -Path "$TARGETDIR\samba"
New-Item -ItemType Directory -Path "$TARGETDIR\server"
New-Item -ItemType Directory -Path "$TARGETDIR\tcp"
New-Item -ItemType Directory -Path "$TARGETDIR\logs"
New-Item -ItemType Directory -Path "$TARGETDIR\watcher"

Copy-Item -Path "icon.ico" -Destination $TARGETDIR
Copy-Item -Path "..\*.py" -Destination $TARGETDIR
Copy-Item -Path "..\watcher.txt" -Destination $TARGETDIR
Copy-Item -Path "..\conf_prod.yaml" -Destination $TARGETDIR\conf.yaml
Copy-Item -Path "..\conf\*.py" -Destination "$TARGETDIR\conf"
Copy-Item -Path "..\db\*.py" -Destination "$TARGETDIR\db"
Copy-Item -Path "..\kvdb\*.py" -Destination "$TARGETDIR\kvdb"
Copy-Item -Path "..\samba\*.py" -Destination "$TARGETDIR\samba"
Copy-Item -Path "..\server\*.py" -Destination "$TARGETDIR\server"
Copy-Item -Path "..\config\*" -Destination "$TARGETDIR\config"
Copy-Item -Path "..\tcp\*" -Destination "$TARGETDIR\tcp"
Copy-Item -Path "..\watcher\*.py" -Destination "$TARGETDIR\watcher"

New-Item -ItemType Directory -Path "$TARGETDIR\config\static"
New-Item -ItemType Directory -Path "$TARGETDIR\config\static\css"
New-Item -ItemType Directory -Path "$TARGETDIR\config\static\js"
Copy-Item -Path "..\config\static\css\*.css" -Destination "$TARGETDIR\config\static\css"
Copy-Item -Path "..\config\static\js\*.js" -Destination "$TARGETDIR\config\static\js"

Copy-Item -Path "python" -Destination $TARGETDIR -Recurse

$CacheItems = Get-ChildItem -Path "$TARGETDIR\python" -Filter "__pycache__" -Recurse -Directory -Name
foreach($CacheItem in $CacheItems) {
    Write-Host "Deleting $TARGETDIR\python\$CacheItem"
    Remove-Item -Recurse "$TARGETDIR\python\$CacheItem"
}

$PycItems = Get-ChildItem -Path "$TARGETDIR\python" -Filter "*.pyc" -Recurse -File -Name
foreach($PycItem in $PycItems) {
    Write-Host "Deleting $TARGETDIR\python\$PycItem"
    Remove-Item -Recurse "$TARGETDIR\python\$PycItem"
}

# Service
Expand-Archive "nssm-2.24.zip" -DestinationPath "$TARGETDIR"

&"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsis