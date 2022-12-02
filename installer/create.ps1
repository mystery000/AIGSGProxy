$TARGETDIR = "FILES"

if ((Test-Path -Path $TARGETDIR)) {
    Remove-Item -Recurse $TARGETDIR
}

New-Item -ItemType Directory -Path $TARGETDIR
New-Item -ItemType Directory -Path "$TARGETDIR\conf"
New-Item -ItemType Directory -Path "$TARGETDIR\db"

Copy-Item -Path "icon.ico" -Destination $TARGETDIR
Copy-Item -Path "..\*.py" -Destination $TARGETDIR

Copy-Item -Path "..\conf.yaml" -Destination $TARGETDIR\conf.yaml
Copy-Item -Path "..\conf\*.py" -Destination "$TARGETDIR\conf"
Copy-Item -Path "..\db\*.py" -Destination "$TARGETDIR\db"


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